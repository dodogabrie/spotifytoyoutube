from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from core.logging_setup import configure_logging
from web.backend.routers import auth_spotify, auth_ytmusic, playlists, transfer


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    settings.ensure_dirs()

    app = FastAPI(
        title="Spotify ⇄ YouTube Music Transfer",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_spotify.router, prefix="/api")
    app.include_router(auth_ytmusic.router, prefix="/api")
    app.include_router(playlists.router, prefix="/api")
    app.include_router(transfer.router, prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    _mount_spa(app, settings.web_static_dir)

    return app


def _mount_spa(app: FastAPI, static_dir: Path | None) -> None:
    if static_dir is None:
        return
    static_dir = Path(static_dir)
    if not static_dir.is_dir():
        return

    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_file = static_dir / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith(("api/", "ws/", "assets/")):
            raise HTTPException(status_code=404)
        candidate = static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(status_code=404)


app = create_app()
