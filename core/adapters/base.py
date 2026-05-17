from abc import ABC, abstractmethod
from typing import Iterable

from core.models import MatchResult, NormalizedTrack, Playlist, Provider


class SourceAdapter(ABC):
    provider: Provider

    @abstractmethod
    def list_user_playlists(self, own_only: bool = True) -> list[Playlist]: ...

    @abstractmethod
    def fetch_playlist_tracks(self, playlist_id: str) -> list[NormalizedTrack]: ...


class TargetAdapter(ABC):
    provider: Provider

    @abstractmethod
    def search_track(self, track: NormalizedTrack) -> MatchResult: ...

    @abstractmethod
    def find_existing_playlist_by_name(self, name: str) -> str | None: ...

    @abstractmethod
    def create_playlist(
        self,
        name: str,
        description: str | None = None,
        public: bool = False,
    ) -> str: ...

    @abstractmethod
    def add_tracks(self, playlist_id: str, target_ids: Iterable[str]) -> None: ...

    @abstractmethod
    def clear_playlist(self, playlist_id: str) -> None:
        """Remove all tracks from a playlist (used by REPLACE idempotency mode)."""

    @abstractmethod
    def playlist_url(self, playlist_id: str) -> str: ...
