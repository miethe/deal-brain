"""Application settings leveraging pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str
    sync_database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"

    import_root: Path = PROJECT_ROOT / "data" / "imports"
    export_root: Path = PROJECT_ROOT / "data" / "exports"
    upload_root: Path = PROJECT_ROOT / "data" / "uploads"

    secret_key: str = "changeme"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    prometheus_enabled: bool = True
    otel_exporter_otlp_endpoint: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


__all__ = ["Settings", "get_settings"]
