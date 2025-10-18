# IngestionEventService - Usage Examples

This document provides practical examples for using the IngestionEventService in Deal Brain's URL ingestion system.

## Basic Setup

```python
from dealbrain_api.services.ingestion import IngestionEventService
from decimal import Decimal

# Initialize the event service
event_service = IngestionEventService()
```

## Example 1: Emit Listing Created Event

When a new listing is successfully imported from a URL:

```python
from dealbrain_api.models.core import Listing
from datetime import datetime

# After creating and saving a new listing
new_listing = Listing(
    id=123,
    title="HP EliteDesk 800 G6 Mini Desktop",
    price_usd=599.99,
    marketplace="ebay",
    vendor_item_id="123456789012",
    created_at=datetime.utcnow()
)

# Emit event with provenance and quality metadata
event_service.emit_listing_created(
    listing=new_listing,
    provenance="ebay_api",  # ebay_api | jsonld
    quality="full"          # full | partial
)

print(f"✓ Emitted listing.created event for: {new_listing.title}")
```

## Example 2: Check and Emit Price Change

When updating an existing listing with a new price:

```python
from decimal import Decimal

# Existing listing
existing_listing = Listing(
    id=456,
    title="Dell OptiPlex 7080 Micro",
    price_usd=549.99,  # NEW price
    marketplace="ebay",
    vendor_item_id="987654321098"
)

# Old price from database
old_price = Decimal("599.99")
new_price = Decimal("549.99")

# Check if price change is significant and emit if so
# Automatically reads thresholds from settings
emitted = event_service.check_and_emit_price_change(
    listing=existing_listing,
    old_price=old_price,
    new_price=new_price
)

if emitted:
    change_amount = new_price - old_price
    change_percent = (change_amount / old_price) * 100
    print(f"🔔 Price alert: {existing_listing.title}")
    print(f"   ${old_price} → ${new_price} ({change_percent:.1f}%)")
else:
    print(f"No significant price change for: {existing_listing.title}")
```

## Example 3: Process All Events

Retrieve and process all emitted events:

```python
from dealbrain_api.services.ingestion import (
    ListingCreatedEvent,
    PriceChangedEvent
)

# Get all events
events = event_service.get_events()

print(f"Processing {len(events)} events...")

for event in events:
    if isinstance(event, ListingCreatedEvent):
        print(f"📦 New Listing:")
        print(f"   Title: {event.title}")
        print(f"   Price: ${event.price}")
        print(f"   Source: {event.provenance}")
        print(f"   Quality: {event.quality}")
        print(f"   Marketplace: {event.marketplace}")

    elif isinstance(event, PriceChangedEvent):
        print(f"💲 Price Change:")
        print(f"   Title: {event.title}")
        print(f"   Old: ${event.old_price}")
        print(f"   New: ${event.new_price}")
        print(f"   Change: ${event.change_amount} ({event.change_percent:.2f}%)")
        print(f"   Marketplace: {event.marketplace}")
```

## Example 4: Integration with Ingestion Pipeline

Complete example of using event service in an ingestion workflow:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from dealbrain_api.services.ingestion import (
    DeduplicationService,
    ListingNormalizer,
    IngestionEventService
)
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

async def import_listing_from_url(
    url: str,
    session: AsyncSession,
    event_service: IngestionEventService
):
    """Import listing from URL and emit events."""

    # 1. Scrape and normalize data (from adapter)
    normalized_data = await scrape_and_normalize(url)

    # 2. Check for duplicates
    dedup_service = DeduplicationService(session)
    result = await dedup_service.find_existing_listing(normalized_data)

    if result.exists:
        # Update existing listing
        existing_listing = result.existing_listing
        old_price = Decimal(str(existing_listing.price_usd))
        new_price = normalized_data.price

        # Update price
        existing_listing.price_usd = float(new_price)
        await session.commit()

        # Check and emit price change event
        event_service.check_and_emit_price_change(
            existing_listing,
            old_price,
            new_price
        )

        return existing_listing
    else:
        # Create new listing
        new_listing = Listing(
            title=normalized_data.title,
            price_usd=float(normalized_data.price),
            marketplace=normalized_data.marketplace,
            vendor_item_id=normalized_data.vendor_item_id,
            # ... other fields
        )

        session.add(new_listing)
        await session.commit()

        # Emit listing created event
        normalizer = ListingNormalizer(session)
        quality = normalizer.assess_quality(normalized_data)

        event_service.emit_listing_created(
            new_listing,
            provenance=determine_provenance(url),
            quality=quality
        )

        return new_listing
```

## Example 5: Custom Threshold Logic

Testing price change detection with custom thresholds:

```python
from dealbrain_api.services.ingestion import should_emit_price_change

# Default thresholds from settings:
# - Absolute: $1.00
# - Percent: 2.0%

# Test various price changes
test_cases = [
    (Decimal("100.00"), Decimal("98.00"), "Should emit (2% and $2)"),
    (Decimal("100.00"), Decimal("99.00"), "Should emit (1% but $1)"),
    (Decimal("100.00"), Decimal("99.50"), "Should NOT emit (0.5% and $0.50)"),
    (Decimal("1000.00"), Decimal("995.00"), "Should emit ($5 but 0.5%)"),
]

for old_price, new_price, description in test_cases:
    should_emit = should_emit_price_change(
        old_price,
        new_price,
        threshold_abs=Decimal("1.00"),
        threshold_pct=Decimal("2.0")
    )

    change_abs = abs(new_price - old_price)
    change_pct = abs((new_price - old_price) / old_price * 100)

    print(f"{description}")
    print(f"  Price: ${old_price} → ${new_price}")
    print(f"  Change: ${change_abs} ({change_pct:.2f}%)")
    print(f"  Emit: {should_emit}")
    print()
```

## Example 6: Event Service in API Endpoint

Using event service in a FastAPI endpoint:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dealbrain_api.db import get_session
from dealbrain_api.services.ingestion import IngestionEventService

router = APIRouter()

# Global event service instance (or use dependency injection)
event_service = IngestionEventService()

@router.post("/api/ingest")
async def ingest_url(
    url: str,
    session: AsyncSession = Depends(get_session)
):
    """Ingest listing from URL and emit events."""

    # Import listing
    listing = await import_listing_from_url(url, session, event_service)

    # Process events (send to Celery, webhooks, etc.)
    events = event_service.get_events()

    # In Phase 3+, send events to background workers
    # for event in events:
    #     send_to_celery_task(event)

    # Clear events after processing
    event_service.clear_events()

    return {
        "listing_id": listing.id,
        "events_emitted": len(events)
    }
```

## Example 7: Test Isolation

Using clear_events() for test isolation:

```python
import pytest

@pytest.fixture
def event_service():
    """Provide clean event service for each test."""
    service = IngestionEventService()
    yield service
    service.clear_events()  # Cleanup after test

def test_listing_created(event_service):
    """Test listing creation emits event."""
    listing = create_test_listing()

    event_service.emit_listing_created(listing, "ebay_api", "full")

    events = event_service.get_events()
    assert len(events) == 1
    assert isinstance(events[0], ListingCreatedEvent)
    # event_service automatically cleared by fixture
```

## Example 8: Price Change Scenarios

Real-world price change scenarios:

```python
from decimal import Decimal

scenarios = [
    # (old_price, new_price, expected_emit, reason)
    (
        Decimal("599.99"),
        Decimal("549.99"),
        True,
        "Major price drop: $50 (8.3%)"
    ),
    (
        Decimal("599.99"),
        Decimal("598.99"),
        False,
        "Minor adjustment: $1 (0.17%)"
    ),
    (
        Decimal("99.99"),
        Decimal("109.99"),
        True,
        "Price increase: $10 (10%)"
    ),
    (
        Decimal("1000.00"),
        Decimal("995.00"),
        True,
        "Small % but large $: $5 (0.5%)"
    ),
]

for old, new, expected, reason in scenarios:
    listing = create_listing(price=float(new))

    emitted = event_service.check_and_emit_price_change(listing, old, new)

    print(f"{reason}")
    print(f"  Emitted: {emitted} (expected: {expected})")
    assert emitted == expected

    if emitted:
        event = event_service.get_events()[-1]
        print(f"  Change: ${event.change_amount} ({event.change_percent:.2f}%)")

    print()
```

## Configuration

Event emission is controlled by settings in `apps/api/dealbrain_api/settings.py`:

```python
class IngestionSettings(BaseModel):
    # Price change thresholds
    price_change_threshold_pct: float = 2.0   # 2%
    price_change_threshold_abs: Decimal = Decimal("1.0")  # $1.00
```

Adjust these values to control event sensitivity:

```python
# In .env or environment variables
INGESTION__PRICE_CHANGE_THRESHOLD_PCT=1.5  # More sensitive (1.5%)
INGESTION__PRICE_CHANGE_THRESHOLD_ABS=0.50  # More sensitive ($0.50)
```

## Future Integration (Phase 3+)

### Celery Task Example

```python
from celery import shared_task

@shared_task
def process_listing_created(event_data: dict):
    """Background task for new listing events."""
    # Send email notification
    # Update search index
    # Trigger analytics pipeline
    pass

@shared_task
def process_price_changed(event_data: dict):
    """Background task for price change events."""
    # Check user watchlists
    # Send price alerts
    # Update price history
    pass

# In event service (Phase 3):
def emit_listing_created(self, listing, provenance, quality):
    event = ListingCreatedEvent(...)
    self._events.append(event)

    # Send to Celery
    process_listing_created.delay(asdict(event))
```

### Webhook Example

```python
import httpx

async def send_webhook(event: ListingCreatedEvent | PriceChangedEvent):
    """Send event to external webhook."""
    webhook_url = settings.webhook_url

    async with httpx.AsyncClient() as client:
        await client.post(
            webhook_url,
            json={
                "event_type": type(event).__name__,
                "data": asdict(event)
            }
        )
```

## Best Practices

1. **Always clear events** after processing in production
2. **Use Decimal** for all price calculations
3. **Check settings** before manual threshold checks
4. **Emit events consistently** across all import paths
5. **Test with fixtures** to ensure isolation
6. **Document provenance** for debugging
7. **Monitor event volume** for performance tuning

## Troubleshooting

### No events emitted

```python
# Check if thresholds are too high
from dealbrain_api.settings import get_settings
settings = get_settings()
print(f"Abs: {settings.ingestion.price_change_threshold_abs}")
print(f"Pct: {settings.ingestion.price_change_threshold_pct}")
```

### Events not persisting

```python
# Remember: events are in-memory in Phase 2
# They don't survive process restarts
# Clear events after processing to avoid memory buildup
event_service.clear_events()
```

### Duplicate events

```python
# Use clear_events() after processing
# Or create new service instance per request
event_service = IngestionEventService()
```

## See Also

- Task ID-014 Implementation Summary
- Settings Documentation
- Ingestion Service Documentation
- Phase 3 Event Processing Plan
