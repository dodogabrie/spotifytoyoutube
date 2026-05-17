from __future__ import annotations

from typing import Protocol

from spotipy.cache_handler import CacheFileHandler, CacheHandler, MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth, SpotifyPKCE

from core.config import Settings

SCOPES = " ".join(
    [
        "playlist-read-private",
        "playlist-read-collaborative",
        "playlist-modify-private",
        "playlist-modify-public",
    ]
)


class _OAuthLike(Protocol):
    def get_access_token(self, code: str | None = None, as_dict: bool = True): ...

    def get_authorize_url(self, state: str | None = None) -> str: ...


def build_cli_auth_manager(settings: Settings) -> SpotifyOAuth:
    """Build a Spotify OAuth manager for the CLI (token cached on disk)."""
    settings.ensure_dirs()
    handler = CacheFileHandler(cache_path=str(settings.spotify_cache_path))
    return SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_cli_redirect_uri,
        scope=SCOPES,
        cache_handler=handler,
        open_browser=True,
    )


def build_web_auth_manager(
    settings: Settings,
    state: str,
    token_cache: CacheHandler | None = None,
) -> SpotifyPKCE:
    """Build a Spotify OAuth manager for the web backend.

    Uses PKCE and an in-memory cache so we never persist user tokens to disk.
    """
    handler = token_cache or MemoryCacheHandler()
    return SpotifyPKCE(
        client_id=settings.spotify_client_id,
        redirect_uri=settings.spotify_redirect_uri,
        scope=SCOPES,
        cache_handler=handler,
        state=state,
        open_browser=False,
    )
