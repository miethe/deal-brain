"""Tests for listing performance metrics calculation."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Cpu, Listing
from dealbrain_api.services.listings import apply_listing_metrics

# Legacy function imports (may not exist - tests will be adjusted)
try:
    from dealbrain_api.services.listings import (
        calculate_cpu_performance_metrics,
        update_listing_metrics,
        bulk_update_listing_metrics,
    )
    LEGACY_FUNCTIONS_AVAILABLE = True
except ImportError:
    LEGACY_FUNCTIONS_AVAILABLE = False


class TestCalculateCpuPerformanceMetrics:
    """Test calculate_cpu_performance_metrics function."""

    def test_calculate_metrics_with_valid_cpu(self):
        """Test metric calculation with valid CPU data."""
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cpu_mark_single=3985,
            cpu_mark_multi=35864,
        )
        listing = Listing(
            title="Test PC",
            price_usd=799.99,
            adjusted_price_usd=649.99,
            condition="used",
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Single-thread metrics
        assert "dollar_per_cpu_mark_single" in metrics
        assert "dollar_per_cpu_mark_single_adjusted" in metrics
        assert metrics["dollar_per_cpu_mark_single"] == pytest.approx(0.200, rel=0.01)
        assert metrics["dollar_per_cpu_mark_single_adjusted"] == pytest.approx(
            0.163, rel=0.01
        )

        # Multi-thread metrics
        assert "dollar_per_cpu_mark_multi" in metrics
        assert "dollar_per_cpu_mark_multi_adjusted" in metrics
        assert metrics["dollar_per_cpu_mark_multi"] == pytest.approx(0.0223, rel=0.01)
        assert metrics["dollar_per_cpu_mark_multi_adjusted"] == pytest.approx(
            0.0181, rel=0.01
        )

    def test_calculate_metrics_no_cpu(self):
        """Test graceful handling when CPU not assigned."""
        listing = Listing(title="Test", price_usd=500, condition="used")
        metrics = calculate_cpu_performance_metrics(listing)
        assert metrics == {}

    def test_calculate_metrics_missing_single_thread(self):
        """Test handling when single-thread benchmark missing."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=None,  # Missing
            cpu_mark_multi=30000,
        )
        listing = Listing(title="Test", price_usd=800, condition="used")
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should only have multi-thread metrics
        assert "dollar_per_cpu_mark_single" not in metrics
        assert "dollar_per_cpu_mark_single_adjusted" not in metrics
        assert "dollar_per_cpu_mark_multi" in metrics
        assert "dollar_per_cpu_mark_multi_adjusted" in metrics

    def test_calculate_metrics_zero_cpu_mark(self):
        """Test handling when CPU mark is zero (invalid data)."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=0,  # Zero (invalid)
            cpu_mark_multi=30000,
        )
        listing = Listing(title="Test", price_usd=800, condition="used")
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should skip zero values
        assert "dollar_per_cpu_mark_single" not in metrics
        assert "dollar_per_cpu_mark_single_adjusted" not in metrics
        assert "dollar_per_cpu_mark_multi" in metrics

    def test_calculate_metrics_no_adjusted_price(self):
        """Test metrics when adjusted_price_usd is None."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        listing = Listing(
            title="Test",
            price_usd=800,
            adjusted_price_usd=None,  # No adjusted price
            condition="new",
        )
        listing.cpu = cpu

        metrics = calculate_cpu_performance_metrics(listing)

        # Should use base price for both raw and adjusted
        assert metrics["dollar_per_cpu_mark_single"] == 0.2  # 800 / 4000
        assert metrics["dollar_per_cpu_mark_single_adjusted"] == 0.2  # Same
        assert metrics["dollar_per_cpu_mark_multi"] == pytest.approx(0.0267, rel=0.01)
        assert metrics["dollar_per_cpu_mark_multi_adjusted"] == pytest.approx(
            0.0267, rel=0.01
        )


@pytest.mark.asyncio
class TestUpdateListingMetrics:
    """Test update_listing_metrics function."""

    async def test_update_listing_metrics(self, session: AsyncSession):
        """Test metric persistence."""
        # Create CPU and listing
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test", price_usd=800, condition="used", cpu_id=cpu.id
        )
        session.add(listing)
        await session.commit()

        # Update metrics
        updated = await update_listing_metrics(session, listing.id)

        assert updated.dollar_per_cpu_mark_single == 0.2  # 800 / 4000
        assert updated.dollar_per_cpu_mark_multi == pytest.approx(0.0267, rel=0.01)
        assert updated.dollar_per_cpu_mark_single_adjusted == 0.2
        assert updated.dollar_per_cpu_mark_multi_adjusted == pytest.approx(
            0.0267, rel=0.01
        )

    async def test_update_listing_metrics_not_found(self, session: AsyncSession):
        """Test error handling when listing not found."""
        with pytest.raises(ValueError, match="Listing .* not found"):
            await update_listing_metrics(session, 99999)


@pytest.mark.asyncio
class TestBulkUpdateListingMetrics:
    """Test bulk_update_listing_metrics function."""

    async def test_bulk_update_all_listings(self, session: AsyncSession):
        """Test bulk update for all listings."""
        # Create CPU
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        # Create multiple listings
        listing1 = Listing(
            title="Test 1", price_usd=800, condition="used", cpu_id=cpu.id
        )
        listing2 = Listing(
            title="Test 2", price_usd=600, condition="refurb", cpu_id=cpu.id
        )
        listing3 = Listing(
            title="Test 3", price_usd=1000, condition="new", cpu_id=cpu.id
        )
        session.add_all([listing1, listing2, listing3])
        await session.commit()

        # Bulk update all
        count = await bulk_update_listing_metrics(session, listing_ids=None)

        assert count == 3

    async def test_bulk_update_specific_listings(self, session: AsyncSession):
        """Test bulk update for specific listing IDs."""
        # Create CPU
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        # Create listings
        listing1 = Listing(
            title="Test 1", price_usd=800, condition="used", cpu_id=cpu.id
        )
        listing2 = Listing(
            title="Test 2", price_usd=600, condition="refurb", cpu_id=cpu.id
        )
        listing3 = Listing(
            title="Test 3", price_usd=1000, condition="new", cpu_id=cpu.id
        )
        session.add_all([listing1, listing2, listing3])
        await session.commit()

        # Update only listing1 and listing2
        count = await bulk_update_listing_metrics(
            session, listing_ids=[listing1.id, listing2.id]
        )

        assert count == 2


@pytest.mark.asyncio
class TestApplyListingMetricsCpuMarks:
    """Test apply_listing_metrics function for CPU Mark calculations."""

    async def test_cpu_mark_calculations_with_both_marks(self, session: AsyncSession):
        """Test CPU Mark metrics calculated with both single and multi marks."""
        # Create CPU with both marks
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cpu_mark_single=3985,
            cpu_mark_multi=35864,
        )
        session.add(cpu)
        await session.flush()

        # Create listing with CPU and price
        listing = Listing(
            title="Test PC",
            price_usd=799.99,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        # Apply metrics
        await apply_listing_metrics(session, listing)

        # Verify calculations
        assert listing.dollar_per_cpu_mark_single is not None
        assert listing.dollar_per_cpu_mark_multi is not None
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 3985, rel=0.01
        )
        assert listing.dollar_per_cpu_mark_multi == pytest.approx(
            listing.adjusted_price_usd / 35864, rel=0.01
        )

    async def test_cpu_mark_calculations_single_only(self, session: AsyncSession):
        """Test metrics when only single-thread mark available."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=None,  # No multi-thread mark
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=800.0,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should have single but not multi
        assert listing.dollar_per_cpu_mark_single is not None
        assert listing.dollar_per_cpu_mark_multi is None
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 4000, rel=0.01
        )

    async def test_cpu_mark_calculations_multi_only(self, session: AsyncSession):
        """Test metrics when only multi-thread mark available."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=None,  # No single-thread mark
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=600.0,
            condition="refurb",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should have multi but not single
        assert listing.dollar_per_cpu_mark_single is None
        assert listing.dollar_per_cpu_mark_multi is not None
        assert listing.dollar_per_cpu_mark_multi == pytest.approx(
            listing.adjusted_price_usd / 30000, rel=0.01
        )

    async def test_cpu_mark_calculations_no_cpu(self, session: AsyncSession):
        """Test metrics when no CPU assigned."""
        listing = Listing(
            title="Test",
            price_usd=500.0,
            condition="used",
            cpu_id=None,  # No CPU
        )
        session.add(listing)
        await session.flush()

        await apply_listing_metrics(session, listing)

        # Should be None
        assert listing.dollar_per_cpu_mark_single is None
        assert listing.dollar_per_cpu_mark_multi is None

    async def test_cpu_mark_recalculation_on_price_update(self, session: AsyncSession):
        """Test metrics recalculate when price changes."""
        cpu = Cpu(
            name="Test CPU",
            manufacturer="Test",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=800.0,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.flush()

        # Initial calculation
        await apply_listing_metrics(session, listing)
        initial_single = listing.dollar_per_cpu_mark_single
        initial_multi = listing.dollar_per_cpu_mark_multi

        # Update price
        listing.price_usd = 600.0

        # Recalculate
        await apply_listing_metrics(session, listing)

        # Metrics should have changed
        assert listing.dollar_per_cpu_mark_single != initial_single
        assert listing.dollar_per_cpu_mark_multi != initial_multi
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 4000, rel=0.01
        )

    async def test_cpu_mark_recalculation_on_cpu_change(self, session: AsyncSession):
        """Test metrics recalculate when CPU changes."""
        cpu1 = Cpu(
            name="CPU 1",
            manufacturer="Intel",
            cpu_mark_single=4000,
            cpu_mark_multi=30000,
        )
        cpu2 = Cpu(
            name="CPU 2",
            manufacturer="AMD",
            cpu_mark_single=5000,
            cpu_mark_multi=40000,
        )
        session.add_all([cpu1, cpu2])
        await session.flush()

        listing = Listing(
            title="Test",
            price_usd=800.0,
            condition="used",
            cpu_id=cpu1.id,
        )
        session.add(listing)
        await session.flush()

        # Initial calculation with CPU1
        await apply_listing_metrics(session, listing)
        initial_single = listing.dollar_per_cpu_mark_single
        initial_multi = listing.dollar_per_cpu_mark_multi

        # Change to CPU2
        listing.cpu_id = cpu2.id

        # Recalculate
        await apply_listing_metrics(session, listing)

        # Metrics should have changed
        assert listing.dollar_per_cpu_mark_single != initial_single
        assert listing.dollar_per_cpu_mark_multi != initial_multi
        assert listing.dollar_per_cpu_mark_single == pytest.approx(
            listing.adjusted_price_usd / 5000, rel=0.01
        )
        assert listing.dollar_per_cpu_mark_multi == pytest.approx(
            listing.adjusted_price_usd / 40000, rel=0.01
        )
