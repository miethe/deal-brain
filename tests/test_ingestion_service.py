"""Tests for IngestionService field persistence and brand/model parsing."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:
    import aiosqlite  # type: ignore  # noqa: F401
except ModuleNotFoundError:
    aiosqlite = None

from dealbrain_api.db import Base
from dealbrain_api.models.core import Cpu, Listing
from dealbrain_api.services.ingestion import IngestionService, ListingNormalizer
from dealbrain_core.schemas.ingestion import NormalizedListingSchema


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated in-memory database session for tests."""
    if aiosqlite is None:
        pytest.skip("aiosqlite is not installed; skipping tests")
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


@pytest_asyncio.fixture
async def sample_cpu(db_session: AsyncSession):
    """Create a sample CPU for testing."""
    cpu = Cpu(
        name="Intel Core i9-12900H",
        manufacturer="Intel",
        cpu_mark_multi=25000,
        cpu_mark_single=3500,
    )
    db_session.add(cpu)
    await db_session.flush()
    await db_session.commit()
    return cpu


@pytest_asyncio.fixture
async def sample_listing(db_session: AsyncSession):
    """Create a sample listing for testing."""
    listing = Listing(
        title="Test Listing",
        price_usd=500.00,
        condition="new",
        marketplace="ebay",
        vendor_item_id="TEST123",
    )
    db_session.add(listing)
    await db_session.flush()
    await db_session.commit()
    return listing


@pytest.mark.asyncio
async def test_create_listing_persists_all_fields(db_session: AsyncSession, sample_cpu: Cpu):
    """Test that _create_listing persists all extracted fields."""
    service = IngestionService(db_session)

    # Create normalized data with all fields
    data = NormalizedListingSchema(
        title="MINISFORUM Venus NAB9 Mini PC",
        price=Decimal("699.99"),
        condition="new",
        marketplace="ebay",
        vendor_item_id="123456",
        seller="seller123",
        images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        description="Great mini PC with powerful specs",
        cpu_model="Intel Core i9-12900H",
        ram_gb=32,
        storage_gb=1000,
        manufacturer="MINISFORUM",
        model_number="Venus NAB9",
    )

    # Create listing
    listing = await service._create_listing(data)
    await db_session.flush()
    await db_session.refresh(listing)

    # Verify all fields persisted
    assert listing.title == "MINISFORUM Venus NAB9 Mini PC"
    assert listing.price_usd == 699.99
    assert listing.condition == "new"
    assert listing.marketplace == "ebay"
    assert listing.vendor_item_id == "123456"
    assert listing.seller == "seller123"
    assert listing.cpu_id == sample_cpu.id  # CPU lookup worked
    assert listing.ram_gb == 32
    assert listing.primary_storage_gb == 1000
    assert listing.notes == "Great mini PC with powerful specs"
    assert listing.manufacturer == "MINISFORUM"
    assert listing.model_number == "Venus NAB9"
    assert "images" in listing.attributes_json
    assert len(listing.attributes_json["images"]) == 2


@pytest.mark.asyncio
async def test_create_listing_handles_missing_fields_gracefully(db_session: AsyncSession):
    """Test that _create_listing handles missing optional fields."""
    service = IngestionService(db_session)

    # Create minimal data (only required fields)
    data = NormalizedListingSchema(
        title="Basic PC",
        price=Decimal("299.99"),
        condition="used",
        marketplace="other",
    )

    # Create listing
    listing = await service._create_listing(data)
    await db_session.flush()
    await db_session.refresh(listing)

    # Verify defaults are applied
    assert listing.title == "Basic PC"
    assert listing.price_usd == 299.99
    assert listing.cpu_id is None  # No CPU provided
    assert listing.ram_gb == 0  # Default to 0
    assert listing.primary_storage_gb == 0  # Default to 0
    assert listing.notes is None  # No description
    assert listing.manufacturer is None  # No brand
    assert listing.model_number is None  # No model
    assert listing.attributes_json == {}  # No images


@pytest.mark.asyncio
async def test_create_listing_cpu_lookup_success(db_session: AsyncSession, sample_cpu: Cpu):
    """Test that CPU lookup works correctly."""
    service = IngestionService(db_session)

    data = NormalizedListingSchema(
        title="PC with Intel CPU",
        price=Decimal("599.99"),
        condition="new",
        marketplace="ebay",
        cpu_model="i9-12900H",  # Partial match
    )

    listing = await service._create_listing(data)
    await db_session.flush()
    await db_session.refresh(listing)

    # CPU should be found via partial match
    assert listing.cpu_id == sample_cpu.id


@pytest.mark.asyncio
async def test_create_listing_cpu_lookup_not_found(db_session: AsyncSession):
    """Test that CPU lookup handles non-existent CPUs gracefully."""
    service = IngestionService(db_session)

    data = NormalizedListingSchema(
        title="PC with Unknown CPU",
        price=Decimal("599.99"),
        condition="new",
        marketplace="ebay",
        cpu_model="AMD Ryzen 99-99999X",  # Does not exist
    )

    listing = await service._create_listing(data)
    await db_session.flush()
    await db_session.refresh(listing)

    # CPU should not be found
    assert listing.cpu_id is None


@pytest.mark.asyncio
async def test_update_listing_preserves_and_updates_fields(
    db_session: AsyncSession, sample_listing: Listing, sample_cpu: Cpu
):
    """Test that _update_listing updates all fields without data loss."""
    service = IngestionService(db_session)

    # Update with new data
    updated_data = NormalizedListingSchema(
        title=sample_listing.title,
        price=Decimal("599.99"),  # Price changed
        condition="used",  # Condition changed
        marketplace=sample_listing.marketplace,
        images=["https://example.com/new-img.jpg"],
        description="Updated description",
        cpu_model="Intel Core i9-12900H",
        ram_gb=64,  # Upgraded RAM
        storage_gb=2000,  # Upgraded storage
        manufacturer="Dell",
        model_number="OptiPlex 7090",
    )

    # Update listing
    updated = await service._update_listing(sample_listing, updated_data)
    await db_session.flush()
    await db_session.refresh(updated)

    # Verify updates
    assert updated.price_usd == 599.99
    assert updated.condition == "used"
    assert updated.cpu_id == sample_cpu.id
    assert updated.ram_gb == 64
    assert updated.primary_storage_gb == 2000
    assert updated.notes == "Updated description"
    assert updated.manufacturer == "Dell"
    assert updated.model_number == "OptiPlex 7090"
    assert "images" in updated.attributes_json
    assert updated.last_seen_at is not None


@pytest.mark.asyncio
async def test_update_listing_partial_updates(db_session: AsyncSession, sample_listing: Listing):
    """Test that _update_listing handles partial updates (not all fields provided)."""
    service = IngestionService(db_session)

    # Set initial values
    sample_listing.ram_gb = 16
    sample_listing.manufacturer = "HP"
    await db_session.flush()

    # Update with partial data (only price and storage)
    partial_data = NormalizedListingSchema(
        title=sample_listing.title,
        price=Decimal("450.00"),
        condition="new",
        marketplace=sample_listing.marketplace,
        storage_gb=512,  # Only update storage
    )

    # Update listing
    updated = await service._update_listing(sample_listing, partial_data)
    await db_session.flush()
    await db_session.refresh(updated)

    # Verify partial update preserved existing values
    assert updated.price_usd == 450.00
    assert updated.primary_storage_gb == 512  # Updated
    assert updated.ram_gb == 16  # Preserved (not in update data)
    assert updated.manufacturer == "HP"  # Preserved (not in update data)


@pytest.mark.asyncio
async def test_parse_brand_and_model_from_title(db_session: AsyncSession):
    """Test brand/model parsing from various title formats."""
    normalizer = ListingNormalizer(db_session)

    test_cases = [
        # Brand at start of title
        ("Dell OptiPlex 7090 Desktop Computer", ("Dell", "OptiPlex 7090")),
        ("HP EliteDesk 800 G6 SFF", ("HP", "EliteDesk 800 G6")),
        ("Lenovo ThinkCentre M920q Tiny", ("Lenovo", "ThinkCentre M920q Tiny")),
        ("ASUS PN64 Mini PC", ("ASUS", "PN64")),
        ("Intel NUC 12 Pro", ("Intel", "NUC 12 Pro")),
        # "by Brand" pattern
        ("Venus NAB9 by MINISFORUM", ("MINISFORUM", "Venus NAB9")),
        # No pattern match
        ("Generic PC no brand", (None, None)),
    ]

    for title, expected in test_cases:
        brand, model = normalizer._parse_brand_and_model(title)
        assert (brand, model) == expected, f"Failed for title: {title} - got ({brand}, {model})"


@pytest.mark.asyncio
async def test_parse_brand_and_model_edge_cases(db_session: AsyncSession):
    """Test brand/model parsing edge cases."""
    normalizer = ListingNormalizer(db_session)

    # Empty title
    brand, model = normalizer._parse_brand_and_model("")
    assert (brand, model) == (None, None)

    # Title with only brand (no model to extract)
    brand, model = normalizer._parse_brand_and_model("Dell")
    # "Dell" alone matches brand pattern but has no remaining text for model
    assert brand is None or model is None

    # Title with complex model numbers
    brand, model = normalizer._parse_brand_and_model("HP EliteDesk 800 G6 Desktop Mini PC")
    assert brand == "HP"
    assert "EliteDesk 800" in model
    # "Desktop" gets stripped by our regex
    assert "Desktop" not in model or model == "EliteDesk 800 G6"


@pytest.mark.asyncio
async def test_normalizer_integrates_brand_model_parsing(db_session: AsyncSession):
    """Test that normalize() integrates brand/model parsing."""
    normalizer = ListingNormalizer(db_session)

    # Create raw data WITHOUT manufacturer/model
    raw_data = NormalizedListingSchema(
        title="Dell OptiPlex 7090 Desktop Computer",
        price=Decimal("599.99"),
        condition="new",
        marketplace="ebay",
        description="Dell PC with i7 CPU",
    )

    # Normalize should parse brand/model from title
    enriched = await normalizer.normalize(raw_data)

    # Verify brand/model were parsed
    assert enriched.manufacturer == "Dell"
    assert enriched.model_number == "OptiPlex 7090"


@pytest.mark.asyncio
async def test_normalizer_preserves_existing_brand_model(db_session: AsyncSession):
    """Test that normalize() preserves existing manufacturer/model if provided."""
    normalizer = ListingNormalizer(db_session)

    # Create raw data WITH manufacturer/model already set
    raw_data = NormalizedListingSchema(
        title="Dell OptiPlex 7090 Desktop Computer",
        price=Decimal("599.99"),
        condition="new",
        marketplace="ebay",
        manufacturer="HP",  # Explicitly set (different from title)
        model_number="EliteDesk 800",  # Explicitly set
    )

    # Normalize should preserve existing values
    enriched = await normalizer.normalize(raw_data)

    # Verify brand/model were NOT overwritten
    assert enriched.manufacturer == "HP"
    assert enriched.model_number == "EliteDesk 800"


@pytest.mark.asyncio
async def test_find_cpu_by_model_exact_match(db_session: AsyncSession, sample_cpu: Cpu):
    """Test CPU lookup with exact match."""
    service = IngestionService(db_session)

    cpu_id = await service._find_cpu_by_model("Intel Core i9-12900H")
    assert cpu_id == sample_cpu.id


@pytest.mark.asyncio
async def test_find_cpu_by_model_partial_match(db_session: AsyncSession, sample_cpu: Cpu):
    """Test CPU lookup with partial match."""
    service = IngestionService(db_session)

    # Try partial matches
    test_cases = ["i9-12900H", "12900H", "i9"]
    for cpu_model in test_cases:
        cpu_id = await service._find_cpu_by_model(cpu_model)
        assert cpu_id == sample_cpu.id, f"Failed to find CPU for: {cpu_model}"


@pytest.mark.asyncio
async def test_find_cpu_by_model_case_insensitive(db_session: AsyncSession, sample_cpu: Cpu):
    """Test CPU lookup is case-insensitive."""
    service = IngestionService(db_session)

    cpu_id = await service._find_cpu_by_model("INTEL CORE I9-12900H")
    assert cpu_id == sample_cpu.id


@pytest.mark.asyncio
async def test_find_cpu_by_model_not_found(db_session: AsyncSession):
    """Test CPU lookup returns None when not found."""
    service = IngestionService(db_session)

    cpu_id = await service._find_cpu_by_model("AMD Ryzen 99-99999X")
    assert cpu_id is None


@pytest.mark.asyncio
async def test_find_cpu_by_model_empty_string(db_session: AsyncSession):
    """Test CPU lookup handles empty string."""
    service = IngestionService(db_session)

    cpu_id = await service._find_cpu_by_model("")
    assert cpu_id is None


@pytest.mark.asyncio
async def test_find_cpu_by_model_none(db_session: AsyncSession):
    """Test CPU lookup handles None."""
    service = IngestionService(db_session)

    cpu_id = await service._find_cpu_by_model(None)
    assert cpu_id is None
