"""Application settings leveraging pydantic-settings."""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

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


class EmailSettings(BaseModel):
    """Configuration for email notifications."""

    enabled: bool = Field(
        default=False,
        description="Enable email notifications. If false, emails won't be sent.",
    )
    smtp_host: str = Field(
        default="localhost",
        description="SMTP server hostname",
    )
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port (587 for TLS, 465 for SSL, 25 for unencrypted)",
    )
    smtp_user: str | None = Field(
        default=None,
        description="SMTP username for authentication",
    )
    smtp_password: str | None = Field(
        default=None,
        description="SMTP password for authentication",
    )
    smtp_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP connection",
    )
    smtp_ssl: bool = Field(
        default=False,
        description="Use SSL for SMTP connection (mutually exclusive with TLS)",
    )
    from_email: str = Field(
        default="noreply@dealbrain.local",
        description="From email address for notifications",
    )
    from_name: str = Field(
        default="Deal Brain",
        description="From name for email notifications",
    )
    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="SMTP connection timeout in seconds",
    )


class TelemetrySettings(BaseModel):
    """Configuration for application telemetry."""

    destination: Literal["console", "json", "otel"] = Field(
        default="console",
        description="Where to send logs/telemetry output.",
    )
    level: str = Field(
        default="INFO",
        description="Verbosity of log entries (DEBUG, INFO, WARNING, ERROR).",
    )
    log_format: Literal["console", "json"] = Field(
        default="console",
        description="Log formatter style. Console is human-readable, JSON is structured.",
    )
    service_name: str = Field(
        default="dealbrain-api",
        description="Service name used for telemetry resources.",
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing pipeline when exporter is configured.",
    )
    otel_endpoint: str | None = Field(
        default=None,
        description="OTLP endpoint for log/trace export, e.g. http://collector:4317",
    )
    suppress_uvicorn_access: bool = Field(
        default=True,
        description="Disable Uvicorn's default access logs when true.",
    )


class PlaywrightSettings(BaseModel):
    """Configuration for Playwright headless browser."""

    enabled: bool = Field(
        default=True,
        description="Enable Playwright for card image generation. If false, feature will be disabled.",
    )
    max_concurrent_browsers: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum number of concurrent browser instances (default 2 to conserve memory)",
    )
    browser_timeout_ms: int = Field(
        default=30000,
        ge=5000,
        le=120000,
        description="Browser operation timeout in milliseconds (default 30s)",
    )
    headless: bool = Field(
        default=True,
        description="Run browsers in headless mode (required for Docker)",
    )


class S3Settings(BaseModel):
    """Configuration for S3 card image caching."""

    enabled: bool = Field(
        default=False,
        description="Enable S3 storage for card images. If false, images won't be cached.",
    )
    bucket_name: str = Field(
        default="dealbrain-card-images",
        description="S3 bucket name for card image storage",
    )
    region: str = Field(
        default="us-east-1",
        description="AWS region for S3 bucket",
    )
    access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID (optional, prefer IAM roles)",
    )
    secret_access_key: str | None = Field(
        default=None,
        description="AWS secret access key (optional, prefer IAM roles)",
    )
    cache_ttl_seconds: int = Field(
        default=2592000,  # 30 days
        ge=86400,  # 1 day minimum
        le=31536000,  # 1 year maximum
        description="Time-to-live for cached card images in seconds (default 30 days)",
    )
    endpoint_url: str | None = Field(
        default=None,
        description="Custom S3 endpoint URL (for LocalStack or MinIO in development)",
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

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

    telemetry: TelemetrySettings = Field(
        default_factory=TelemetrySettings,
        description="Telemetry/logging configuration.",
    )

    # Email settings
    email: EmailSettings = Field(
        default_factory=EmailSettings,
        description="Email notification configuration",
    )

    # URL Ingestion settings
    ingestion: IngestionSettings = Field(
        default_factory=IngestionSettings,
        description="URL ingestion configuration",
    )

    # Playwright settings for card image generation
    playwright: PlaywrightSettings = Field(
        default_factory=PlaywrightSettings,
        description="Playwright headless browser configuration",
    )

    # S3 settings for card image caching
    s3: S3Settings = Field(
        default_factory=S3Settings,
        description="S3 card image caching configuration",
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

    # AWS credentials (override S3 settings if provided)
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID (loaded from AWS_ACCESS_KEY_ID env var)",
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS secret access key (loaded from AWS_SECRET_ACCESS_KEY env var)",
    )
    aws_region: str | None = Field(
        default=None,
        description="AWS region (loaded from AWS_REGION env var)",
    )
    aws_s3_bucket_name: str | None = Field(
        default=None,
        description="S3 bucket name (loaded from AWS_S3_BUCKET_NAME env var)",
    )

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to inject API keys into adapter configs."""
        if self.ebay_api_key:
            self.ingestion.ebay.api_key = self.ebay_api_key
        if self.amazon_api_key:
            self.ingestion.amazon.api_key = self.amazon_api_key

        # Override S3 settings with environment variables if provided
        if self.aws_access_key_id:
            self.s3.access_key_id = self.aws_access_key_id
        if self.aws_secret_access_key:
            self.s3.secret_access_key = self.aws_secret_access_key
        if self.aws_region:
            self.s3.region = self.aws_region
        if self.aws_s3_bucket_name:
            self.s3.bucket_name = self.aws_s3_bucket_name


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


__all__ = [
    "AdapterConfig",
    "EmailSettings",
    "IngestionSettings",
    "TelemetrySettings",
    "PlaywrightSettings",
    "S3Settings",
    "Settings",
    "get_settings",
]
