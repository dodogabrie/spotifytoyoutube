from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Callable

from core.adapters.base import SourceAdapter, TargetAdapter
from core.exceptions import TransferAborted
from core.models import (
    IdempotencyMode,
    PlaylistTransferOutcome,
    TransferDirection,
    TransferProgressEvent,
    TransferReport,
)
from core.transfer.idempotency import resolve_target

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[TransferProgressEvent], None]


class TransferEngine:
    def __init__(
        self,
        source: SourceAdapter,
        target: TargetAdapter,
        direction: TransferDirection,
        progress_callback: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
    ):
        self.source = source
        self.target = target
        self.direction = direction
        self._cb = progress_callback or (lambda _e: None)
        self._cancel = cancel_event or threading.Event()

    def _emit(self, event: TransferProgressEvent) -> None:
        try:
            self._cb(event)
        except Exception:  # pragma: no cover - never let a UI callback kill the engine
            logger.exception("progress callback raised")

    def _check_cancel(self) -> None:
        if self._cancel.is_set():
            raise TransferAborted("Cancelled by user")

    def transfer(
        self,
        playlist_ids: list[str],
        idempotency: IdempotencyMode = IdempotencyMode.CREATE_NEW,
        target_public_default: bool = False,
    ) -> TransferReport:
        started_at = datetime.now(timezone.utc)
        outcomes: list[PlaylistTransferOutcome] = []

        all_source_playlists = {p.id: p for p in self.source.list_user_playlists()}

        self._emit(
            TransferProgressEvent(
                type="job_started",
                total=len(playlist_ids),
                message=f"Transferring {len(playlist_ids)} playlist(s)",
            )
        )

        for idx, pid in enumerate(playlist_ids, start=1):
            self._check_cancel()
            playlist = all_source_playlists.get(pid)
            if playlist is None:
                logger.warning("Source playlist %s not found; skipping", pid)
                self._emit(
                    TransferProgressEvent(
                        type="error",
                        playlist_id=pid,
                        message="Source playlist not found",
                    )
                )
                continue

            self._emit(
                TransferProgressEvent(
                    type="playlist_started",
                    playlist_id=playlist.id,
                    playlist_name=playlist.name,
                    current=idx,
                    total=len(playlist_ids),
                )
            )

            tracks = self.source.fetch_playlist_tracks(playlist.id)

            target_public = (
                bool(playlist.public) if playlist.public is not None else target_public_default
            )
            resolution = resolve_target(
                self.target,
                desired_name=playlist.name,
                description=playlist.description,
                public=target_public,
                mode=idempotency,
            )

            if resolution.action == "skipped":
                outcomes.append(
                    PlaylistTransferOutcome(
                        source_playlist=playlist,
                        target_playlist_id=resolution.playlist_id,
                        target_playlist_name=resolution.name_used,
                        action="skipped",
                        matched_count=0,
                        unmatched_count=0,
                        skipped_count=len(tracks),
                    )
                )
                self._emit(
                    TransferProgressEvent(
                        type="playlist_done",
                        playlist_id=playlist.id,
                        playlist_name=playlist.name,
                        target_playlist_id=resolution.playlist_id,
                        message="Skipped (already exists)",
                    )
                )
                continue

            target_ids: list[str] = []
            unmatched = []
            for t_idx, track in enumerate(tracks, start=1):
                self._check_cancel()
                match = self.target.search_track(track)
                if match.target_id:
                    target_ids.append(match.target_id)
                    self._emit(
                        TransferProgressEvent(
                            type="track_matched",
                            playlist_id=playlist.id,
                            playlist_name=playlist.name,
                            current=t_idx,
                            total=len(tracks),
                            track_title=track.title,
                            extra={"score": match.score, "result_type": match.result_type},
                        )
                    )
                else:
                    unmatched.append(match)
                    self._emit(
                        TransferProgressEvent(
                            type="track_unmatched",
                            playlist_id=playlist.id,
                            playlist_name=playlist.name,
                            current=t_idx,
                            total=len(tracks),
                            track_title=track.title,
                            extra={
                                "top_candidate": match.candidate_title,
                                "score": match.score,
                            },
                        )
                    )

            if target_ids and resolution.playlist_id:
                self.target.add_tracks(resolution.playlist_id, target_ids)

            outcomes.append(
                PlaylistTransferOutcome(
                    source_playlist=playlist,
                    target_playlist_id=resolution.playlist_id,
                    target_playlist_name=resolution.name_used,
                    action=resolution.action,
                    matched_count=len(target_ids),
                    unmatched_count=len(unmatched),
                    skipped_count=0,
                    unmatched=unmatched,
                )
            )

            self._emit(
                TransferProgressEvent(
                    type="playlist_done",
                    playlist_id=playlist.id,
                    playlist_name=playlist.name,
                    target_playlist_id=resolution.playlist_id,
                    message=f"{len(target_ids)} matched, {len(unmatched)} unmatched",
                )
            )

        finished_at = datetime.now(timezone.utc)
        report = TransferReport(
            direction=self.direction,
            started_at=started_at,
            finished_at=finished_at,
            idempotency=idempotency,
            playlists=outcomes,
        )
        self._emit(
            TransferProgressEvent(
                type="job_done",
                total=len(playlist_ids),
                message=(
                    f"Done: matched={report.total_matched}, "
                    f"unmatched={report.total_unmatched}, "
                    f"skipped={report.total_skipped}"
                ),
            )
        )
        return report
