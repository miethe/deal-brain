"""Schemas for URL ingestion workflow."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field, HttpUrl, field_validator

from ..enums import Condition, Marketplace
from .base import DealBrainModel


class NormalizedListingSchema(DealBrainModel):
    """
    Normalized listing data extracted from any adapter.

    This schema represents the canonical format that all adapters
    (eBay API, JSON-LD, generic scraper) must produce. It contains
    the essential listing information needed to create a Listing record.

    Attributes:
        title: Product title/name
        price: Listing price (always positive)
        currency: ISO currency code (default USD)
        condition: Product condition (maps to Condition enum)
        images: List of image URLs
        seller: Seller name or identifier (optional)
        marketplace: Source marketplace (ebay|amazon|other)
        vendor_item_id: Marketplace-specific item ID (optional)
        cpu_model: Extracted CPU model string (optional)
        ram_gb: Extracted RAM amount in GB (optional)
        storage_gb: Extracted storage amount in GB (optional)
        description: Full product description text (optional)
    """

    title: str = Field(
        ...,
        description="Product title/name",
        min_length=1,
        max_length=500,
    )
    price: Decimal = Field(
        ...,
        description="Listing price (must be positive)",
        gt=0,
        decimal_places=2,
    )
    currency: str = Field(
        default="USD",
        description="ISO currency code",
        pattern=r"^[A-Z]{3}$",
    )
    condition: str = Field(
        ...,
        description="Product condition (new|refurb|used)",
    )
    images: list[str] = Field(
        default_factory=list,
        description="List of image URLs",
    )
    seller: str | None = Field(
        default=None,
        description="Seller name or identifier",
        max_length=200,
    )
    marketplace: str = Field(
        ...,
        description="Source marketplace (ebay|amazon|other)",
    )
    vendor_item_id: str | None = Field(
        default=None,
        description="Marketplace-specific item ID (e.g., eBay item number)",
        max_length=100,
    )
    cpu_model: str | None = Field(
        default=None,
        description="Extracted CPU model string",
        max_length=200,
    )
    ram_gb: int | None = Field(
        default=None,
        description="Extracted RAM amount in GB",
        ge=0,
    )
    storage_gb: int | None = Field(
        default=None,
        description="Extracted storage amount in GB",
        ge=0,
    )
    description: str | None = Field(
        default=None,
        description="Full product description text",
    )

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str) -> str:
        """Validate condition maps to valid Condition enum value."""
        value_lower = value.lower()
        try:
            Condition(value_lower)
            return value_lower
        except ValueError as e:
            raise ValueError(
                f"Invalid condition: {value}. Must be one of: "
                f"{', '.join([c.value for c in Condition])}"
            ) from e

    @field_validator("marketplace")
    @classmethod
    def validate_marketplace(cls, value: str) -> str:
        """Validate marketplace maps to valid Marketplace enum value."""
        value_lower = value.lower()
        try:
            Marketplace(value_lower)
            return value_lower
        except ValueError as e:
            raise ValueError(
                f"Invalid marketplace: {value}. Must be one of: "
                f"{', '.join([m.value for m in Marketplace])}"
            ) from e

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, value: Any) -> list[str]:
        """Ensure images is always a list."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)


class IngestionRequest(DealBrainModel):
    """
    Request schema for single URL import.

    Attributes:
        url: Valid HTTP/HTTPS URL to import
        priority: Import priority level (normal|high)
    """

    url: HttpUrl = Field(
        ...,
        description="Valid HTTP/HTTPS URL to import",
    )
    priority: str = Field(
        default="normal",
        description="Import priority level",
        pattern=r"^(normal|high)$",
    )


class IngestionResponse(DealBrainModel):
    """
    Response schema for single URL import.

    Attributes:
        job_id: Unique job identifier (UUID or session ID)
        status: Job status (queued|running|complete|partial|failed)
        progress_pct: Progress percentage (0-100)
        listing_id: Created listing ID if successful (optional)
        provenance: Data source used (ebay_api|jsonld|scraper)
        quality: Data quality level (full|partial)
        errors: List of error details if any issues occurred
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier",
    )
    status: str = Field(
        ...,
        description="Job status",
        pattern=r"^(queued|running|complete|partial|failed)$",
    )
    progress_pct: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Progress percentage (0-100)",
    )
    listing_id: int | None = Field(
        default=None,
        description="Created listing ID if successful",
    )
    provenance: str | None = Field(
        default=None,
        description="Data source used (ebay_api|jsonld|scraper)",
        pattern=r"^(ebay_api|jsonld|scraper)$",
    )
    quality: str | None = Field(
        default=None,
        description="Data quality level (full|partial)",
        pattern=r"^(full|partial)$",
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of error details",
    )


class BulkIngestionRequest(DealBrainModel):
    """
    Request schema for bulk URL import.

    Attributes:
        urls: List of URLs to import (1-100 URLs)
    """

    urls: list[str] = Field(
        ...,
        description="List of URLs to import",
        min_length=1,
        max_length=100,
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, value: list[str]) -> list[str]:
        """Validate all URLs are valid HTTP/HTTPS URLs."""
        validated_urls = []
        for url in value:
            # Validate using HttpUrl
            try:
                validated_url = HttpUrl(url)
                validated_urls.append(str(validated_url))
            except Exception as e:
                raise ValueError(f"Invalid URL '{url}': {e}") from e
        return validated_urls


class BulkIngestionResponse(DealBrainModel):
    """
    Response schema for bulk URL import.

    Attributes:
        bulk_job_id: Unique bulk job identifier
        total_urls: Total number of URLs submitted
        per_row_statuses: Per-URL status information (optional)
    """

    bulk_job_id: str = Field(
        ...,
        description="Unique bulk job identifier",
    )
    total_urls: int = Field(
        ...,
        description="Total number of URLs submitted",
        ge=1,
    )
    per_row_statuses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-URL status information",
    )


class PerRowStatus(DealBrainModel):
    """
    Per-URL status information for bulk ingestion.

    Attributes:
        url: The URL being processed
        status: Job status (queued|running|complete|partial|failed)
        listing_id: Created listing ID if successful (optional)
        error: Error message if failed (optional)
    """

    url: str = Field(
        ...,
        description="The URL being processed",
    )
    status: str = Field(
        ...,
        description="Job status",
        pattern=r"^(queued|running|complete|partial|failed)$",
    )
    listing_id: int | None = Field(
        default=None,
        description="Created listing ID if successful",
    )
    error: str | None = Field(
        default=None,
        description="Error message if failed",
    )


class BulkIngestionStatusResponse(DealBrainModel):
    """
    Response schema for bulk ingestion status poll endpoint.

    Attributes:
        bulk_job_id: Unique bulk job identifier
        status: Overall bulk job status (queued|running|complete|partial|failed)
        total_urls: Total number of URLs in the bulk job
        completed: Number of URLs that finished processing (complete + partial + failed)
        success: Number of URLs successfully completed (complete only)
        partial: Number of URLs partially completed
        failed: Number of URLs that failed
        running: Number of URLs currently running
        queued: Number of URLs still queued
        per_row_status: Per-URL status information with pagination
        offset: Pagination offset
        limit: Pagination limit
        has_more: Whether there are more results beyond current page
    """

    bulk_job_id: str = Field(
        ...,
        description="Unique bulk job identifier",
    )
    status: str = Field(
        ...,
        description="Overall bulk job status",
        pattern=r"^(queued|running|complete|partial|failed)$",
    )
    total_urls: int = Field(
        ...,
        description="Total number of URLs in the bulk job",
        ge=0,
    )
    completed: int = Field(
        ...,
        description="Number of URLs that finished processing",
        ge=0,
    )
    success: int = Field(
        ...,
        description="Number of URLs successfully completed",
        ge=0,
    )
    partial: int = Field(
        ...,
        description="Number of URLs partially completed",
        ge=0,
    )
    failed: int = Field(
        ...,
        description="Number of URLs that failed",
        ge=0,
    )
    running: int = Field(
        ...,
        description="Number of URLs currently running",
        ge=0,
    )
    queued: int = Field(
        ...,
        description="Number of URLs still queued",
        ge=0,
    )
    per_row_status: list[PerRowStatus] = Field(
        default_factory=list,
        description="Per-URL status information with pagination",
    )
    offset: int = Field(
        ...,
        description="Pagination offset",
        ge=0,
    )
    limit: int = Field(
        ...,
        description="Pagination limit",
        ge=1,
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more results beyond current page",
    )


__all__ = [
    "NormalizedListingSchema",
    "IngestionRequest",
    "IngestionResponse",
    "BulkIngestionRequest",
    "BulkIngestionResponse",
    "PerRowStatus",
    "BulkIngestionStatusResponse",
]
