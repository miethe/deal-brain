"""CRUD operations for listings.

This module handles basic create, read, update, and delete operations for listings,
along with payload normalization and validation utilities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...events import EventType, publish_event
from ...models import Listing, Profile
from ...telemetry import get_logger

logger = get_logger("dealbrain.listings.crud")

# Fields that should trigger card cache invalidation when updated
CACHE_INVALIDATION_FIELDS: set[str] = {
    "price_usd",
    "adjusted_price_usd",
    "cpu_id",
    "gpu_id",
    "ram_gb",
    "primary_storage_gb",
    "primary_storage_type",
    "secondary_storage_gb",
    "secondary_storage_type",
    "title",
    "manufacturer",
    "series",
    "score_composite",
}

# Mutable fields that can be updated via partial_update_listing
MUTABLE_LISTING_FIELDS: set[str] = {
    "title",
    "listing_url",
    "other_urls",
    "seller",
    "price_usd",
    "price_date",
    "condition",
    "status",
    "cpu_id",
    "gpu_id",
    "ports_profile_id",
    "ram_spec_id",
    "primary_storage_profile_id",
    "secondary_storage_profile_id",
    "device_model",
    "ram_gb",
    "ram_notes",
    "primary_storage_gb",
    "primary_storage_type",
    "secondary_storage_gb",
    "secondary_storage_type",
    "os_license",
    "notes",
    "ruleset_id",
    # Partial import fields (Phase 1)
    "quality",
    "extraction_metadata",
    "missing_fields",
    "vendor_item_id",
    "marketplace",
    "provenance",
}


def _normalize_listing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle legacy field aliases and normalize payload keys."""
    if "url" in payload and "listing_url" not in payload:
        payload["listing_url"] = payload.pop("url")
    if "listing_url" in payload:
        payload["listing_url"] = _sanitize_primary_url(payload["listing_url"])
    if "other_urls" in payload:
        payload["other_urls"] = _normalize_other_urls(payload["other_urls"])
    return payload


def _sanitize_primary_url(value: Any) -> str | None:
    """Sanitize and validate primary listing URL."""
    if value in (None, "", []):
        return None
    url_str = str(value).strip()
    parsed = urlparse(url_str)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("listing_url must use http:// or https:// and include a host")
    return url_str


def _normalize_other_urls(value: Any) -> list[dict[str, str | None]]:
    """Normalize supplemental URLs to standardized format."""
    if not value:
        return []
    normalized: list[dict[str, str | None]] = []
    items = value if isinstance(value, (list, tuple)) else [value]
    seen: set[str] = set()
    for item in items:
        if item in (None, "", {}):
            continue
        if isinstance(item, str):
            url = item.strip()
            label = None
        elif isinstance(item, dict):
            url = str(item.get("url") or item.get("href") or "").strip()
            label_value = item.get("label") or item.get("text")
            label = str(label_value).strip() if label_value else None
        else:
            url = str(item).strip()
            label = None
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "Supplemental link URLs must use http:// or https:// and include a host"
            )
        if url in seen:
            continue
        seen.add(url)
        normalized.append({"url": url, "label": label})
    return normalized


async def get_default_profile(session: AsyncSession) -> Profile | None:
    """Get the default scoring profile.

    Returns:
        Default profile if exists, otherwise first profile by ID, or None if no profiles exist
    """
    result = await session.execute(select(Profile).where(Profile.is_default == True))  # noqa: E712
    profile = result.scalars().first()
    if profile:
        return profile
    result = await session.execute(select(Profile).order_by(Profile.id))
    return result.scalars().first()


async def create_listing(session: AsyncSession, payload: dict) -> Listing:
    """Create a new listing.

    Args:
        session: Database session
        payload: Dictionary of listing fields

    Returns:
        Created listing instance

    Note:
        Does NOT apply metrics - caller should call apply_listing_metrics separately
    """
    from .components import _prepare_component_relationships

    # Map "attributes" to "attributes_json" for SQLAlchemy model
    if "attributes" in payload:
        payload["attributes_json"] = payload.pop("attributes")
    payload = _normalize_listing_payload(payload)
    await _prepare_component_relationships(session, payload)
    listing = Listing(**payload)
    session.add(listing)
    await session.flush()
    logger.info(
        "listing.created",
        listing_id=listing.id,
        title=listing.title,
        price=listing.price_usd,
        ruleset_id=listing.ruleset_id,
    )

    # Publish SSE event
    await publish_event(
        EventType.LISTING_CREATED,
        {"listing_id": listing.id, "timestamp": datetime.utcnow().isoformat()},
    )

    return listing


async def update_listing(session: AsyncSession, listing: Listing, payload: dict) -> Listing:
    """Update an existing listing.

    Args:
        session: Database session
        listing: Listing instance to update
        payload: Dictionary of fields to update

    Returns:
        Updated listing instance

    Note:
        Does NOT apply metrics - caller should call apply_listing_metrics separately
    """
    from .components import _prepare_component_relationships

    payload = _normalize_listing_payload(payload)
    await _prepare_component_relationships(session, payload, listing=listing)

    # Track changed fields for event
    changed_fields = list(payload.keys())

    for field, value in payload.items():
        setattr(listing, field, value)
    await session.flush()
    logger.info(
        "listing.updated",
        listing_id=listing.id,
        updated_fields=changed_fields,
        ruleset_id=listing.ruleset_id,
    )

    # Publish SSE event
    await publish_event(
        EventType.LISTING_UPDATED,
        {
            "listing_id": listing.id,
            "changes": changed_fields,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
    # Invalidate card image cache if price or components changed
    await _invalidate_card_cache_if_needed(session, listing, payload)

    return listing


async def partial_update_listing(
    session: AsyncSession,
    listing: Listing,
    fields: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
    *,
    run_metrics: bool = True,
) -> Listing:
    """Update listing with partial field updates and optional metric recalculation.

    Only updates fields in MUTABLE_LISTING_FIELDS whitelist. Handles attributes_json
    merging and automatic metrics recalculation.

    Args:
        session: Database session
        listing: Listing to update
        fields: Dictionary of listing fields to update
        attributes: Dictionary of attributes to merge into attributes_json
        run_metrics: Whether to recalculate metrics after update

    Returns:
        Updated listing instance
    """
    from .components import _prepare_component_relationships
    from .valuation import apply_listing_metrics

    fields = fields or {}
    attributes = attributes or {}
    fields = _normalize_listing_payload(dict(fields))
    await _prepare_component_relationships(session, fields, listing=listing)

    # Track changed fields for event
    changed_fields = []

    for field, value in fields.items():
        if field in MUTABLE_LISTING_FIELDS:
            setattr(listing, field, value)
            changed_fields.append(field)

    if attributes:
        merged = dict(listing.attributes_json or {})
        for key, value in attributes.items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = value
        listing.attributes_json = merged
        changed_fields.append("attributes_json")

    logger.info(
        "listing.partial_update",
        listing_id=listing.id,
        updated_fields=list(fields.keys()),
        attribute_keys=list(attributes.keys()),
        run_metrics=run_metrics,
    )

    await session.flush()

    # Publish SSE event
    await publish_event(
        EventType.LISTING_UPDATED,
        {
            "listing_id": listing.id,
            "changes": changed_fields,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # Check if recalculation should be triggered asynchronously
    # Fields that trigger async recalculation via Celery
    async_recalc_fields = {
        "price_usd",
        "cpu_id",
        "gpu_id",
        "ram_gb",
        "ram_capacity_gb",
        "primary_storage_gb",
        "secondary_storage_gb",
        "ruleset_id",
    }

    should_queue_recalc = bool(set(changed_fields) & async_recalc_fields)
    # Invalidate card image cache if price or components changed
    await _invalidate_card_cache_if_needed(session, listing, fields)

    if run_metrics:
        # Only apply metrics if listing has a price
        if listing.price_usd is not None:
            await apply_listing_metrics(session, listing)
            await session.refresh(listing)
        else:
            logger.info(
                "listing.partial_update.skipped_metrics",
                listing_id=listing.id,
                reason="price_is_none",
            )
    else:
        # If metrics are disabled but recalc fields changed, still consider queuing
        should_queue_recalc = should_queue_recalc and listing.price_usd is not None

    # Queue async recalculation if needed (optional background enhancement)
    # This ensures valuations stay fresh when critical fields change
    if should_queue_recalc:
        from ...tasks.valuation import enqueue_listing_recalculation

        # Queue recalculation (fire-and-forget, non-blocking)
        try:
            enqueue_listing_recalculation(
                listing_ids=[listing.id],
                reason="field_update",
                use_celery=True,
            )
        except Exception as exc:
            logger.warning(
                "listing.recalc.queue_failed",
                listing_id=listing.id,
                error=str(exc),
            )

    return listing


async def bulk_update_listings(
    session: AsyncSession,
    listing_ids: list[int],
    fields: dict[str, Any] | None = None,
    attributes: dict[str, Any] | None = None,
) -> list[Listing]:
    """Update multiple listings with same field updates.

    Args:
        session: Database session
        listing_ids: List of listing IDs to update
        fields: Dictionary of fields to update
        attributes: Dictionary of attributes to merge

    Returns:
        List of updated listings
    """
    from .valuation import apply_listing_metrics

    if not listing_ids:
        return []

    result = await session.execute(select(Listing).where(Listing.id.in_(listing_ids)))
    listings = result.scalars().unique().all()
    if not listings:
        return []

    for listing in listings:
        await partial_update_listing(
            session,
            listing,
            fields,
            attributes,
            run_metrics=False,
        )

    await session.flush()
    for listing in listings:
        # Only apply metrics if listing has a price
        if listing.price_usd is not None:
            await apply_listing_metrics(session, listing)
        else:
            logger.info(
                "listing.bulk_update.skipped_metrics",
                listing_id=listing.id,
                reason="price_is_none",
            )
    await session.flush()
    for listing in listings:
        await session.refresh(listing)
    return listings


async def delete_listing(
    session: AsyncSession,
    listing_id: int,
) -> None:
    """Delete listing and cascade related records.

    Cascades delete to:
    - ListingComponent records
    - ListingScoreSnapshot records
    - RawPayload records
    - EntityFieldValue records (custom fields) via DB FK cascade

    Args:
    ----
        session: Database session
        listing_id: ID of listing to delete

    Raises:
    ------
        ValueError: Listing not found
    """
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    logger.info(
        "listing.delete",
        listing_id=listing_id,
        title=listing.title,
    )

    await session.delete(listing)
    await session.commit()

    logger.info(
        "listing.deleted",
        listing_id=listing_id,
    )

    # Publish SSE event
    await publish_event(
        EventType.LISTING_DELETED,
        {"listing_id": listing_id, "timestamp": datetime.utcnow().isoformat()},
    )

async def _invalidate_card_cache_if_needed(
    session: AsyncSession,
    listing: Listing,
    updated_fields: dict[str, Any],
) -> None:
    """Invalidate card image cache if relevant fields changed.

    Checks if any fields that affect card rendering were updated,
    and if so, invalidates all cached card images for the listing.

    Args:
        session: Database session
        listing: Listing instance
        updated_fields: Dictionary of updated fields
    """
    # Check if any cache-invalidation fields were updated
    should_invalidate = any(
        field in CACHE_INVALIDATION_FIELDS
        for field in updated_fields.keys()
    )

    if not should_invalidate:
        return

    # Import here to avoid circular dependency
    try:
        from ..image_generation import ImageGenerationService

        # Create service and invalidate cache
        image_service = ImageGenerationService(session)
        deleted_count = await image_service.invalidate_cache(listing.id)

        if deleted_count > 0:
            logger.info(
                "listing.card_cache_invalidated",
                listing_id=listing.id,
                deleted_count=deleted_count,
                updated_fields=list(updated_fields.keys()),
            )
    except Exception as e:
        # Don't fail the update if cache invalidation fails
        logger.warning(
            "listing.card_cache_invalidation_failed",
            listing_id=listing.id,
            error=str(e),
        )
