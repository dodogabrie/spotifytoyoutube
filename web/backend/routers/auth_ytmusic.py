from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from core.auth.ytmusic_auth import poll_device_flow, start_device_flow
from core.config import get_settings
from web.backend.deps import require_csrf, require_session
from web.backend.schemas import YTMusicPollResponse, YTMusicStartResponse
from web.backend.sessions import SessionData

router = APIRouter(prefix="/auth/ytmusic", tags=["auth"])


@router.post("/start", response_model=YTMusicStartResponse)
def start(session: SessionData = Depends(require_csrf)) -> YTMusicStartResponse:
    settings = get_settings()
    if not settings.ytmusic_client_id:
        raise HTTPException(status_code=400, detail="YTMUSIC_CLIENT_ID not configured")
    flow = start_device_flow(settings.ytmusic_client_id)
    session.ytmusic_device_state = {
        "device_code": flow.device_code,
        "expires_at": time.time() + flow.expires_in,
        "interval": flow.interval,
    }
    return YTMusicStartResponse(
        verification_url=flow.verification_url,
        user_code=flow.user_code,
        interval=flow.interval,
        expires_in=flow.expires_in,
    )


@router.post("/poll", response_model=YTMusicPollResponse)
def poll(session: SessionData = Depends(require_csrf)) -> YTMusicPollResponse:
    settings = get_settings()
    state = session.ytmusic_device_state
    if not state:
        raise HTTPException(status_code=400, detail="No device flow in progress")
    if time.time() > state["expires_at"]:
        session.ytmusic_device_state = None
        return YTMusicPollResponse(status="expired")
    result = poll_device_flow(
        settings.ytmusic_client_id,
        settings.ytmusic_client_secret,
        state["device_code"],
    )
    if result.status == "authorized" and result.credentials:
        session.ytmusic_token = result.credentials
        session.ytmusic_device_state = None
    return YTMusicPollResponse(status=result.status, error=result.error)


@router.post("/logout")
def logout(session: SessionData = Depends(require_csrf)) -> dict:
    session.ytmusic_token = None
    session.ytmusic_device_state = None
    return {"ok": True}


@router.get("/status")
def status(session: SessionData = Depends(require_session)) -> dict:
    return {
        "spotify_connected": session.spotify_token_info is not None,
        "ytmusic_connected": session.ytmusic_token is not None,
    }
