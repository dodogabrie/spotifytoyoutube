from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from core.auth.spotify_auth import build_web_auth_manager
from core.config import get_settings
from web.backend.deps import get_or_create_session, require_csrf
from web.backend.sessions import SessionData

router = APIRouter(prefix="/auth/spotify", tags=["auth"])


@router.get("/login")
def login(session: SessionData = Depends(get_or_create_session)) -> RedirectResponse:
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    session.spotify_oauth_state = state
    auth_manager = build_web_auth_manager(settings, state=state)
    # store the PKCE verifier on the session so we can finish the exchange in /callback
    session.spotify_code_verifier = auth_manager.code_verifier
    url = auth_manager.get_authorize_url()
    return RedirectResponse(url=url, status_code=302)


@router.get("/callback")
def callback(request: Request, code: str | None = None, state: str | None = None,
             session: SessionData = Depends(get_or_create_session)) -> RedirectResponse:
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")
    if not session.spotify_oauth_state or state != session.spotify_oauth_state:
        raise HTTPException(status_code=400, detail="OAuth state mismatch")
    settings = get_settings()
    auth_manager = build_web_auth_manager(settings, state=state)
    if session.spotify_code_verifier:
        auth_manager.code_verifier = session.spotify_code_verifier
    token_info = auth_manager.get_access_token(code=code, as_dict=True)
    if not token_info:
        raise HTTPException(status_code=400, detail="Spotify token exchange failed")
    session.spotify_token_info = token_info
    session.spotify_oauth_state = None
    session.spotify_code_verifier = None
    # Redirect to the SPA. In dev that's :5173.
    origin = settings.cors_origins_list[0] if settings.cors_origins_list else "/"
    return RedirectResponse(url=f"{origin}/playlists", status_code=302)


@router.post("/logout")
def logout(session: SessionData = Depends(require_csrf)) -> dict:
    session.spotify_token_info = None
    return {"ok": True}
