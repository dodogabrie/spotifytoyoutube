from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Provider(str, Enum):
    SPOTIFY = "spotify"
    YTMUSIC = "ytmusic"


class TransferDirection(str, Enum):
    SPOTIFY_TO_YTMUSIC = "spotify_to_ytmusic"
    YTMUSIC_TO_SPOTIFY = "ytmusic_to_spotify"

    @property
    def source(self) -> Provider:
        return (
            Provider.SPOTIFY
            if self is TransferDirection.SPOTIFY_TO_YTMUSIC
            else Provider.YTMUSIC
        )

    @property
    def target(self) -> Provider:
        return (
            Provider.YTMUSIC
            if self is TransferDirection.SPOTIFY_TO_YTMUSIC
            else Provider.SPOTIFY
        )


class IdempotencyMode(str, Enum):
    CREATE_NEW = "create_new"
    APPEND = "append"
    REPLACE = "replace"
    SKIP_IF_EXISTS = "skip_if_exists"


class NormalizedTrack(BaseModel):
    source_id: str
    title: str
    artists: list[str]
    album: str | None = None
    duration_ms: int | None = None
    isrc: str | None = None
    explicit: bool = False


class Playlist(BaseModel):
    id: str
    name: str
    description: str | None = None
    owner: str | None = None
    track_count: int | None = None
    public: bool | None = None
    collaborative: bool = False


class MatchResult(BaseModel):
    track: NormalizedTrack
    target_id: str | None = None
    result_type: Literal["song", "video", "track", "none"] = "none"
    score: float = 0.0
    candidate_title: str | None = None
    candidate_artists: list[str] = Field(default_factory=list)


class TransferProgressEvent(BaseModel):
    type: Literal[
        "job_started",
        "playlist_started",
        "track_matched",
        "track_skipped",
        "track_unmatched",
        "playlist_done",
        "job_done",
        "error",
    ]
    playlist_id: str | None = None
    playlist_name: str | None = None
    current: int | None = None
    total: int | None = None
    track_title: str | None = None
    target_playlist_id: str | None = None
    message: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class PlaylistTransferOutcome(BaseModel):
    source_playlist: Playlist
    target_playlist_id: str | None
    target_playlist_name: str
    action: Literal["created", "appended", "replaced", "skipped"]
    matched_count: int
    unmatched_count: int
    skipped_count: int
    unmatched: list[MatchResult] = Field(default_factory=list)


class TransferReport(BaseModel):
    direction: TransferDirection
    started_at: datetime
    finished_at: datetime
    idempotency: IdempotencyMode
    playlists: list[PlaylistTransferOutcome] = Field(default_factory=list)

    @property
    def total_matched(self) -> int:
        return sum(p.matched_count for p in self.playlists)

    @property
    def total_unmatched(self) -> int:
        return sum(p.unmatched_count for p in self.playlists)

    @property
    def total_skipped(self) -> int:
        return sum(p.skipped_count for p in self.playlists)
