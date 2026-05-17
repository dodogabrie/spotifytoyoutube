from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from time import time
from typing import Any

SESSION_COOKIE = "sty_session"
CSRF_COOKIE = "XSRF-TOKEN"
SESSION_TTL_SECONDS = 60 * 60 * 6  # 6 hours


@dataclass
class SessionData:
    session_id: str
    csrf_token: str
    created_at: float = field(default_factory=time)
    last_seen: float = field(default_factory=time)

    spotify_token_info: dict[str, Any] | None = None
    spotify_oauth_state: str | None = None
    spotify_code_verifier: str | None = None

    ytmusic_device_state: dict[str, Any] | None = None  # device_code, expires_at, client_id
    ytmusic_token: dict[str, Any] | None = None

    def touch(self) -> None:
        self.last_seen = time()

    def is_expired(self) -> bool:
        return (time() - self.last_seen) > SESSION_TTL_SECONDS


class SessionStore:
    """In-memory session store. Replaceable by Redis-backed implementation later."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.Lock()

    def create(self) -> SessionData:
        with self._lock:
            sid = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            data = SessionData(session_id=sid, csrf_token=csrf)
            self._sessions[sid] = data
            return data

    def get(self, sid: str | None) -> SessionData | None:
        if not sid:
            return None
        with self._lock:
            data = self._sessions.get(sid)
            if data is None:
                return None
            if data.is_expired():
                self._sessions.pop(sid, None)
                return None
            data.touch()
            return data

    def delete(self, sid: str | None) -> None:
        if not sid:
            return
        with self._lock:
            self._sessions.pop(sid, None)


_store = SessionStore()


def get_store() -> SessionStore:
    return _store
