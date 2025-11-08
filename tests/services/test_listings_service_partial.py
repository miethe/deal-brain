"""Tests for ListingsService partial import support.

This test suite verifies that the ListingsService can create listings without prices
(partial imports) and skip metrics calculation appropriately.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.db import Base, get_engine, get_session_factory
from dealbrain_api.models.core import Listing, Cpu, ValuationRuleset, ValuationRuleGroup
from dealbrain_api.services.listings import (
    create_from_ingestion,
    apply_listing_metrics,
    partial_update_listing,
    bulk_update_listings,
    calculate_cpu_performance_metrics,
)
from dealbrain_core.schemas.ingestion import NormalizedListingSchema


# --- Fixtures ---


@pytest_asyncio.fixture(scope="function")
async def async_session():
    """Create async database session for tests."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def sample_cpu(async_session: AsyncSession) -> Cpu:
    """Create a sample CPU for testing."""
    cpu = Cpu(
        name="Intel Core i5-12400",
        manufacturer="Intel",
        cores=6,
        threads=12,
        tdp_w=65,
        cpu_mark_multi=20000,
        cpu_mark_single=3500,
    )
    async_session.add(cpu)
    await async_session.commit()
    await async_session.refresh(cpu)
    return cpu


@pytest.fixture
def partial_normalized_data() -> NormalizedListingSchema:
    """Create normalized data WITHOUT price (partial import)."""
    return NormalizedListingSchema(
        title="Dell OptiPlex 7090 SFF",
        price=None,  # Missing price
        currency="USD",
        condition="used",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="test_seller",
        cpu_model="Intel Core i5-12400",
        ram_gb=16,
        storage_gb=512,
        quality="partial",
        extraction_metadata={
            "title": "extracted",
            "cpu_model": "extracted",
            "ram_gb": "extracted",
            "storage_gb": "extracted",
            "price": "extraction_failed",
        },
        missing_fields=["price"],
    )


@pytest.fixture
def complete_normalized_data() -> NormalizedListingSchema:
    """Create normalized data WITH price (complete import)."""
    return NormalizedListingSchema(
        title="Dell OptiPlex 7090 SFF",
        price=Decimal("599.99"),
        currency="USD",
        condition="used",
        marketplace="ebay",
        vendor_item_id="123456789012",
        seller="test_seller",
        cpu_model="Intel Core i5-12400",
        ram_gb=16,
        storage_gb=512,
        quality="full",
        extraction_metadata={
            "title": "extracted",
            "price": "extracted",
            "cpu_model": "extracted",
            "ram_gb": "extracted",
            "storage_gb": "extracted",
        },
        missing_fields=[],
    )


# --- Tests ---


class TestCreateFromIngestionPartial:
    """Test create_from_ingestion with partial imports (no price)."""

    @pytest.mark.asyncio
    async def test_create_partial_listing_no_price(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Create listing without price - should skip metrics calculation."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # Verify listing created
        assert listing.id is not None
        assert listing.title == "Dell OptiPlex 7090 SFF"
        assert listing.price_usd is None

        # Verify quality tracking
        assert listing.quality == "partial"
        assert listing.missing_fields == ["price"]

        # Verify extraction metadata stored
        assert listing.extraction_metadata is not None
        assert listing.extraction_metadata["title"] == "extracted"
        assert listing.extraction_metadata["price"] == "extraction_failed"

        # Verify metrics NOT calculated (no price)
        assert listing.valuation_breakdown is None
        assert listing.adjusted_price_usd is None
        assert listing.score_composite is None
        assert listing.dollar_per_cpu_mark is None

    @pytest.mark.asyncio
    async def test_create_partial_listing_quality_tracking(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Verify quality, extraction_metadata, missing_fields stored correctly."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # Quality indicator
        assert listing.quality == "partial"

        # Missing fields tracking
        assert "price" in listing.missing_fields

        # Extraction metadata
        assert listing.extraction_metadata["price"] == "extraction_failed"
        assert listing.extraction_metadata["title"] == "extracted"

        # Component data stored
        assert listing.ram_gb == 16
        assert listing.primary_storage_gb == 512
        assert listing.attributes_json is not None
        assert "cpu_model_raw" in listing.attributes_json
        assert listing.attributes_json["cpu_model_raw"] == "Intel Core i5-12400"

    @pytest.mark.asyncio
    async def test_partial_listing_no_valuation_breakdown(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Verify valuation_breakdown is None for partial imports."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        assert listing.valuation_breakdown is None
        assert listing.adjusted_price_usd is None

    @pytest.mark.asyncio
    async def test_partial_listing_skips_metrics(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Verify all metric fields are None for partial imports."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # All CPU metrics should be None
        assert listing.dollar_per_cpu_mark is None
        assert listing.dollar_per_single_mark is None
        assert listing.score_cpu_multi is None
        assert listing.score_cpu_single is None
        assert listing.score_composite is None

        # Performance metrics should be None
        assert not hasattr(listing, "dollar_per_cpu_mark_single") or listing.dollar_per_cpu_mark_single is None
        assert not hasattr(listing, "dollar_per_cpu_mark_multi") or listing.dollar_per_cpu_mark_multi is None


class TestCreateFromIngestionComplete:
    """Test create_from_ingestion with complete imports (with price)."""

    @pytest.mark.asyncio
    async def test_create_full_listing_still_works(
        self, async_session: AsyncSession, complete_normalized_data: NormalizedListingSchema
    ):
        """Ensure complete imports with price still work and calculate metrics."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=complete_normalized_data,
        )

        # Verify listing created
        assert listing.id is not None
        assert listing.title == "Dell OptiPlex 7090 SFF"
        assert listing.price_usd == 599.99

        # Verify quality tracking
        assert listing.quality == "full"
        assert listing.missing_fields == []

        # Verify metrics calculated (price exists)
        assert listing.valuation_breakdown is not None
        assert listing.adjusted_price_usd is not None
        assert listing.adjusted_price_usd > 0

    @pytest.mark.asyncio
    async def test_create_full_listing_with_cpu_metrics(
        self, async_session: AsyncSession, complete_normalized_data: NormalizedListingSchema, sample_cpu: Cpu
    ):
        """Verify metrics calculated when CPU assigned and price exists."""
        # Assign CPU to listing
        complete_normalized_data.cpu_model = sample_cpu.name

        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=complete_normalized_data,
        )

        # Manually assign CPU (in real system, this would be done by enrichment)
        listing.cpu_id = sample_cpu.id
        await async_session.commit()
        await async_session.refresh(listing)

        # Recalculate metrics
        await apply_listing_metrics(async_session, listing)
        await async_session.commit()
        await async_session.refresh(listing)

        # Verify CPU metrics calculated
        assert listing.score_cpu_multi is not None
        assert listing.score_cpu_single is not None
        assert listing.dollar_per_cpu_mark is not None


class TestApplyListingMetricsNullSafety:
    """Test apply_listing_metrics handles None prices correctly."""

    @pytest.mark.asyncio
    async def test_apply_metrics_requires_price(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Verify apply_listing_metrics raises ValueError when price is None."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # Try to apply metrics to listing without price
        with pytest.raises(ValueError, match="price_usd=None"):
            await apply_listing_metrics(async_session, listing)


class TestPartialUpdateListingNullSafety:
    """Test partial_update_listing handles None prices correctly."""

    @pytest.mark.asyncio
    async def test_partial_update_skips_metrics_when_no_price(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Verify partial_update_listing skips metrics when price is None."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # Update some field
        updated = await partial_update_listing(
            session=async_session,
            listing=listing,
            fields={"title": "Updated Title"},
            run_metrics=True,  # Request metrics but should skip due to no price
        )

        # Verify update succeeded
        assert updated.title == "Updated Title"

        # Verify metrics still None (skipped)
        assert updated.valuation_breakdown is None
        assert updated.adjusted_price_usd is None

    @pytest.mark.asyncio
    async def test_partial_update_calculates_metrics_when_price_added(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Verify metrics calculated when price added via partial_update."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # Add price
        updated = await partial_update_listing(
            session=async_session,
            listing=listing,
            fields={"price_usd": 599.99, "quality": "full"},
            run_metrics=True,
        )

        # Verify metrics calculated
        assert updated.price_usd == 599.99
        assert updated.quality == "full"
        assert updated.valuation_breakdown is not None
        assert updated.adjusted_price_usd is not None


class TestBulkUpdateListingsNullSafety:
    """Test bulk_update_listings handles None prices correctly."""

    @pytest.mark.asyncio
    async def test_bulk_update_skips_metrics_for_listings_without_price(
        self,
        async_session: AsyncSession,
        partial_normalized_data: NormalizedListingSchema,
        complete_normalized_data: NormalizedListingSchema,
    ):
        """Verify bulk update skips metrics for partial listings but calculates for complete."""
        # Create one partial and one complete listing
        partial_listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        complete_listing = await create_from_ingestion(
            session=async_session,
            normalized_data=complete_normalized_data,
        )

        await async_session.commit()

        # Bulk update both
        updated_listings = await bulk_update_listings(
            session=async_session,
            listing_ids=[partial_listing.id, complete_listing.id],
            fields={"notes": "Bulk updated"},
        )

        await async_session.commit()

        # Verify both updated
        assert len(updated_listings) == 2

        # Find each listing
        partial = next((l for l in updated_listings if l.id == partial_listing.id), None)
        complete = next((l for l in updated_listings if l.id == complete_listing.id), None)

        assert partial is not None
        assert complete is not None

        # Verify partial still has no metrics
        assert partial.valuation_breakdown is None

        # Verify complete has metrics
        assert complete.valuation_breakdown is not None


class TestCalculateCpuPerformanceMetricsNullSafety:
    """Test calculate_cpu_performance_metrics handles None prices correctly."""

    @pytest.mark.asyncio
    async def test_calculate_metrics_returns_empty_when_no_price(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema, sample_cpu: Cpu
    ):
        """Verify calculate_cpu_performance_metrics returns empty dict when price is None."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        # Assign CPU
        listing.cpu_id = sample_cpu.id
        listing.cpu = sample_cpu
        await async_session.commit()
        await async_session.refresh(listing)

        # Try to calculate metrics
        metrics = calculate_cpu_performance_metrics(listing)

        # Should return empty dict (no price)
        assert metrics == {}

    @pytest.mark.asyncio
    async def test_calculate_metrics_works_when_price_exists(
        self, async_session: AsyncSession, complete_normalized_data: NormalizedListingSchema, sample_cpu: Cpu
    ):
        """Verify calculate_cpu_performance_metrics works when price exists."""
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=complete_normalized_data,
        )

        # Assign CPU
        listing.cpu_id = sample_cpu.id
        listing.cpu = sample_cpu
        # Set valuation breakdown for adjustment calculation
        listing.valuation_breakdown = {
            "total_adjustment": -50.0,
        }
        await async_session.commit()
        await async_session.refresh(listing)

        # Calculate metrics
        metrics = calculate_cpu_performance_metrics(listing)

        # Should have metrics
        assert "dollar_per_cpu_mark_single" in metrics
        assert "dollar_per_cpu_mark_multi" in metrics
        assert metrics["dollar_per_cpu_mark_single"] > 0
        assert metrics["dollar_per_cpu_mark_multi"] > 0


class TestIntegrationEndToEnd:
    """Integration tests for partial import end-to-end flow."""

    @pytest.mark.asyncio
    async def test_partial_import_to_completion_workflow(
        self, async_session: AsyncSession, partial_normalized_data: NormalizedListingSchema
    ):
        """Test complete workflow: partial import -> manual completion -> metrics calculation."""
        # Step 1: Create partial listing
        listing = await create_from_ingestion(
            session=async_session,
            normalized_data=partial_normalized_data,
        )

        assert listing.quality == "partial"
        assert listing.price_usd is None
        assert listing.valuation_breakdown is None

        # Step 2: User manually adds price
        updated = await partial_update_listing(
            session=async_session,
            listing=listing,
            fields={"price_usd": 599.99, "quality": "full", "missing_fields": []},
            run_metrics=True,
        )

        # Step 3: Verify metrics now calculated
        await async_session.commit()
        await async_session.refresh(updated)

        assert updated.quality == "full"
        assert updated.price_usd == 599.99
        assert updated.valuation_breakdown is not None
        assert updated.adjusted_price_usd is not None
        assert updated.missing_fields == []
