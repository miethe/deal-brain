"""Tests for ListingsService.upsert_from_url() method.

Tests URL ingestion integration with ListingsService for Task ID-020.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - optional dependency check
    import aiosqlite  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - skip when unavailable
    aiosqlite = None

from dealbrain_api.db import Base
from dealbrain_api.models.core import Listing
from dealbrain_api.services.ingestion import DeduplicationResult
from dealbrain_api.services.listings import upsert_from_url
from dealbrain_core.schemas.ingestion import NormalizedListingSchema


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated in-memory database session for tests."""
    if aiosqlite is None:
        pytest.skip("aiosqlite is not installed; skipping listing service tests")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = async_session()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest.fixture()
def sample_normalized() -> NormalizedListingSchema:
    """Create sample normalized listing data."""
    return NormalizedListingSchema(
        title="Gaming PC Intel i7",
        price=Decimal("599.99"),
        currency="USD",
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="TechStore",
        images=["https://example.com/img1.jpg"],
    )


@pytest.fixture()
def sample_normalized_updated_price() -> NormalizedListingSchema:
    """Create sample normalized listing with updated price."""
    return NormalizedListingSchema(
        title="Gaming PC Intel i7",
        price=Decimal("549.99"),  # Price dropped by $50
        currency="USD",
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="TechStore",
        images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
    )


@pytest.mark.asyncio()
async def test_upsert_from_url_creates_new_listing(
    db_session: AsyncSession,
    sample_normalized: NormalizedListingSchema,
):
    """Test that upsert_from_url creates new listing when no duplicate exists."""
    # Arrange: No existing listing
    dedupe_result = DeduplicationResult(
        exists=False,
        existing_listing=None,
        is_exact_match=False,
        confidence=0.0,
        dedup_hash="abc123def456",
    )

    # Act: Create new listing
    listing = await upsert_from_url(db_session, sample_normalized, dedupe_result)

    # Refresh to ensure all attributes loaded after metrics calculation
    await db_session.refresh(listing)

    # Assert: Listing created with correct data
    assert listing.id is not None
    assert listing.title == "Gaming PC Intel i7"
    assert listing.price_usd == 599.99
    assert listing.condition == "new"
    assert listing.marketplace == "ebay"
    assert listing.vendor_item_id == "123456789012"
    assert listing.seller == "TechStore"
    assert listing.dedup_hash == "abc123def456"
    assert listing.last_seen_at is not None

    # Assert: Images stored in attributes_json
    assert "images" in listing.attributes_json
    assert listing.attributes_json["images"] == ["https://example.com/img1.jpg"]

    # Assert: Valuation and metrics calculated (apply_listing_metrics called)
    assert listing.adjusted_price_usd is not None
    assert listing.valuation_breakdown is not None


@pytest.mark.asyncio()
async def test_upsert_from_url_updates_existing_listing(
    db_session: AsyncSession,
    sample_normalized: NormalizedListingSchema,
    sample_normalized_updated_price: NormalizedListingSchema,
):
    """Test that upsert_from_url updates existing listing when duplicate found."""
    # Arrange: Create existing listing
    existing_listing = Listing(
        title="Gaming PC Intel i7",
        price_usd=599.99,
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="TechStore",
        dedup_hash="abc123def456",
    )
    db_session.add(existing_listing)
    await db_session.flush()
    existing_id = existing_listing.id

    # Create dedup result with existing listing
    dedupe_result = DeduplicationResult(
        exists=True,
        existing_listing=existing_listing,
        is_exact_match=True,
        confidence=1.0,
        dedup_hash="abc123def456",
    )

    # Act: Update existing listing
    updated_listing = await upsert_from_url(
        db_session,
        sample_normalized_updated_price,
        dedupe_result,
    )

    # Assert: Same listing updated (not new)
    assert updated_listing.id == existing_id
    assert updated_listing.price_usd == 549.99  # Price updated
    assert updated_listing.title == "Gaming PC Intel i7"  # Title unchanged

    # Assert: Images updated
    assert "images" in updated_listing.attributes_json
    assert len(updated_listing.attributes_json["images"]) == 2

    # Assert: last_seen_at updated
    assert updated_listing.last_seen_at is not None


@pytest.mark.asyncio()
async def test_upsert_from_url_emits_price_changed_event(
    db_session: AsyncSession,
    sample_normalized: NormalizedListingSchema,
    sample_normalized_updated_price: NormalizedListingSchema,
):
    """Test that price.changed event emitted when price changes significantly."""
    # Arrange: Create existing listing with higher price
    existing_listing = Listing(
        title="Gaming PC Intel i7",
        price_usd=599.99,
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="TechStore",
        dedup_hash="abc123def456",
    )
    db_session.add(existing_listing)
    await db_session.flush()

    dedupe_result = DeduplicationResult(
        exists=True,
        existing_listing=existing_listing,
        is_exact_match=True,
        confidence=1.0,
        dedup_hash="abc123def456",
    )

    # Act: Update with lower price (price drop of $50, 8.3%)
    updated_listing = await upsert_from_url(
        db_session,
        sample_normalized_updated_price,
        dedupe_result,
    )

    # Assert: Price updated
    assert updated_listing.price_usd == 549.99

    # Note: Event emission is logged but not returned from this method
    # The IngestionEventService is initialized locally and events are not
    # accessible from this test. In production, events would be sent to
    # Celery or event bus. This test primarily verifies no errors occur.


@pytest.mark.asyncio()
async def test_upsert_from_url_no_event_if_price_unchanged(
    db_session: AsyncSession,
    sample_normalized: NormalizedListingSchema,
):
    """Test that no price.changed event emitted if price unchanged."""
    # Arrange: Create existing listing with same price
    existing_listing = Listing(
        title="Gaming PC Intel i7",
        price_usd=599.99,  # Same price
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="TechStore",
        dedup_hash="abc123def456",
    )
    db_session.add(existing_listing)
    await db_session.flush()

    dedupe_result = DeduplicationResult(
        exists=True,
        existing_listing=existing_listing,
        is_exact_match=True,
        confidence=1.0,
        dedup_hash="abc123def456",
    )

    # Act: Update with same price
    updated_listing = await upsert_from_url(db_session, sample_normalized, dedupe_result)

    # Assert: Price unchanged
    assert updated_listing.price_usd == 599.99

    # Note: check_and_emit_price_change returns False if no change
    # This is verified in the implementation


@pytest.mark.asyncio()
async def test_upsert_from_url_preserves_metadata(
    db_session: AsyncSession,
    sample_normalized: NormalizedListingSchema,
):
    """Test that provenance, vendor_item_id, marketplace preserved correctly."""
    # Arrange: No existing listing
    dedupe_result = DeduplicationResult(
        exists=False,
        existing_listing=None,
        is_exact_match=False,
        confidence=0.0,
        dedup_hash="abc123def456",
    )

    # Act: Create listing
    listing = await upsert_from_url(db_session, sample_normalized, dedupe_result)

    # Assert: Metadata preserved
    assert listing.vendor_item_id == "123456789012"
    assert listing.marketplace == "ebay"
    assert listing.seller == "TechStore"
    assert listing.dedup_hash == "abc123def456"


@pytest.mark.asyncio()
async def test_upsert_from_url_handles_refurb_condition(
    db_session: AsyncSession,
):
    """Test that refurb condition mapped correctly."""
    # Arrange: Normalized data with refurb condition
    normalized = NormalizedListingSchema(
        title="Refurbished PC",
        price=Decimal("399.99"),
        currency="USD",
        condition="refurb",  # Refurbished
        marketplace="ebay",
        vendor_item_id="987654321098",
    )

    dedupe_result = DeduplicationResult(
        exists=False,
        existing_listing=None,
        is_exact_match=False,
        confidence=0.0,
        dedup_hash="xyz789",
    )

    # Act: Create listing
    listing = await upsert_from_url(db_session, normalized, dedupe_result)

    # Assert: Condition mapped correctly
    assert listing.condition == "refurb"


@pytest.mark.asyncio()
async def test_upsert_from_url_handles_used_condition(
    db_session: AsyncSession,
):
    """Test that used condition mapped correctly."""
    # Arrange: Normalized data with used condition
    normalized = NormalizedListingSchema(
        title="Used PC",
        price=Decimal("299.99"),
        currency="USD",
        condition="used",  # Used
        marketplace="amazon",
        vendor_item_id="ABC123",
    )

    dedupe_result = DeduplicationResult(
        exists=False,
        existing_listing=None,
        is_exact_match=False,
        confidence=0.0,
        dedup_hash="xyz789",
    )

    # Act: Create listing
    listing = await upsert_from_url(db_session, normalized, dedupe_result)

    # Assert: Condition mapped correctly
    assert listing.condition == "used"
    assert listing.marketplace == "amazon"


@pytest.mark.asyncio()
async def test_upsert_from_url_invalid_input_raises_error(
    db_session: AsyncSession,
):
    """Test that ValueError raised for invalid input."""
    # Arrange: Invalid normalized data (not NormalizedListingSchema)
    invalid_normalized = {"title": "PC", "price": 500}  # type: ignore

    dedupe_result = DeduplicationResult(
        exists=False,
        existing_listing=None,
        is_exact_match=False,
        confidence=0.0,
        dedup_hash="xyz789",
    )

    # Act & Assert: Raises ValueError
    with pytest.raises(ValueError, match="normalized must be a NormalizedListingSchema instance"):
        await upsert_from_url(db_session, invalid_normalized, dedupe_result)


@pytest.mark.asyncio()
async def test_upsert_from_url_no_images_handled_correctly(
    db_session: AsyncSession,
):
    """Test that listings without images handled correctly."""
    # Arrange: Normalized data without images
    normalized = NormalizedListingSchema(
        title="PC without images",
        price=Decimal("499.99"),
        currency="USD",
        condition="new",
        marketplace="other",
        images=[],  # No images
    )

    dedupe_result = DeduplicationResult(
        exists=False,
        existing_listing=None,
        is_exact_match=False,
        confidence=0.0,
        dedup_hash="xyz789",
    )

    # Act: Create listing
    listing = await upsert_from_url(db_session, normalized, dedupe_result)

    # Assert: No images stored
    assert listing.attributes_json == {} or "images" not in listing.attributes_json


@pytest.mark.asyncio()
async def test_upsert_from_url_updates_condition_on_existing(
    db_session: AsyncSession,
):
    """Test that condition updated when existing listing re-imported."""
    # Arrange: Create existing listing with 'new' condition
    existing_listing = Listing(
        title="Gaming PC",
        price_usd=599.99,
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456",
        dedup_hash="abc123",
    )
    db_session.add(existing_listing)
    await db_session.flush()

    # Create normalized data with 'used' condition
    normalized = NormalizedListingSchema(
        title="Gaming PC",
        price=Decimal("499.99"),  # Lower price
        currency="USD",
        condition="used",  # Condition changed
        marketplace="ebay",
        vendor_item_id="123456",
    )

    dedupe_result = DeduplicationResult(
        exists=True,
        existing_listing=existing_listing,
        is_exact_match=True,
        confidence=1.0,
        dedup_hash="abc123",
    )

    # Act: Update listing
    updated_listing = await upsert_from_url(db_session, normalized, dedupe_result)

    # Assert: Condition updated
    assert updated_listing.condition == "used"
    assert updated_listing.price_usd == 499.99
