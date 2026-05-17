from __future__ import annotations

from typing import Any

import spotipy


def get_spotify_client(auth_manager: Any) -> spotipy.Spotify:
    return spotipy.Spotify(auth_manager=auth_manager, retries=3)
