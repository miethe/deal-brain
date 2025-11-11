"""Component management for listings.

This module handles listing component synchronization, component input building,
and component relationship preparation for listings.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterable

from dealbrain_core.enums import ComponentType
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from dealbrain_core.valuation import ComponentValuationInput
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import Listing, ListingComponent
from ...telemetry import get_logger
from ..component_catalog import (
    get_or_create_ram_spec,
    get_or_create_storage_profile,
    normalize_int,
    normalize_ram_generation,
    normalize_ram_spec_payload,
    normalize_storage_profile_payload,
    storage_medium_display,
)

if TYPE_CHECKING:
    pass

logger = get_logger("dealbrain.listings.components")


async def sync_listing_components(
    session: AsyncSession,
    listing: Listing,
    components_payload: list[dict] | None,
) -> None:
    """Replace listing components using explicit SQL to avoid lazy relationship access."""
    if components_payload is None:
        return

    await session.execute(delete(ListingComponent).where(ListingComponent.listing_id == listing.id))
    await session.flush()

    for component in components_payload:
        payload = dict(component)
        component_type = payload.get("component_type")
        if not component_type:
            fallback = getattr(ComponentType, "OTHER", None)
            component_type = fallback.value if fallback else "misc"
        session.add(
            ListingComponent(
                listing_id=listing.id,
                rule_id=payload.get("rule_id"),
                component_type=component_type,
                name=payload.get("name"),
                quantity=payload.get("quantity", 1),
                metadata_json=payload.get("metadata_json"),
                adjustment_value_usd=payload.get("adjustment_value_usd"),
            ),
        )
    await session.flush()
    logger.info(
        "listing.components.synced",
        listing_id=listing.id,
        component_count=len(components_payload),
    )


def build_component_inputs(listing: Listing) -> Iterable[ComponentValuationInput]:
    """Build component valuation inputs from listing data.

    Yields ComponentValuationInput instances for:
    - RAM (if ram_gb present)
    - Primary storage (if primary_storage_gb present)
    - Secondary storage (if secondary_storage_gb present)
    - OS license (if os_license present)
    - All listing components
    """
    from .valuation import storage_component_type

    if listing.ram_gb:
        yield ComponentValuationInput(
            component_type=ComponentType.RAM,
            quantity=float(listing.ram_gb),
            label=f"RAM {listing.ram_gb}GB",
        )
    if listing.primary_storage_gb:
        yield ComponentValuationInput(
            component_type=storage_component_type(listing.primary_storage_type),
            quantity=float(listing.primary_storage_gb),
            label=f"Primary Storage {listing.primary_storage_gb}GB",
        )
    if listing.secondary_storage_gb:
        yield ComponentValuationInput(
            component_type=storage_component_type(listing.secondary_storage_type),
            quantity=float(listing.secondary_storage_gb),
            label=f"Secondary Storage {listing.secondary_storage_gb}GB",
        )
    if listing.os_license:
        yield ComponentValuationInput(
            component_type=ComponentType.OS_LICENSE,
            quantity=1,
            label=f"OS License {listing.os_license}",
        )
    for component in listing.components:
        from .valuation import _coerce_component_type

        component_type = _coerce_component_type(component.component_type)
        quantity = float(component.quantity or 1)
        yield ComponentValuationInput(
            component_type=component_type,
            quantity=quantity,
            label=component.name or component_type.value,
        )


async def _prepare_component_relationships(
    session: AsyncSession,
    payload: dict[str, Any],
    *,
    listing: Listing | None = None,
) -> None:
    """Resolve or create component relationships for a listing payload.

    Handles:
    - RAM spec resolution/creation from ram_spec payload or hints
    - Storage profile resolution/creation for primary and secondary storage
    - Fallback to existing listing data if not provided in payload

    Modifies payload in-place by setting:
    - ram_spec_id (and ram_gb if available)
    - primary_storage_profile_id (and capacity/type if available)
    - secondary_storage_profile_id (and capacity/type if available)
    """
    ram_type_hint = payload.pop("ram_type", None)
    ram_speed_hint = payload.pop("ram_speed_mhz", None)
    ram_spec_payload = payload.pop("ram_spec", None)

    if "ram_spec_id" not in payload:
        total_capacity = normalize_int(payload.get("ram_gb"))
        if total_capacity is None and listing:
            total_capacity = (
                listing.ram_spec.total_capacity_gb if listing.ram_spec else listing.ram_gb
            )
        spec_input = normalize_ram_spec_payload(
            ram_spec_payload,
            fallback_total_gb=total_capacity,
            fallback_generation=normalize_ram_generation(ram_type_hint)
            if ram_type_hint
            else (listing.ram_spec.ddr_generation if listing and listing.ram_spec else None),
            fallback_speed=
            normalize_int(ram_speed_hint)
            or (listing.ram_spec.speed_mhz if listing and listing.ram_spec else None),
        )
        if spec_input:
            ram_spec = await get_or_create_ram_spec(session, spec_input)
            payload["ram_spec_id"] = ram_spec.id
            if payload.get("ram_gb") is None and ram_spec.total_capacity_gb is not None:
                payload["ram_gb"] = ram_spec.total_capacity_gb
        elif ram_spec_payload or ram_type_hint or ram_speed_hint:
            # If hints were provided but unusable, raise to surface validation issues
            raise ValueError("RAM specification details were provided but could not be resolved")

    for prefix in ("primary", "secondary"):
        profile_key = f"{prefix}_storage_profile"
        profile_id_key = f"{prefix}_storage_profile_id"
        storage_type_key = f"{prefix}_storage_type"
        capacity_key = f"{prefix}_storage_gb"
        existing_profile = getattr(listing, f"{prefix}_storage_profile") if listing else None

        profile_payload = payload.pop(profile_key, None)
        if profile_id_key in payload:
            continue

        fallback_capacity = normalize_int(payload.get(capacity_key))
        if fallback_capacity is None:
            if existing_profile and existing_profile.capacity_gb is not None:
                fallback_capacity = existing_profile.capacity_gb
            elif listing:
                fallback_capacity = normalize_int(getattr(listing, f"{prefix}_storage_gb", None))

        fallback_type = payload.get(storage_type_key)
        if fallback_type is None:
            if existing_profile and existing_profile.medium:
                fallback_type = existing_profile.medium
            elif listing:
                fallback_type = getattr(listing, storage_type_key, None)

        profile_input = normalize_storage_profile_payload(
            profile_payload,
            fallback_capacity_gb=fallback_capacity,
            fallback_type=fallback_type,
        )

        if not profile_input:
            continue

        storage_profile = await get_or_create_storage_profile(session, profile_input)
        payload[profile_id_key] = storage_profile.id

        if (
            payload.get(capacity_key) is None
            and storage_profile.capacity_gb is not None
        ):
            payload[capacity_key] = storage_profile.capacity_gb

        # Import here to avoid circular dependency
        from dealbrain_core.enums import StorageMedium

        if storage_profile.medium and storage_profile.medium != StorageMedium.UNKNOWN:
            payload[storage_type_key] = payload.get(storage_type_key) or storage_medium_display(
                storage_profile.medium
            )


async def complete_partial_import(
    session: AsyncSession,
    listing_id: int,
    completion_data: dict[str, Any],
    user_id: str,
) -> Listing:
    """
    Complete a partial import by providing missing fields.

    This method is called by the manual population modal when user
    provides missing data (typically price). It updates the listing,
    recalculates metrics, and marks as complete.

    Args:
        session: Database session
        listing_id: Listing to complete
        completion_data: Dict with missing fields (e.g., {"price": 299.99})
        user_id: User completing the import

    Returns:
        Updated listing with metrics calculated

    Raises:
        ValueError: If listing not found or not partial
        ValueError: If price invalid (must be positive)

    Example:
        >>> updated = await complete_partial_import(
        ...     session=session,
        ...     listing_id=123,
        ...     completion_data={"price": 299.99},
        ...     user_id="user123",
        ... )
        >>> assert updated.quality == "full"
        >>> assert updated.price_usd == 299.99
    """
    from .valuation import apply_listing_metrics

    # Fetch and validate listing
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    if listing.quality != "partial":
        raise ValueError(
            f"Listing {listing_id} is already complete (quality={listing.quality}). "
            "Only partial listings can be completed."
        )

    # Update price field if provided
    if "price" in completion_data:
        price_value = completion_data["price"]

        # Validate price is numeric
        try:
            price_float = float(price_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid price value: {price_value}. Price must be a numeric value."
            ) from exc

        # Validate price is positive
        if price_float <= 0:
            raise ValueError(
                f"Invalid price value: {price_float}. Price must be greater than 0."
            )

        # Update listing price
        listing.price_usd = price_float

        # Track in extraction_metadata (need to create new dict for SQLAlchemy to detect change)
        metadata = dict(listing.extraction_metadata or {})
        metadata["price"] = "manual"
        listing.extraction_metadata = metadata

        # Remove "price" from missing_fields if present (create new list for SQLAlchemy to detect change)
        if listing.missing_fields and "price" in listing.missing_fields:
            listing.missing_fields = [
                field for field in listing.missing_fields if field != "price"
            ]

    # Update quality if all required fields are present
    if listing.price_usd is not None and (not listing.missing_fields or len(listing.missing_fields) == 0):
        listing.quality = "full"

    await session.flush()

    # Calculate metrics if quality is now "full" and price exists
    if listing.quality == "full" and listing.price_usd is not None:
        await apply_listing_metrics(session, listing)
        logger.info(
            "listing.partial_import.completed",
            listing_id=listing.id,
            title=listing.title,
            price=listing.price_usd,
            user_id=user_id,
            message="Partial listing completed with metrics calculated",
        )
    else:
        logger.info(
            "listing.partial_import.updated",
            listing_id=listing.id,
            title=listing.title,
            quality=listing.quality,
            missing_fields=listing.missing_fields,
            user_id=user_id,
            message="Partial listing updated but still incomplete",
        )

    await session.flush()
    await session.refresh(listing)

    return listing


async def create_from_ingestion(
    session: AsyncSession,
    normalized_data: NormalizedListingSchema,
    user_id: str | None = None,
) -> Listing:
    """Create listing from normalized ingestion data.

    Supports both partial and complete imports:
    - If price is None: Creates partial listing without metrics calculation
    - If price is provided: Creates complete listing with full metrics

    Args:
        session: Database session (caller controls transaction)
        normalized_data: Normalized listing data from adapter
        user_id: User ID for audit trail (optional)

    Returns:
        Created Listing instance

    Raises:
        ValueError: If normalized data invalid or required fields missing

    Example:
        >>> from dealbrain_core.schemas.ingestion import NormalizedListingSchema
        >>> normalized = NormalizedListingSchema(
        ...     title="Gaming PC",
        ...     price=Decimal("599.99"),
        ...     currency="USD",
        ...     condition="new",
        ...     marketplace="ebay",
        ...     quality="full",
        ... )
        >>> listing = await create_from_ingestion(session, normalized)
    """
    from decimal import Decimal

    from dealbrain_core.enums import Condition

    from .valuation import apply_listing_metrics

    # Validate input
    if not isinstance(normalized_data, NormalizedListingSchema):
        raise ValueError("normalized_data must be a NormalizedListingSchema instance")

    # Map condition string to enum
    condition_map = {
        "new": Condition.NEW,
        "refurb": Condition.REFURB,
        "used": Condition.USED,
    }
    condition_enum = condition_map.get(normalized_data.condition.lower(), Condition.USED)

    # Determine quality: use explicit quality from schema, or infer from price presence
    quality = normalized_data.quality
    if quality == "full" and normalized_data.price is None:
        # If marked as full but missing price, downgrade to partial
        quality = "partial"

    # Create listing with base fields
    listing = Listing(
        title=normalized_data.title,
        price_usd=float(normalized_data.price) if normalized_data.price else None,
        condition=condition_enum.value,
        quality=quality,
        extraction_metadata=normalized_data.extraction_metadata or {},
        missing_fields=normalized_data.missing_fields or [],
        marketplace=normalized_data.marketplace,
        vendor_item_id=normalized_data.vendor_item_id,
        seller=normalized_data.seller,
        last_seen_at=datetime.utcnow(),
    )

    # Store images in attributes_json if provided
    if normalized_data.images:
        listing.attributes_json = {"images": normalized_data.images}

    # Store extracted component data if available
    # Note: CPU/GPU/RAM/Storage matching would happen in a separate enrichment step
    # For now, just store raw extracted values in attributes_json
    component_attrs = {}
    if normalized_data.cpu_model:
        component_attrs["cpu_model_raw"] = normalized_data.cpu_model
    if normalized_data.ram_gb is not None:
        listing.ram_gb = normalized_data.ram_gb
    if normalized_data.storage_gb is not None:
        listing.primary_storage_gb = normalized_data.storage_gb
    if normalized_data.manufacturer:
        listing.manufacturer = normalized_data.manufacturer
    if normalized_data.model_number:
        listing.device_model = normalized_data.model_number

    if component_attrs:
        attrs = dict(listing.attributes_json or {})
        attrs.update(component_attrs)
        listing.attributes_json = attrs

    session.add(listing)
    await session.flush()  # Get ID without committing

    # Only calculate metrics if price exists
    if listing.price_usd is not None:
        await apply_listing_metrics(session, listing)
        logger.info(
            "listing.created_from_ingestion.complete",
            listing_id=listing.id,
            title=listing.title,
            price=listing.price_usd,
            quality=quality,
            marketplace=normalized_data.marketplace,
        )
    else:
        # Set valuation_breakdown to None for partial imports
        listing.valuation_breakdown = None
        logger.info(
            "listing.created_from_ingestion.partial",
            listing_id=listing.id,
            title=listing.title,
            quality=quality,
            marketplace=normalized_data.marketplace,
            missing_fields=normalized_data.missing_fields,
            message="Listing created without price - metrics deferred until completion",
        )

    return listing


async def upsert_from_url(
    session: AsyncSession,
    normalized: NormalizedListingSchema,
    dedupe_result: Any,  # DeduplicationResult to avoid circular import
) -> Listing:
    """Upsert listing from URL ingestion.

    If dedup match found, updates existing listing with new data.
    If new listing, creates listing with URL ingestion metadata.

    This method integrates URL ingestion with existing ListingsService,
    maintaining backward compatibility with Excel import flow.

    Args:
    ----
        session: Database session (caller controls transaction)
        normalized: Normalized listing data from adapter
        dedupe_result: Deduplication result with match info

    Returns:
    -------
        Created or updated Listing instance

    Raises:
    ------
        ValueError: If normalized data invalid or condition cannot be mapped

    Example:
    -------
        >>> from dealbrain_core.schemas.ingestion import NormalizedListingSchema
        >>> from dealbrain_api.services.ingestion import DeduplicationResult
        >>>
        >>> normalized = NormalizedListingSchema(
        ...     title="Gaming PC",
        ...     price=Decimal("599.99"),
        ...     currency="USD",
        ...     condition="new",
        ...     marketplace="ebay",
        ...     vendor_item_id="123456789012",
        ...     provenance="ebay_api",
        ...     dedup_hash="abc123...",
        ... )
        >>> dedupe_result = DeduplicationResult(
        ...     exists=False,
        ...     existing_listing=None,
        ...     is_exact_match=False,
        ...     confidence=0.0,
        ...     dedup_hash="abc123...",
        ... )
        >>> listing = await upsert_from_url(session, normalized, dedupe_result)

    """
    from decimal import Decimal

    from dealbrain_core.enums import Condition
    from dealbrain_core.schemas.ingestion import NormalizedListingSchema

    from .valuation import apply_listing_metrics

    # Import IngestionEventService locally to avoid circular imports
    from ..ingestion import IngestionEventService

    # Validate input
    if not isinstance(normalized, NormalizedListingSchema):
        raise ValueError("normalized must be a NormalizedListingSchema instance")

    # Initialize event service for price change tracking
    event_service = IngestionEventService()

    # Map condition string to enum
    condition_map = {
        "new": Condition.NEW,
        "refurb": Condition.REFURB,
        "used": Condition.USED,
    }
    condition_enum = condition_map.get(normalized.condition.lower(), Condition.USED)

    if dedupe_result.exists and dedupe_result.existing_listing:
        # UPDATE PATH: Update existing listing
        existing = dedupe_result.existing_listing

        # Check if price changed for event emission
        old_price = Decimal(str(existing.price_usd))
        new_price = normalized.price

        # Update mutable fields
        existing.price_usd = float(new_price)
        existing.condition = condition_enum.value

        # Update images if provided
        if normalized.images:
            # Store images as JSON array (need to check model schema)
            # For now, store in attributes_json as the Listing model doesn't have images field
            attrs = dict(existing.attributes_json or {})
            attrs["images"] = normalized.images
            existing.attributes_json = attrs

        # Update timestamps
        existing.last_seen_at = datetime.utcnow()

        await session.flush()

        # Emit price.changed event if threshold met
        if old_price != new_price:
            emitted = event_service.check_and_emit_price_change(
                existing, old_price, new_price,
            )
            logger.debug(
                "Price change event emission",
                extra={
                    "listing_id": existing.id,
                    "old_price": float(old_price),
                    "new_price": float(new_price),
                    "emitted": emitted,
                },
            )

        return existing

    # CREATE PATH: Create new listing
    # Get dedup hash from DeduplicationResult (generated by DeduplicationService)
    dedup_hash = dedupe_result.dedup_hash

    listing = Listing(
        title=normalized.title,
        price_usd=float(normalized.price),
        condition=condition_enum.value,
        marketplace=normalized.marketplace,
        vendor_item_id=normalized.vendor_item_id,
        seller=normalized.seller,
        dedup_hash=dedup_hash,
        last_seen_at=datetime.utcnow(),
    )

    # Store images in attributes_json if provided
    if normalized.images:
        listing.attributes_json = {"images": normalized.images}

    # Store provenance if available in normalized data
    # Note: provenance is not in NormalizedListingSchema but should be tracked
    # It will be set by the caller (IngestionService)

    session.add(listing)
    await session.flush()  # Get ID without committing

    # Apply valuation rules and calculate metrics
    await apply_listing_metrics(session, listing)

    # Emit listing.created event
    # Note: We don't have provenance or quality in this method
    # Those should be emitted by the caller (IngestionService)
    logger.info(
        "Created new listing from URL ingestion",
        extra={
            "listing_id": listing.id,
            "title": listing.title,
            "price": listing.price_usd,
            "marketplace": listing.marketplace,
        },
    )

    return listing
