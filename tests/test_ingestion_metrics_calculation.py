"""Test that URL ingestion calculates performance metrics."""

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
from dealbrain_api.services.ingestion import IngestionService
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


@pytest.mark.asyncio
async def test_url_ingestion_calculates_metrics_on_create(
    db_session: AsyncSession, sample_cpu: Cpu
):
    """Test that URL ingestion calculates performance metrics when creating a new listing."""
    service = IngestionService(db_session)

    # Mock the adapter to return normalized data
    mock_normalized = NormalizedListingSchema(
        title="Gaming PC Intel i9-12900H",
        price=Decimal("999.99"),
        condition="new",
        marketplace="ebay",
        vendor_item_id="TEST123",
        seller="TestSeller",
        cpu_model="Intel Core i9-12900H",
        ram_gb=32,
        storage_gb=1000,
    )

    with patch.object(service.router, "extract", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = (mock_normalized, "ebay_api")

        # Execute ingestion
        result = await service.ingest_single_url("https://ebay.com/itm/TEST123")

        # Verify success
        assert result.success is True
        assert result.status == "created"
        assert result.listing_id is not None

        # Verify metrics were calculated
        listing = await db_session.get(Listing, result.listing_id)
        assert listing is not None
        assert listing.cpu_id == sample_cpu.id

        # Check that adjusted_price_usd was calculated
        assert listing.adjusted_price_usd is not None
        assert listing.adjusted_price_usd > 0

        # Check that performance metrics were calculated
        assert listing.dollar_per_cpu_mark_single is not None
        assert listing.dollar_per_cpu_mark_multi is not None

        # Verify the calculation is correct
        expected_single = listing.adjusted_price_usd / sample_cpu.cpu_mark_single
        expected_multi = listing.adjusted_price_usd / sample_cpu.cpu_mark_multi

        assert abs(listing.dollar_per_cpu_mark_single - expected_single) < 0.0001
        assert abs(listing.dollar_per_cpu_mark_multi - expected_multi) < 0.0001


@pytest.mark.asyncio
async def test_url_ingestion_calculates_metrics_on_update(
    db_session: AsyncSession, sample_cpu: Cpu
):
    """Test that URL ingestion recalculates metrics when updating an existing listing."""
    service = IngestionService(db_session)

    # Create initial listing
    initial_listing = Listing(
        title="Gaming PC Intel i9-12900H",
        price_usd=899.99,
        condition="new",
        marketplace="ebay",
        vendor_item_id="TEST123",
        cpu_id=sample_cpu.id,
        ram_gb=16,
        primary_storage_gb=512,
    )
    db_session.add(initial_listing)
    await db_session.flush()
    await db_session.commit()

    # Mock the adapter to return updated normalized data (price changed)
    mock_normalized = NormalizedListingSchema(
        title="Gaming PC Intel i9-12900H",
        price=Decimal("799.99"),  # Price dropped
        condition="new",
        marketplace="ebay",
        vendor_item_id="TEST123",
        seller="TestSeller",
        cpu_model="Intel Core i9-12900H",
        ram_gb=32,
        storage_gb=1000,
    )

    with patch.object(service.router, "extract", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = (mock_normalized, "ebay_api")

        # Execute ingestion
        result = await service.ingest_single_url("https://ebay.com/itm/TEST123")

        # Verify update
        assert result.success is True
        assert result.status == "updated"
        assert result.listing_id == initial_listing.id

        # Verify metrics were recalculated with new price
        await db_session.refresh(initial_listing)
        assert initial_listing.price_usd == 799.99
        assert initial_listing.adjusted_price_usd is not None

        # Check that performance metrics were recalculated
        assert initial_listing.dollar_per_cpu_mark_single is not None
        assert initial_listing.dollar_per_cpu_mark_multi is not None

        # Verify metrics reflect new adjusted price
        expected_single = initial_listing.adjusted_price_usd / sample_cpu.cpu_mark_single
        expected_multi = initial_listing.adjusted_price_usd / sample_cpu.cpu_mark_multi

        assert abs(initial_listing.dollar_per_cpu_mark_single - expected_single) < 0.0001
        assert abs(initial_listing.dollar_per_cpu_mark_multi - expected_multi) < 0.0001


@pytest.mark.asyncio
async def test_url_ingestion_skips_metrics_without_cpu(db_session: AsyncSession):
    """Test that URL ingestion skips metrics calculation when no CPU is identified."""
    service = IngestionService(db_session)

    # Mock the adapter to return normalized data WITHOUT CPU
    mock_normalized = NormalizedListingSchema(
        title="Generic PC",
        price=Decimal("299.99"),
        condition="used",
        marketplace="other",
        seller="TestSeller",
        ram_gb=8,
        storage_gb=256,
    )

    with patch.object(service.router, "extract", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = (mock_normalized, "jsonld")

        # Execute ingestion
        result = await service.ingest_single_url("https://example.com/pc")

        # Verify success
        assert result.success is True
        assert result.status == "created"
        assert result.listing_id is not None

        # Verify no CPU was assigned
        listing = await db_session.get(Listing, result.listing_id)
        assert listing is not None
        assert listing.cpu_id is None

        # Metrics should be NULL since no CPU
        assert listing.dollar_per_cpu_mark_single is None
        assert listing.dollar_per_cpu_mark_multi is None
