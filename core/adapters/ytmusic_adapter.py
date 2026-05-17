from __future__ import annotations

from typing import Iterable

from core.adapters.base import SourceAdapter, TargetAdapter
from core.config import get_settings
from core.models import MatchResult, NormalizedTrack, Playlist, Provider
from core.ytmusic import reader as yt_reader
from core.ytmusic import search as yt_search
from core.ytmusic import writer as yt_writer


class YTMusicAdapter(SourceAdapter, TargetAdapter):
    provider = Provider.YTMUSIC

    def __init__(self, yt, score_threshold: float | None = None):
        self.yt = yt
        self.score_threshold = (
            score_threshold if score_threshold is not None else get_settings().match_score_threshold
        )

    def list_user_playlists(self, own_only: bool = True) -> list[Playlist]:
        return yt_reader.list_user_playlists(self.yt, own_only=own_only)

    def fetch_playlist_tracks(self, playlist_id: str) -> list[NormalizedTrack]:
        return yt_reader.fetch_playlist_tracks(self.yt, playlist_id)

    def search_track(self, track: NormalizedTrack) -> MatchResult:
        return yt_search.search_track(self.yt, track, self.score_threshold)

    def find_existing_playlist_by_name(self, name: str) -> str | None:
        return yt_writer.find_existing_playlist_by_name(self.yt, name)

    def create_playlist(
        self,
        name: str,
        description: str | None = None,
        public: bool = False,
    ) -> str:
        return yt_writer.create_playlist(self.yt, name, description=description, public=public)

    def add_tracks(self, playlist_id: str, target_ids: Iterable[str]) -> None:
        yt_writer.add_tracks_in_batches(self.yt, playlist_id, target_ids)

    def clear_playlist(self, playlist_id: str) -> None:
        yt_writer.clear_playlist(self.yt, playlist_id)

    def playlist_url(self, playlist_id: str) -> str:
        return f"https://music.youtube.com/playlist?list={playlist_id}"
