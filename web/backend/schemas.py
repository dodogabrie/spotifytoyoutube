from __future__ import annotations

from pydantic import BaseModel

from core.models import IdempotencyMode, TransferDirection


class AuthStatus(BaseModel):
    spotify_connected: bool
    ytmusic_connected: bool


class YTMusicStartResponse(BaseModel):
    verification_url: str
    user_code: str
    interval: int
    expires_in: int


class YTMusicPollResponse(BaseModel):
    status: str  # pending | authorized | expired | denied | error
    error: str | None = None


class PlaylistDTO(BaseModel):
    id: str
    name: str
    description: str | None = None
    track_count: int | None = None
    public: bool | None = None
    collaborative: bool = False


class TransferRequest(BaseModel):
    direction: TransferDirection
    playlist_ids: list[str]
    idempotency: IdempotencyMode = IdempotencyMode.CREATE_NEW


class JobCreated(BaseModel):
    job_id: str


class JobSnapshot(BaseModel):
    job_id: str
    status: str  # queued | running | done | error
    direction: TransferDirection
    idempotency: IdempotencyMode
    last_events: list[dict] = []
    matched: int = 0
    unmatched: int = 0
    skipped: int = 0
    report_path: str | None = None
    error: str | None = None
