from __future__ import annotations

import logging
from typing import Any

from core.matching.scoring import score_match
from core.matching.strategies import ytmusic_queries
from core.models import MatchResult, NormalizedTrack

logger = logging.getLogger(__name__)


def _candidate_from_item(item: dict[str, Any]) -> NormalizedTrack | None:
    video_id = item.get("videoId")
    if not video_id:
        return None
    artists = [a.get("name", "") for a in item.get("artists") or [] if a.get("name")]
    duration_s = item.get("duration_seconds")
    duration_ms = duration_s * 1000 if isinstance(duration_s, int) else None
    return NormalizedTrack(
        source_id=video_id,
        title=item.get("title") or "",
        artists=artists,
        album=(item.get("album") or {}).get("name") if isinstance(item.get("album"), dict) else None,
        duration_ms=duration_ms,
    )


def _result_type_from_filter(filter_name: str) -> str:
    return "song" if filter_name == "songs" else "video"


def search_track(yt, track: NormalizedTrack, threshold: float) -> MatchResult:
    best: tuple[NormalizedTrack, float, str] | None = None  # (candidate, score, type)

    for query in ytmusic_queries(track):
        for filter_name in ("songs", "videos"):
            try:
                results = yt.search(query, filter=filter_name, limit=5, ignore_spelling=False) or []
            except Exception as exc:  # ytmusicapi can raise on transient errors
                logger.warning("YT Music search failed (%s, %s): %s", query, filter_name, exc)
                continue
            for item in results:
                candidate = _candidate_from_item(item)
                if not candidate:
                    continue
                s = score_match(track, candidate)
                if filter_name == "songs":
                    s = min(1.0, s + 0.05)
                if best is None or s > best[1]:
                    best = (candidate, s, _result_type_from_filter(filter_name))
            if best and best[1] >= 0.9:
                # high-confidence early exit
                break
        if best and best[1] >= 0.9:
            break

    if best is None:
        return MatchResult(track=track, target_id=None, result_type="none", score=0.0)

    candidate, score, result_type = best
    if score < threshold:
        return MatchResult(
            track=track,
            target_id=None,
            result_type="none",
            score=score,
            candidate_title=candidate.title,
            candidate_artists=candidate.artists,
        )
    return MatchResult(
        track=track,
        target_id=candidate.source_id,
        result_type=result_type,  # type: ignore[arg-type]
        score=score,
        candidate_title=candidate.title,
        candidate_artists=candidate.artists,
    )
