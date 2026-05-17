"""YouTube Music authentication helpers.

We implement the OAuth 2.0 device-code flow explicitly using Google's official
endpoints so the web flow can drive it step-by-step. The same flow is used
internally by ``ytmusicapi.setup_oauth`` for the CLI helper.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from core.exceptions import AuthError

logger = logging.getLogger(__name__)

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/youtube"
# ytmusicapi sends this user-agent for the OAuth handshake (TV/limited-input device profile).
USER_AGENT = "Mozilla/5.0 (Linux; U; Android 9; en-us; Pixel 3 XL Build/PD1A.180720.030) Cookie"


@dataclass
class DeviceFlowStart:
    device_code: str
    user_code: str
    verification_url: str
    interval: int
    expires_in: int


@dataclass
class DeviceFlowResult:
    status: str  # "pending" | "authorized" | "expired" | "denied" | "error"
    credentials: dict[str, Any] | None = None
    error: str | None = None


def start_device_flow(client_id: str) -> DeviceFlowStart:
    response = httpx.post(
        DEVICE_CODE_URL,
        data={"client_id": client_id, "scope": SCOPE},
        headers={"User-Agent": USER_AGENT},
        timeout=15.0,
    )
    if response.status_code != 200:
        raise AuthError(f"Failed to start device flow: HTTP {response.status_code} {response.text}")
    data = response.json()
    return DeviceFlowStart(
        device_code=data["device_code"],
        user_code=data["user_code"],
        verification_url=data.get("verification_url") or data.get("verification_uri", ""),
        interval=int(data.get("interval", 5)),
        expires_in=int(data.get("expires_in", 1800)),
    )


def poll_device_flow(client_id: str, client_secret: str, device_code: str) -> DeviceFlowResult:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=15.0,
    )
    payload = response.json() if response.content else {}

    if response.status_code == 200 and "access_token" in payload:
        return DeviceFlowResult(status="authorized", credentials=payload)

    error = payload.get("error")
    if error == "authorization_pending":
        return DeviceFlowResult(status="pending")
    if error == "slow_down":
        return DeviceFlowResult(status="pending")
    if error == "expired_token":
        return DeviceFlowResult(status="expired", error=error)
    if error == "access_denied":
        return DeviceFlowResult(status="denied", error=error)
    return DeviceFlowResult(status="error", error=str(payload or response.text))


def wait_for_authorization(
    client_id: str,
    client_secret: str,
    flow: DeviceFlowStart,
    on_tick: callable | None = None,  # type: ignore[valid-type]
) -> dict[str, Any]:
    """Block until the user authorizes (or the flow expires). For CLI use."""
    deadline = time.monotonic() + flow.expires_in
    interval = flow.interval
    while time.monotonic() < deadline:
        result = poll_device_flow(client_id, client_secret, flow.device_code)
        if on_tick:
            on_tick(result)
        if result.status == "authorized" and result.credentials:
            return result.credentials
        if result.status in ("expired", "denied", "error"):
            raise AuthError(f"YT Music device flow {result.status}: {result.error}")
        time.sleep(interval)
    raise AuthError("YT Music device flow expired before authorization")
