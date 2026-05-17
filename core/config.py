from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/api/auth/spotify/callback"
    spotify_cli_redirect_uri: str = "http://127.0.0.1:8888/callback"

    ytmusic_client_id: str = ""
    ytmusic_client_secret: str = ""

    app_secret_key: str = "dev-insecure-change-me"
    web_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    match_score_threshold: float = 0.62

    reports_dir: Path = Field(default=Path("./reports"))
    secrets_dir: Path = Field(default=Path("./secrets"))

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.web_cors_origins.split(",") if o.strip()]

    @property
    def spotify_cache_path(self) -> Path:
        return self.secrets_dir / ".spotify-cache"

    @property
    def ytmusic_oauth_path(self) -> Path:
        return self.secrets_dir / "oauth.json"

    def ensure_dirs(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
