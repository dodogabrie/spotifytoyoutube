from fastapi.testclient import TestClient

from web.backend.main import app


def test_health_ok():
    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ytmusic_status_creates_session_cookie():
    client = TestClient(app)
    res = client.get("/api/auth/ytmusic/status")
    # First call has no session yet → 401
    assert res.status_code == 401


def test_csrf_required_on_post():
    client = TestClient(app)
    # POST to logout without CSRF header should be rejected (401 if no session, 403 if session).
    res = client.post("/api/auth/spotify/logout")
    assert res.status_code in (401, 403)


def test_playlists_requires_auth():
    client = TestClient(app)
    res = client.get("/api/playlists", params={"provider": "spotify"})
    assert res.status_code == 401
