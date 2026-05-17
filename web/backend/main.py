from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    return app


app = create_app()
