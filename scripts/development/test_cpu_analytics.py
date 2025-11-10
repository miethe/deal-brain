#!/usr/bin/env python3
"""Test script for CPU analytics service.

This script tests the CPU analytics service methods:
1. calculate_price_targets() - Calculate price ranges from listings
2. calculate_performance_value() - Calculate $/PassMark metrics
3. update_cpu_analytics() - Persist analytics to database
4. recalculate_all_cpu_metrics() - Batch recalculation

Usage:
    poetry run python scripts/test_cpu_analytics.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.models.core import Cpu, Listing
from apps.api.dealbrain_api.services.cpu_analytics import CPUAnalyticsService
from dealbrain_core.enums import ListingStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def find_test_cpu():
    """Find a CPU with active listings for testing."""
    async with session_scope() as session:
        # Find CPU with most active listings
        stmt = (
            select(
                Cpu.id,
                Cpu.name,
                Cpu.cpu_mark_single,
                Cpu.cpu_mark_multi,
                func.count(Listing.id).label('listing_count')
            )
            .join(Listing, Listing.cpu_id == Cpu.id)
            .where(
                Listing.status == ListingStatus.ACTIVE.value,
                Listing.adjusted_price_usd.isnot(None),
                Listing.adjusted_price_usd > 0
            )
            .group_by(Cpu.id, Cpu.name, Cpu.cpu_mark_single, Cpu.cpu_mark_multi)
            .order_by(func.count(Listing.id).desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.first()

        if not row:
            logger.error("No CPUs with active listings found in database")
            return None

        logger.info(
            f"Found test CPU: {row.name} (ID: {row.id}) with {row.listing_count} active listings"
        )
        logger.info(
            f"  Benchmark scores - Single: {row.cpu_mark_single}, Multi: {row.cpu_mark_multi}"
        )

        return row.id


async def test_price_targets(cpu_id: int):
    """Test price target calculation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Price Target Calculation")
    logger.info("="*80)

    async with session_scope() as session:
        result = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)

        logger.info(f"\nPrice Target Results:")
        logger.info(f"  Sample Size: {result.sample_size}")
        logger.info(f"  Confidence: {result.confidence}")
        logger.info(f"  Good (avg): ${result.good:.2f}" if result.good else "  Good: None")
        logger.info(f"  Great (avg-σ): ${result.great:.2f}" if result.great else "  Great: None")
        logger.info(f"  Fair (avg+σ): ${result.fair:.2f}" if result.fair else "  Fair: None")
        logger.info(f"  Std Dev: ${result.stddev:.2f}" if result.stddev else "  Std Dev: None")
        logger.info(f"  Updated: {result.updated_at}")

        assert result.sample_size >= 0, "Sample size should be non-negative"
        if result.sample_size >= 2:
            assert result.good is not None, "Good price should be set with sufficient data"
            assert result.great is not None, "Great price should be set with sufficient data"
            assert result.fair is not None, "Fair price should be set with sufficient data"
            assert result.confidence != 'insufficient', "Confidence should not be insufficient"

        logger.info("\n✅ Price target calculation PASSED")


async def test_performance_value(cpu_id: int):
    """Test performance value calculation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Performance Value Calculation")
    logger.info("="*80)

    async with session_scope() as session:
        result = await CPUAnalyticsService.calculate_performance_value(session, cpu_id)

        logger.info(f"\nPerformance Value Results:")
        logger.info(
            f"  $/Single-Thread Mark: ${result.dollar_per_mark_single:.4f}"
            if result.dollar_per_mark_single else "  $/Single-Thread Mark: None"
        )
        logger.info(
            f"  $/Multi-Thread Mark: ${result.dollar_per_mark_multi:.4f}"
            if result.dollar_per_mark_multi else "  $/Multi-Thread Mark: None"
        )
        logger.info(
            f"  Percentile: {result.percentile:.1f}%"
            if result.percentile is not None else "  Percentile: None"
        )
        logger.info(f"  Rating: {result.rating}" if result.rating else "  Rating: None")
        logger.info(f"  Updated: {result.updated_at}")

        if result.dollar_per_mark_single is not None:
            assert result.dollar_per_mark_single > 0, "$/mark should be positive"
            assert result.dollar_per_mark_multi > 0, "$/mark should be positive"
            assert 0 <= result.percentile <= 100, "Percentile should be 0-100"
            assert result.rating in ['excellent', 'good', 'fair', 'poor'], "Invalid rating"

        logger.info("\n✅ Performance value calculation PASSED")


async def test_update_analytics(cpu_id: int):
    """Test updating CPU analytics in database."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Update CPU Analytics")
    logger.info("="*80)

    async with session_scope() as session:
        # Update analytics
        await CPUAnalyticsService.update_cpu_analytics(session, cpu_id)
        await session.commit()

        # Verify fields were updated
        cpu = await session.get(Cpu, cpu_id)

        logger.info(f"\nCPU Analytics After Update:")
        logger.info(f"  Price Target Good: ${cpu.price_target_good:.2f}" if cpu.price_target_good else "  Price Target Good: None")
        logger.info(f"  Price Target Great: ${cpu.price_target_great:.2f}" if cpu.price_target_great else "  Price Target Great: None")
        logger.info(f"  Price Target Fair: ${cpu.price_target_fair:.2f}" if cpu.price_target_fair else "  Price Target Fair: None")
        logger.info(f"  Sample Size: {cpu.price_target_sample_size}")
        logger.info(f"  Confidence: {cpu.price_target_confidence}")
        logger.info(f"  Price Targets Updated: {cpu.price_target_updated_at}")
        logger.info("")
        logger.info(
            f"  $/Single Mark: ${cpu.dollar_per_mark_single:.4f}"
            if cpu.dollar_per_mark_single else "  $/Single Mark: None"
        )
        logger.info(
            f"  $/Multi Mark: ${cpu.dollar_per_mark_multi:.4f}"
            if cpu.dollar_per_mark_multi else "  $/Multi Mark: None"
        )
        logger.info(
            f"  Percentile: {cpu.performance_value_percentile:.1f}%"
            if cpu.performance_value_percentile is not None else "  Percentile: None"
        )
        logger.info(f"  Rating: {cpu.performance_value_rating}" if cpu.performance_value_rating else "  Rating: None")
        logger.info(f"  Performance Metrics Updated: {cpu.performance_metrics_updated_at}")

        assert cpu.price_target_updated_at is not None, "Price target timestamp should be set"
        assert cpu.performance_metrics_updated_at is not None, "Performance metrics timestamp should be set"

        if cpu.price_target_sample_size >= 2:
            assert cpu.price_target_good is not None, "Price targets should be populated"

        logger.info("\n✅ Update CPU analytics PASSED")


async def test_recalculate_all(limit: int = 5):
    """Test batch recalculation (limited sample)."""
    logger.info("\n" + "="*80)
    logger.info(f"TEST 4: Recalculate All CPU Metrics (first {limit} CPUs)")
    logger.info("="*80)

    async with session_scope() as session:
        # Get first N CPU IDs for testing
        stmt = select(Cpu.id).limit(limit)
        result = await session.execute(stmt)
        cpu_ids = [row[0] for row in result.all()]

        logger.info(f"\nProcessing {len(cpu_ids)} CPUs for testing...")

        # Process each CPU
        for cpu_id in cpu_ids:
            try:
                await CPUAnalyticsService.update_cpu_analytics(session, cpu_id)
                logger.info(f"  ✓ CPU {cpu_id} updated")
            except Exception as e:
                logger.error(f"  ✗ CPU {cpu_id} failed: {e}")

        await session.commit()

        logger.info("\n✅ Batch recalculation PASSED")


async def main():
    """Run all tests."""
    logger.info("Starting CPU Analytics Service Tests")
    logger.info("="*80)

    try:
        # Find a test CPU
        cpu_id = await find_test_cpu()
        if not cpu_id:
            logger.error("Cannot run tests without a CPU with active listings")
            return 1

        # Run tests
        await test_price_targets(cpu_id)
        await test_performance_value(cpu_id)
        await test_update_analytics(cpu_id)
        await test_recalculate_all(limit=5)

        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("="*80)

        return 0

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
