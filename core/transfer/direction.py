from __future__ import annotations

from core.adapters.base import SourceAdapter, TargetAdapter
from core.adapters.spotify_adapter import SpotifyAdapter
from core.adapters.ytmusic_adapter import YTMusicAdapter
from core.exceptions import TransferError
from core.models import TransferDirection


def build_adapters(
    direction: TransferDirection,
    spotify_adapter: SpotifyAdapter,
    ytmusic_adapter: YTMusicAdapter,
) -> tuple[SourceAdapter, TargetAdapter]:
    if direction is TransferDirection.SPOTIFY_TO_YTMUSIC:
        return spotify_adapter, ytmusic_adapter
    if direction is TransferDirection.YTMUSIC_TO_SPOTIFY:
        return ytmusic_adapter, spotify_adapter
    raise TransferError(f"Unsupported direction: {direction}")
