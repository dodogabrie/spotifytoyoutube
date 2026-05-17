from __future__ import annotations

import logging
from typing import Iterable

import spotipy

from core.exceptions import SpotifyError

logger = logging.getLogger(__name__)


def _current_user_id(sp: spotipy.Spotify) -> str:
    me = sp.current_user()
    if not me or "id" not in me:
        raise SpotifyError("Could not fetch current Spotify user")
    return me["id"]


def find_existing_playlist_by_name(sp: spotipy.Spotify, name: str) -> str | None:
    user_id = _current_user_id(sp)
    offset = 0
    page_size = 50
    while True:
        page = sp.current_user_playlists(limit=page_size, offset=offset)
        if not page:
            return None
        for item in page.get("items") or []:
            owner_id = (item.get("owner") or {}).get("id")
            if owner_id == user_id and item.get("name") == name:
                return item["id"]
        if page.get("next"):
            offset += page_size
        else:
            return None


def create_playlist(
    sp: spotipy.Spotify,
    name: str,
    description: str | None = None,
    public: bool = False,
) -> str:
    user_id = _current_user_id(sp)
    result = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=public,
        collaborative=False,
        description=description or "",
    )
    if not result or "id" not in result:
        raise SpotifyError(f"Failed to create Spotify playlist {name!r}")
    return result["id"]


def add_tracks_in_batches(
    sp: spotipy.Spotify,
    playlist_id: str,
    track_ids: Iterable[str],
    batch_size: int = 100,
) -> int:
    """Add tracks to a Spotify playlist. Returns number of tracks added.

    Spotify's API accepts up to 100 URIs per request.
    """
    added = 0
    batch: list[str] = []
    for track_id in track_ids:
        batch.append(f"spotify:track:{track_id}")
        if len(batch) >= batch_size:
            sp.playlist_add_items(playlist_id, batch)
            added += len(batch)
            batch.clear()
    if batch:
        sp.playlist_add_items(playlist_id, batch)
        added += len(batch)
    return added


def clear_playlist(sp: spotipy.Spotify, playlist_id: str) -> None:
    """Remove every track from a Spotify playlist."""
    while True:
        page = sp.playlist_items(playlist_id, limit=100, additional_types=("track",))
        items = (page or {}).get("items") or []
        if not items:
            return
        uris = []
        for item in items:
            track = item.get("track") or {}
            tid = track.get("id")
            if tid:
                uris.append(f"spotify:track:{tid}")
        if not uris:
            return
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris)
