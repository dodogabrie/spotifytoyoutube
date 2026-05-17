from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException, Response, status

from core.config import get_settings
from web.backend.sessions import CSRF_COOKIE, SESSION_COOKIE, SessionData, SessionStore, get_store


def get_session_store() -> SessionStore:
    return get_store()


def get_or_create_session(
    response: Response,
    store: SessionStore = Depends(get_session_store),
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionData:
    session = store.get(session_cookie)
    if session is None:
        secure = get_settings().session_cookie_secure
        session = store.create()
        response.set_cookie(
            key=SESSION_COOKIE,
            value=session.session_id,
            httponly=True,
            samesite="lax",
            secure=secure,
            max_age=60 * 60 * 6,
            path="/",
        )
        response.set_cookie(
            key=CSRF_COOKIE,
            value=session.csrf_token,
            httponly=False,  # readable by JS for double-submit
            samesite="lax",
            secure=secure,
            max_age=60 * 60 * 6,
            path="/",
        )
    return session


def require_session(
    store: SessionStore = Depends(get_session_store),
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionData:
    session = store.get(session_cookie)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")
    return session


def require_csrf(
    session: SessionData = Depends(require_session),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> SessionData:
    if not x_csrf_token or x_csrf_token != session.csrf_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token mismatch")
    return session


def require_spotify(session: SessionData = Depends(require_session)) -> SessionData:
    if not session.spotify_token_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Spotify not authorized")
    return session


def require_ytmusic(session: SessionData = Depends(require_session)) -> SessionData:
    if not session.ytmusic_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="YT Music not authorized")
    return session
