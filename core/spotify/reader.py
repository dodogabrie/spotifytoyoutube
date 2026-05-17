from __future__ import annotations

import logging
from typing import Any

import spotipy

from core.exceptions import SpotifyError
from core.models import NormalizedTrack, Playlist

logger = logging.getLogger(__name__)


def _current_user_id(sp: spotipy.Spotify) -> str:
    me = sp.current_user()
    if not me or "id" not in me:
        raise SpotifyError("Could not fetch current Spotify user")
    return me["id"]


def list_user_playlists(sp: spotipy.Spotify, own_only: bool = True) -> list[Playlist]:
    """Return all playlists visible to the authenticated user.

    With own_only=True, filters to playlists where the current user is the owner.
    """
    user_id = _current_user_id(sp) if own_only else None
    playlists: list[Playlist] = []
    offset = 0
    page_size = 50
    while True:
        page = sp.current_user_playlists(limit=page_size, offset=offset)
        if not page:
            break
        items = page.get("items") or []
        for item in items:
            owner_id = (item.get("owner") or {}).get("id")
            if own_only and owner_id != user_id:
                continue
            playlists.append(
                Playlist(
                    id=item["id"],
                    name=item.get("name") or "(untitled)",
                    description=item.get("description") or None,
                    owner=owner_id,
                    track_count=(item.get("tracks") or {}).get("total"),
                    public=item.get("public"),
                    collaborative=bool(item.get("collaborative")),
                )
            )
        if page.get("next"):
            offset += page_size
        else:
            break
    return playlists


def _normalize(track_obj: dict[str, Any]) -> NormalizedTrack | None:
    if not track_obj:
        return None
    if track_obj.get("is_local"):
        return None
    if track_obj.get("type") and track_obj["type"] != "track":
        return None
    track_id = track_obj.get("id")
    if not track_id:
        return None
    artists = [a.get("name", "") for a in track_obj.get("artists") or [] if a.get("name")]
    isrc = (track_obj.get("external_ids") or {}).get("isrc")
    album = (track_obj.get("album") or {}).get("name")
    return NormalizedTrack(
        source_id=track_id,
        title=track_obj.get("name") or "",
        artists=artists,
        album=album,
        duration_ms=track_obj.get("duration_ms"),
        isrc=isrc,
        explicit=bool(track_obj.get("explicit", False)),
    )


def fetch_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> list[NormalizedTrack]:
    tracks: list[NormalizedTrack] = []
    offset = 0
    page_size = 100
    while True:
        page = sp.playlist_items(
            playlist_id,
            limit=page_size,
            offset=offset,
            additional_types=("track",),
        )
        if not page:
            break
        for item in page.get("items") or []:
            normalized = _normalize(item.get("track") or {})
            if normalized:
                tracks.append(normalized)
        if page.get("next"):
            offset += page_size
        else:
            break
    return tracks
