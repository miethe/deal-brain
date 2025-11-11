"""Ingestion service orchestration and public API exports.

This module provides:
1. Public API exports for all ingestion components (backward compatibility)
2. IngestionService - Main orchestration service for URL ingestion workflow
3. IngestionResult - Result dataclass for ingestion operations

The ingestion service has been refactored into focused modules:
- converters.py: Currency and condition conversion utilities
- quality.py: Quality assessment and spec extraction utilities
- deduplication.py: Deduplication service and result dataclass
- normalizer.py: Listing normalization and enrichment service
- events.py: Event tracking and emission service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from dealbrain_api.adapters import AdapterRouter
from dealbrain_api.models.core import Listing, RawPayload
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ...telemetry import get_logger

# Import all components for public API
from .converters import (
    CONDITION_MAPPING,
    CURRENCY_RATES,
    convert_to_usd,
    normalize_condition,
)
from .deduplication import DeduplicationResult, DeduplicationService
from .events import (
    IngestionEventService,
    ListingCreatedEvent,
    PriceChangedEvent,
    should_emit_price_change,
)
from .normalizer import ListingNormalizer
from .quality import (
    CPU_PATTERN,
    RAM_PATTERN,
    STORAGE_PATTERN,
    assess_quality,
    extract_specs,
    parse_brand_and_model,
)

logger = get_logger("dealbrain.ingestion")


@dataclass
class IngestionResult:
    """Result of ingesting a single URL.

    Attributes:
        success: Whether ingestion completed successfully
        listing_id: Database ID of created/updated listing (None if failed)
        status: Ingestion status (created|updated|failed)
        provenance: Data source used (ebay_api|jsonld)
        quality: Data quality assessment (full|partial)
        url: Source URL that was ingested
        dedup_result: Deduplication check result (optional)
        error: Error message if ingestion failed (optional)
        title: Listing title (optional)
        price: Listing price in USD (optional)
        vendor_item_id: Marketplace-specific item ID (optional)
        marketplace: Marketplace identifier (ebay|amazon|other)
    """

    # Required fields
    success: bool
    listing_id: int | None
    status: str  # "created" | "updated" | "failed"
    provenance: str  # "ebay_api" | "jsonld"
    quality: str  # "full" | "partial"
    url: str

    # Optional fields with defaults
    dedup_result: DeduplicationResult | None = None
    error: str | None = None
    title: str | None = None
    price: Decimal | None = None
    vendor_item_id: str | None = None
    marketplace: str = "other"


class IngestionService:
    """Orchestrates URL ingestion workflow.

    Coordinates the complete ingestion pipeline:
    1. Select adapter (AdapterRouter)
    2. Extract raw data (adapter.extract())
    3. Normalize and enrich (ListingNormalizer)
    4. Check for duplicates (DeduplicationService)
    5. Upsert listing (create or update)
    6. Emit events (IngestionEventService)
    7. Store raw payload (RawPayload model)

    Example:
        >>> async with session_scope() as session:
        ...     service = IngestionService(session)
        ...     result = await service.ingest_single_url("https://ebay.com/itm/123")
        ...     if result.success:
        ...         print(f"Created listing {result.listing_id}")
    """

    def __init__(self, session: AsyncSession):
        """Initialize ingestion service.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session
        self.router = AdapterRouter()
        self.dedup_service = DeduplicationService(session)
        self.normalizer = ListingNormalizer(session)
        self.event_service = IngestionEventService()

    async def ingest_single_url(self, url: str) -> IngestionResult:
        """Ingest a single URL through complete workflow.

        Orchestrates the full ingestion pipeline from URL to persisted listing.
        Handles errors gracefully and returns result with detailed status.

        Args:
            url: The URL to ingest

        Returns:
            IngestionResult with outcome details (success/failure, listing_id, etc.)

        Example:
            >>> result = await service.ingest_single_url("https://ebay.com/itm/123")
            >>> if result.success:
            ...     print(f"{result.status}: listing {result.listing_id}")
            ... else:
            ...     print(f"Failed: {result.error}")
        """
        logger.info("ingestion.url.start", url=url)
        try:
            # Step 1: Extract raw data via adapter with fallback chain
            raw_data, adapter_name = await self.router.extract(url)

            # Step 2: Normalize and enrich
            normalized = await self.normalizer.normalize(raw_data)

            # Step 3: Check for duplicates
            dedup_result = await self.dedup_service.find_existing_listing(normalized)

            # Step 4: Upsert listing
            if dedup_result.exists and dedup_result.existing_listing:
                listing = await self._update_listing(dedup_result.existing_listing, normalized)
                status = "updated"
            else:
                listing = await self._create_listing(normalized)
                status = "created"

            # Step 4.5: Calculate performance metrics
            if listing.cpu_id:
                from ..listings import apply_listing_metrics

                await apply_listing_metrics(self.session, listing)
                await self.session.refresh(listing)
                logger.info(
                    "ingestion.listing.metrics_applied",
                    listing_id=listing.id,
                    has_adjusted_price=listing.adjusted_price_usd is not None,
                    has_single_thread_metric=listing.dollar_per_cpu_mark_single is not None,
                    has_multi_thread_metric=listing.dollar_per_cpu_mark_multi is not None,
                )

            # Step 5: Emit events
            quality = self.normalizer.assess_quality(normalized)
            if status == "created":
                self.event_service.emit_listing_created(
                    listing, provenance=adapter_name, quality=quality
                )
            elif status == "updated" and dedup_result.existing_listing:
                # Check if price changed significantly
                old_price = Decimal(str(dedup_result.existing_listing.price_usd))
                new_price = normalized.price
                self.event_service.check_and_emit_price_change(listing, old_price, new_price)

            # Step 6: Store raw payload
            await self._store_raw_payload(listing, adapter_name, normalized)

            # Step 7: Return result
            result = IngestionResult(
                success=True,
                listing_id=listing.id,
                status=status,
                provenance=adapter_name,
                quality=quality,
                dedup_result=dedup_result,
                url=url,
                title=listing.title,
                price=Decimal(str(listing.price_usd)),
                vendor_item_id=listing.vendor_item_id,
                marketplace=listing.marketplace,
            )
            logger.info(
                "ingestion.url.completed",
                url=url,
                listing_id=listing.id,
                status=status,
                provenance=adapter_name,
                quality=quality,
                dedup_exists=dedup_result.exists,
                dedup_exact=dedup_result.is_exact_match,
            )
            return result

        except Exception as e:
            logger.exception("ingestion.url.failed", url=url)
            return IngestionResult(
                success=False,
                listing_id=None,
                status="failed",
                provenance="unknown",
                quality="partial",
                error=str(e),
                url=url,
            )

    async def _find_cpu_by_model(self, cpu_model: str) -> int | None:
        """Find CPU by model string using fuzzy matching.

        Args:
            cpu_model: CPU model string to search for

        Returns:
            CPU ID if found, None otherwise
        """
        from dealbrain_api.models.core import Cpu

        if not cpu_model:
            return None

        # Normalize the cpu_model string (lowercase, strip whitespace)
        normalized = cpu_model.lower().strip()

        # Query CPU catalog for exact match first
        stmt = select(Cpu).where(func.lower(Cpu.name).contains(normalized))
        result = await self.session.execute(stmt)
        cpu = result.scalars().first()

        if cpu:
            logger.info(
                "ingestion.cpu.match",
                match_type="model",
                cpu_id=cpu.id,
                cpu_name=cpu.name,
                query=cpu_model,
            )
            return cpu.id

        # Try partial match (e.g., "i9-12900H" matches "Intel Core i9-12900H")
        # Extract key parts (e.g., "12900H" from "Intel Core i9-12900H")
        cpu_keywords = [part for part in normalized.split() if len(part) > 2]
        if cpu_keywords:
            for keyword in cpu_keywords:
                stmt = select(Cpu).where(func.lower(Cpu.name).contains(keyword))
                result = await self.session.execute(stmt)
                cpu = result.scalars().first()
                if cpu:
                    logger.info(
                        "ingestion.cpu.match",
                        match_type="keyword",
                        cpu_id=cpu.id,
                        cpu_name=cpu.name,
                        keyword=keyword,
                        query=cpu_model,
                    )
                    return cpu.id

        logger.warning("ingestion.cpu.not_found", query=cpu_model)
        return None

    async def _create_listing(self, data: NormalizedListingSchema) -> Listing:
        """Create new listing from normalized data.

        Args:
            data: Normalized listing schema from adapter

        Returns:
            Created Listing instance (with ID assigned)

        Raises:
            ValueError: If condition string cannot be mapped to Condition enum
        """
        # Generate dedup hash
        dedup_hash = self.dedup_service._generate_hash(data)

        # Map condition string to enum
        condition_map = {
            "new": Condition.NEW,
            "refurb": Condition.REFURB,
            "used": Condition.USED,
        }
        condition = condition_map.get(data.condition.lower(), Condition.USED)

        # Look up CPU if cpu_model is provided
        cpu_id = None
        if data.cpu_model:
            cpu_id = await self._find_cpu_by_model(data.cpu_model)

        # Prepare attributes_json with images
        attributes_json = {}
        if data.images:
            attributes_json["images"] = data.images
            logger.info(
                "ingestion.images.persist",
                count=len(data.images),
                listing_title=data.title,
            )

        # Create listing with all fields
        listing = Listing(
            title=data.title,
            price_usd=float(data.price) if data.price is not None else 0.00,
            condition=condition.value,
            marketplace=data.marketplace,
            vendor_item_id=data.vendor_item_id,
            seller=data.seller,
            dedup_hash=dedup_hash,
            # NEW FIELDS
            cpu_id=cpu_id,  # Foreign key to CPU table
            ram_gb=data.ram_gb or 0,  # Default to 0 if not provided
            primary_storage_gb=data.storage_gb or 0,  # Default to 0 if not provided
            notes=data.description,  # Store description in notes field
            attributes_json=attributes_json,  # Store images and other metadata
            manufacturer=data.manufacturer,  # Brand/manufacturer
            model_number=data.model_number,  # Model number
            # last_seen_at is auto-set by default
        )

        logger.info(
            "ingestion.listing.created",
            title=listing.title,
            cpu_id=cpu_id,
            ram_gb=data.ram_gb or 0,
            storage_gb=data.storage_gb or 0,
            image_count=len(data.images) if data.images else 0,
            manufacturer=data.manufacturer,
            model_number=data.model_number,
            condition=condition.value,
        )

        self.session.add(listing)
        await self.session.flush()  # Get ID without committing

        return listing

    async def _update_listing(self, existing: Listing, data: NormalizedListingSchema) -> Listing:
        """Update existing listing with new data.

        Updates mutable fields (price, images) and refreshes last_seen_at.
        Does not update immutable fields like title or vendor_item_id.

        Args:
            existing: Existing listing to update
            data: New normalized data from adapter

        Returns:
            Updated Listing instance
        """
        # Update price and check for changes
        old_price = existing.price_usd
        existing.price_usd = float(data.price) if data.price is not None else 0.00
        existing.last_seen_at = datetime.utcnow()

        # Update condition if changed
        condition_map = {
            "new": Condition.NEW,
            "refurb": Condition.REFURB,
            "used": Condition.USED,
        }
        condition = condition_map.get(data.condition.lower(), Condition.USED)
        existing.condition = condition.value

        # Update seller if provided
        if data.seller:
            existing.seller = data.seller

        # NEW: Update all extracted fields
        if data.cpu_model:
            cpu_id = await self._find_cpu_by_model(data.cpu_model)
            if cpu_id:
                existing.cpu_id = cpu_id

        if data.ram_gb is not None:
            existing.ram_gb = data.ram_gb

        if data.storage_gb is not None:
            existing.primary_storage_gb = data.storage_gb

        if data.description:
            existing.notes = data.description

        if data.manufacturer:
            existing.manufacturer = data.manufacturer

        if data.model_number:
            existing.model_number = data.model_number

        if data.images:
            # Merge with existing attributes_json
            if not existing.attributes_json:
                existing.attributes_json = {}
            existing.attributes_json["images"] = data.images
            flag_modified(existing, "attributes_json")  # Tell SQLAlchemy JSON changed

        logger.info(
            "ingestion.listing.updated",
            listing_id=existing.id,
            title=existing.title,
            old_price=float(old_price or 0),
            new_price=float(data.price),
            cpu_id=existing.cpu_id,
            ram_gb=data.ram_gb if data.ram_gb is not None else existing.ram_gb,
            storage_gb=(
                data.storage_gb if data.storage_gb is not None else existing.primary_storage_gb
            ),
            manufacturer=data.manufacturer or existing.manufacturer,
            model_number=data.model_number or existing.model_number,
        )

        await self.session.flush()

        return existing

    async def _store_raw_payload(
        self, listing: Listing, adapter_name: str, raw_data: NormalizedListingSchema
    ) -> None:
        """Store raw normalized data as JSON payload.

        Preserves original adapter data for debugging and re-processing.
        Truncates large payloads to stay within 512KB limit.

        Args:
            listing: Listing instance to attach payload to
            adapter_name: Name of adapter used (ebay|jsonld)
            raw_data: Normalized listing schema to serialize
        """
        import json

        # Convert NormalizedListingSchema to dict
        payload_dict = raw_data.model_dump(mode="json")

        # Truncate if too large (512KB limit from plan)
        payload_json = json.dumps(payload_dict)
        max_size = 512 * 1024  # 512KB

        if len(payload_json) > max_size:
            # Truncate description or other large fields
            payload_dict["description"] = payload_dict.get("description", "")[:1000] + "..."
            payload_json = json.dumps(payload_dict)

        # Create RawPayload record
        raw_payload = RawPayload(
            listing_id=listing.id,
            adapter=adapter_name,
            source_type="json",  # NormalizedListingSchema is always JSON
            payload=payload_json,  # Store as JSON string
            ttl_days=30,  # From plan
        )

        self.session.add(raw_payload)


# Public API exports (backward compatibility)
__all__ = [
    # Main orchestration
    "IngestionService",
    "IngestionResult",
    # Deduplication
    "DeduplicationService",
    "DeduplicationResult",
    # Normalization
    "ListingNormalizer",
    # Events
    "IngestionEventService",
    "ListingCreatedEvent",
    "PriceChangedEvent",
    "should_emit_price_change",
    # Converters
    "CURRENCY_RATES",
    "CONDITION_MAPPING",
    "convert_to_usd",
    "normalize_condition",
    # Quality utilities
    "CPU_PATTERN",
    "RAM_PATTERN",
    "STORAGE_PATTERN",
    "extract_specs",
    "parse_brand_and_model",
    "assess_quality",
]
