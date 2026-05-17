from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials


def _credentials(client_id: str, client_secret: str) -> OAuthCredentials:
    return OAuthCredentials(client_id=client_id, client_secret=client_secret)


def get_ytmusic_client_from_file(
    oauth_file: str | Path,
    client_id: str,
    client_secret: str,
) -> YTMusic:
    return YTMusic(str(oauth_file), oauth_credentials=_credentials(client_id, client_secret))


def get_ytmusic_client_from_dict(
    token: dict[str, Any],
    client_id: str,
    client_secret: str,
) -> YTMusic:
    return YTMusic(json.dumps(token), oauth_credentials=_credentials(client_id, client_secret))
