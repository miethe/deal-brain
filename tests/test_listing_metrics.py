"""Tests for listing performance metrics calculation."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Cpu, Listing
from dealbrain_api.services.listings import (
    calculate_cpu_performance_metrics,
    update_listing_metrics,
    bulk_update_listing_metrics,
)


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
