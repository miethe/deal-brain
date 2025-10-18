"""Application settings leveraging pydantic-settings."""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AdapterConfig(BaseModel):
    """Configuration for a single URL ingestion adapter."""

    enabled: bool = Field(
        default=True,
        description="Whether this adapter is enabled",
    )
    timeout_s: int = Field(
        default=8,
        ge=1,
        le=60,
        description="Request timeout in seconds",
    )
    retries: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Maximum retry attempts",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authenticated adapters (from environment)",
    )


class IngestionSettings(BaseModel):
    """Configuration for URL ingestion system."""

    ingestion_enabled: bool = Field(
        default=True,
        description="Master switch for URL ingestion feature",
    )

    # Per-adapter configurations
    ebay: AdapterConfig = Field(
        default_factory=lambda: AdapterConfig(
            enabled=True,
            timeout_s=6,
            retries=2,
        ),
        description="eBay adapter configuration",
    )
    jsonld: AdapterConfig = Field(
        default_factory=lambda: AdapterConfig(
            enabled=True,
            timeout_s=8,
            retries=1,
        ),
        description="JSON-LD adapter configuration",
    )
    amazon: AdapterConfig = Field(
        default_factory=lambda: AdapterConfig(
            enabled=False,  # P1 phase - not implemented yet
            timeout_s=8,
            retries=1,
        ),
        description="Amazon adapter configuration (P1 - disabled)",
    )

    # Price change detection
    price_change_threshold_pct: float = Field(
        default=2.0,
        ge=0.0,
        le=100.0,
        description="Emit price change event if price changes by this percentage",
    )
    price_change_threshold_abs: Decimal = Field(
        default=Decimal("1.0"),
        ge=0,
        description="Emit price change event if price changes by this absolute amount (USD)",
    )

    # Raw payload management
    raw_payload_ttl_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Time-to-live for raw payload data in days",
    )
    raw_payload_max_bytes: int = Field(
        default=524288,  # 512KB
        ge=1024,
        le=10485760,  # 10MB max
        description="Maximum raw payload size in bytes (512KB default)",
    )


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

    analytics_enabled: bool = True

    # URL Ingestion settings
    ingestion: IngestionSettings = Field(
        default_factory=IngestionSettings,
        description="URL ingestion configuration",
    )

    # Environment variable overrides for adapter API keys
    ebay_api_key: str | None = Field(
        default=None,
        description="eBay API key (loaded from EBAY_API_KEY env var)",
    )
    amazon_api_key: str | None = Field(
        default=None,
        description="Amazon API key (loaded from AMAZON_API_KEY env var)",
    )

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to inject API keys into adapter configs."""
        if self.ebay_api_key:
            self.ingestion.ebay.api_key = self.ebay_api_key
        if self.amazon_api_key:
            self.ingestion.amazon.api_key = self.amazon_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


__all__ = [
    "AdapterConfig",
    "IngestionSettings",
    "Settings",
    "get_settings",
]
