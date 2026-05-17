from __future__ import annotations

import logging
from typing import Any

from core.models import NormalizedTrack, Playlist

logger = logging.getLogger(__name__)


def list_user_playlists(yt, own_only: bool = True) -> list[Playlist]:
    """List playlists in the user's YouTube Music library.

    ytmusicapi already returns library playlists (i.e. ones the user owns or has saved).
    The ``own_only`` flag mirrors the SourceAdapter API; library playlists are treated
    as "personal" for our purposes.
    """
    raw = yt.get_library_playlists(limit=200) or []
    playlists: list[Playlist] = []
    for item in raw:
        pid = item.get("playlistId") or item.get("id")
        if not pid:
            continue
        # ytmusicapi includes a virtual "LM" playlist (Liked Music). Skip it because
        # the user requested personal playlists only.
        if pid == "LM":
            continue
        playlists.append(
            Playlist(
                id=pid,
                name=item.get("title") or "(untitled)",
                description=item.get("description"),
                owner=(item.get("author") or [{}])[0].get("name") if item.get("author") else None,
                track_count=item.get("count"),
                public=None,
                collaborative=False,
            )
        )
    return playlists


def _duration_seconds(raw: dict[str, Any]) -> int | None:
    seconds = raw.get("duration_seconds")
    if isinstance(seconds, int) and seconds > 0:
        return seconds
    duration = raw.get("duration")
    if not duration:
        return None
    try:
        parts = [int(p) for p in str(duration).split(":")]
    except ValueError:
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def _normalize(track: dict[str, Any]) -> NormalizedTrack | None:
    if not track:
        return None
    video_id = track.get("videoId")
    if not video_id:
        return None
    artists = [a.get("name", "") for a in track.get("artists") or [] if a.get("name")]
    duration_s = _duration_seconds(track)
    duration_ms = duration_s * 1000 if duration_s else None
    album = (track.get("album") or {}).get("name") if isinstance(track.get("album"), dict) else None
    return NormalizedTrack(
        source_id=video_id,
        title=track.get("title") or "",
        artists=artists,
        album=album,
        duration_ms=duration_ms,
        isrc=None,  # YouTube Music does not expose ISRC reliably
        explicit=bool(track.get("isExplicit", False)),
    )


def fetch_playlist_tracks(yt, playlist_id: str) -> list[NormalizedTrack]:
    """Fetch all tracks from a YouTube Music playlist.

    We use ``limit=None`` so ytmusicapi paginates through everything.
    """
    data = yt.get_playlist(playlist_id, limit=None)
    raw_tracks = (data or {}).get("tracks") or []
    tracks: list[NormalizedTrack] = []
    for raw in raw_tracks:
        normalized = _normalize(raw)
        if normalized:
            tracks.append(normalized)
    return tracks
