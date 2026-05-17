from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.adapters.spotify_adapter import SpotifyAdapter
from core.adapters.ytmusic_adapter import YTMusicAdapter
from core.auth.spotify_auth import build_web_auth_manager
from core.config import get_settings
from core.models import Provider
from core.spotify.client import get_spotify_client
from core.ytmusic.client import get_ytmusic_client_from_dict
from spotipy.cache_handler import MemoryCacheHandler
from web.backend.deps import require_session
from web.backend.schemas import PlaylistDTO
from web.backend.sessions import SessionData

router = APIRouter(prefix="/playlists", tags=["playlists"])


def _spotify_adapter(session: SessionData) -> SpotifyAdapter:
    if not session.spotify_token_info:
        raise HTTPException(status_code=401, detail="Spotify not authorized")
    settings = get_settings()
    cache = MemoryCacheHandler(token_info=session.spotify_token_info)
    auth_manager = build_web_auth_manager(settings, state="", token_cache=cache)
    sp = get_spotify_client(auth_manager)
    return SpotifyAdapter(sp)


def _ytmusic_adapter(session: SessionData) -> YTMusicAdapter:
    if not session.ytmusic_token:
        raise HTTPException(status_code=401, detail="YT Music not authorized")
    settings = get_settings()
    yt = get_ytmusic_client_from_dict(
        session.ytmusic_token,
        settings.ytmusic_client_id,
        settings.ytmusic_client_secret,
    )
    return YTMusicAdapter(yt)


@router.get("", response_model=list[PlaylistDTO])
def list_playlists(
    provider: Provider = Query(..., description="Source provider to list playlists from"),
    own_only: bool = Query(True),
    session: SessionData = Depends(require_session),
) -> list[PlaylistDTO]:
    adapter = (
        _spotify_adapter(session) if provider is Provider.SPOTIFY else _ytmusic_adapter(session)
    )
    playlists = adapter.list_user_playlists(own_only=own_only)
    return [
        PlaylistDTO(
            id=p.id,
            name=p.name,
            description=p.description,
            track_count=p.track_count,
            public=p.public,
            collaborative=p.collaborative,
        )
        for p in playlists
    ]
