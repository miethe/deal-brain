"""Ingestion event tracking and emission.

This module provides event dataclasses and a service for tracking ingestion events:
- listing.created - When a new listing is imported
- price.changed - When an existing listing's price changes significantly

Phase 2 Implementation:
- Uses in-memory event storage for testing
- Future phases will integrate with Celery, webhooks, or event bus
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from dealbrain_api.models.core import Listing


@dataclass
class ListingCreatedEvent:
    """Event emitted when a new listing is created.

    Attributes:
        listing_id: Database ID of the created listing
        title: Listing title
        price: Current price in USD
        marketplace: Marketplace identifier (ebay|amazon|other)
        vendor_item_id: Marketplace-specific item ID (optional)
        provenance: Data source (ebay_api|jsonld)
        quality: Data quality assessment (full|partial)
        created_at: Timestamp when listing was created
    """

    listing_id: int
    title: str
    price: Decimal
    marketplace: str
    vendor_item_id: str | None
    provenance: str
    quality: str
    created_at: datetime


@dataclass
class PriceChangedEvent:
    """Event emitted when a listing's price changes significantly.

    Attributes:
        listing_id: Database ID of the listing
        title: Listing title
        old_price: Previous price in USD
        new_price: Current price in USD
        change_amount: Price difference (new - old, negative = price drop)
        change_percent: Percentage change ((new - old) / old * 100)
        marketplace: Marketplace identifier (ebay|amazon|other)
        vendor_item_id: Marketplace-specific item ID (optional)
        changed_at: Timestamp when price change was detected
    """

    listing_id: int
    title: str
    old_price: Decimal
    new_price: Decimal
    change_amount: Decimal
    change_percent: Decimal
    marketplace: str
    vendor_item_id: str | None
    changed_at: datetime


def should_emit_price_change(
    old_price: Decimal,
    new_price: Decimal,
    threshold_abs: Decimal,
    threshold_pct: Decimal,
) -> bool:
    """Determine if price change is significant enough to emit event.

    Emits if EITHER:
    - Absolute change >= threshold_abs
    - Percent change >= threshold_pct

    Args:
        old_price: Previous price in USD
        new_price: Current price in USD
        threshold_abs: Minimum absolute change threshold (e.g., $1.00)
        threshold_pct: Minimum percent change threshold (e.g., 2.0 for 2%)

    Returns:
        True if price change is significant, False otherwise

    Example:
        >>> should_emit_price_change(
        ...     Decimal("100.00"),
        ...     Decimal("98.00"),
        ...     Decimal("1.00"),
        ...     Decimal("2.0")
        ... )
        True  # $2 change >= $1 threshold AND 2% >= 2% threshold
    """
    change_abs = abs(new_price - old_price)

    # Handle zero old_price edge case
    if old_price == Decimal("0"):
        return change_abs >= threshold_abs

    # Calculate percentage change
    change_pct = abs((new_price - old_price) / old_price * Decimal("100"))

    # Emit if EITHER threshold is met
    return change_abs >= threshold_abs or change_pct >= threshold_pct


class IngestionEventService:
    """Service for emitting ingestion-related events.

    Emits events for:
    - listing.created - When a new listing is imported
    - price.changed - When an existing listing's price changes significantly

    Phase 2 Implementation:
    - Uses in-memory event storage for testing
    - Future phases will integrate with Celery, webhooks, or event bus

    Example:
        >>> event_service = IngestionEventService()
        >>> event_service.emit_listing_created(
        ...     listing=new_listing,
        ...     provenance="ebay_api",
        ...     quality="full"
        ... )
        >>> events = event_service.get_events()
        >>> print(f"Emitted {len(events)} events")
    """

    def __init__(self):
        """Initialize event service with in-memory event storage."""
        self._events: list[ListingCreatedEvent | PriceChangedEvent] = []

    def emit_listing_created(
        self,
        listing: Listing,
        provenance: str,
        quality: str,
    ) -> None:
        """Emit event when new listing is created.

        Args:
            listing: Newly created listing instance
            provenance: Data source (ebay_api|jsonld)
            quality: Data quality assessment (full|partial)

        Example:
            >>> listing = Listing(
            ...     id=1,
            ...     title="Gaming PC",
            ...     price_usd=599.99,
            ...     marketplace="ebay",
            ...     vendor_item_id="123456789012"
            ... )
            >>> event_service.emit_listing_created(listing, "ebay_api", "full")
        """
        event = ListingCreatedEvent(
            listing_id=listing.id,
            title=listing.title,
            price=Decimal(str(listing.price_usd)),
            marketplace=listing.marketplace,
            vendor_item_id=listing.vendor_item_id,
            provenance=provenance,
            quality=quality,
            created_at=listing.created_at,
        )

        self._events.append(event)
        # Future: Send to Celery task, webhook, or event bus

    def emit_price_changed(
        self,
        listing: Listing,
        old_price: Decimal,
        new_price: Decimal,
    ) -> None:
        """Emit event when listing price changes significantly.

        Args:
            listing: Listing instance with updated price
            old_price: Previous price in USD
            new_price: Current price in USD

        Example:
            >>> listing = Listing(
            ...     id=1,
            ...     title="Gaming PC",
            ...     price_usd=549.99,
            ...     marketplace="ebay"
            ... )
            >>> event_service.emit_price_changed(
            ...     listing,
            ...     Decimal("599.99"),
            ...     Decimal("549.99")
            ... )
        """
        change_amount = new_price - old_price

        # Calculate percentage change (handle zero old_price edge case)
        if old_price != Decimal("0"):
            change_percent = (new_price - old_price) / old_price * Decimal("100")
        else:
            change_percent = Decimal("0")

        event = PriceChangedEvent(
            listing_id=listing.id,
            title=listing.title,
            old_price=old_price,
            new_price=new_price,
            change_amount=change_amount,
            change_percent=change_percent,
            marketplace=listing.marketplace,
            vendor_item_id=listing.vendor_item_id,
            changed_at=datetime.utcnow(),
        )

        self._events.append(event)
        # Future: Send to Celery task, webhook, or event bus

    def check_and_emit_price_change(
        self,
        listing: Listing,
        old_price: Decimal,
        new_price: Decimal,
    ) -> bool:
        """Check if price change is significant and emit event if so.

        Reads thresholds from application settings and emits price.changed
        event if either threshold is met.

        Args:
            listing: Listing instance with updated price
            old_price: Previous price in USD
            new_price: Current price in USD

        Returns:
            True if event was emitted, False otherwise

        Example:
            >>> # Assuming settings.ingestion.price_change_threshold_abs = 1.0
            >>> # and settings.ingestion.price_change_threshold_pct = 2.0
            >>> listing = Listing(id=1, title="PC", price_usd=98.00, marketplace="ebay")
            >>> emitted = event_service.check_and_emit_price_change(
            ...     listing,
            ...     Decimal("100.00"),
            ...     Decimal("98.00")
            ... )
            >>> print(f"Event emitted: {emitted}")
            Event emitted: True
        """
        from dealbrain_api.settings import get_settings

        settings = get_settings()

        threshold_abs = Decimal(str(settings.ingestion.price_change_threshold_abs))
        threshold_pct = Decimal(str(settings.ingestion.price_change_threshold_pct))

        if should_emit_price_change(old_price, new_price, threshold_abs, threshold_pct):
            self.emit_price_changed(listing, old_price, new_price)
            return True

        return False

    def get_events(self) -> list[ListingCreatedEvent | PriceChangedEvent]:
        """Get all emitted events (for testing).

        Returns:
            Copy of all emitted events

        Example:
            >>> events = event_service.get_events()
            >>> for event in events:
            ...     if isinstance(event, ListingCreatedEvent):
            ...         print(f"Created: {event.title}")
            ...     elif isinstance(event, PriceChangedEvent):
            ...         print(f"Price changed: {event.title}")
        """
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear all events (for testing).

        Resets the in-memory event storage to empty list.
        Useful for test isolation and cleanup.

        Example:
            >>> event_service.emit_listing_created(listing, "ebay_api", "full")
            >>> len(event_service.get_events())
            1
            >>> event_service.clear_events()
            >>> len(event_service.get_events())
            0
        """
        self._events.clear()


__all__ = [
    "ListingCreatedEvent",
    "PriceChangedEvent",
    "should_emit_price_change",
    "IngestionEventService",
]
