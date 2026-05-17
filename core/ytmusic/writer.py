from __future__ import annotations

import logging
from typing import Iterable

from core.exceptions import YTMusicError

logger = logging.getLogger(__name__)


def find_existing_playlist_by_name(yt, name: str) -> str | None:
    raw = yt.get_library_playlists(limit=200) or []
    for item in raw:
        if (item.get("title") or "") == name:
            pid = item.get("playlistId") or item.get("id")
            if pid and pid != "LM":
                return pid
    return None


def create_playlist(
    yt,
    name: str,
    description: str | None = None,
    public: bool = False,
) -> str:
    privacy = "PUBLIC" if public else "PRIVATE"
    pid = yt.create_playlist(title=name, description=description or "", privacy_status=privacy)
    if not isinstance(pid, str) or not pid:
        raise YTMusicError(f"Unexpected response creating YT Music playlist: {pid!r}")
    return pid


def add_tracks_in_batches(
    yt,
    playlist_id: str,
    video_ids: Iterable[str],
    batch_size: int = 50,
) -> int:
    added = 0
    batch: list[str] = []
    for vid in video_ids:
        batch.append(vid)
        if len(batch) >= batch_size:
            yt.add_playlist_items(playlist_id, batch, duplicates=True)
            added += len(batch)
            batch.clear()
    if batch:
        yt.add_playlist_items(playlist_id, batch, duplicates=True)
        added += len(batch)
    return added


def clear_playlist(yt, playlist_id: str) -> None:
    data = yt.get_playlist(playlist_id, limit=None)
    items = (data or {}).get("tracks") or []
    removable = [
        {"videoId": t["videoId"], "setVideoId": t.get("setVideoId")}
        for t in items
        if t.get("videoId") and t.get("setVideoId")
    ]
    if removable:
        yt.remove_playlist_items(playlist_id, removable)
