from __future__ import annotations

from typing import Iterable

import spotipy

from core.adapters.base import SourceAdapter, TargetAdapter
from core.config import get_settings
from core.models import MatchResult, NormalizedTrack, Playlist, Provider
from core.spotify import reader as sp_reader
from core.spotify import search as sp_search
from core.spotify import writer as sp_writer


class SpotifyAdapter(SourceAdapter, TargetAdapter):
    provider = Provider.SPOTIFY

    def __init__(self, sp: spotipy.Spotify, score_threshold: float | None = None):
        self.sp = sp
        self.score_threshold = (
            score_threshold if score_threshold is not None else get_settings().match_score_threshold
        )

    # SourceAdapter ----------------------------------------------------------

    def list_user_playlists(self, own_only: bool = True) -> list[Playlist]:
        return sp_reader.list_user_playlists(self.sp, own_only=own_only)

    def fetch_playlist_tracks(self, playlist_id: str) -> list[NormalizedTrack]:
        return sp_reader.fetch_playlist_tracks(self.sp, playlist_id)

    # TargetAdapter ----------------------------------------------------------

    def search_track(self, track: NormalizedTrack) -> MatchResult:
        return sp_search.search_track(self.sp, track, self.score_threshold)

    def find_existing_playlist_by_name(self, name: str) -> str | None:
        return sp_writer.find_existing_playlist_by_name(self.sp, name)

    def create_playlist(
        self,
        name: str,
        description: str | None = None,
        public: bool = False,
    ) -> str:
        return sp_writer.create_playlist(self.sp, name, description=description, public=public)

    def add_tracks(self, playlist_id: str, target_ids: Iterable[str]) -> None:
        sp_writer.add_tracks_in_batches(self.sp, playlist_id, target_ids)

    def clear_playlist(self, playlist_id: str) -> None:
        sp_writer.clear_playlist(self.sp, playlist_id)

    def playlist_url(self, playlist_id: str) -> str:
        return f"https://open.spotify.com/playlist/{playlist_id}"
