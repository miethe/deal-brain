"""CPU analytics service for price targets and performance value calculations."""

from __future__ import annotations

import logging
from datetime import datetime
from statistics import mean, stdev
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import Cpu, Listing
from dealbrain_core.enums import ListingStatus
from dealbrain_core.schemas.cpu import PerformanceValue, PriceTarget

logger = logging.getLogger(__name__)


class CPUAnalyticsService:
    """Service for CPU performance analytics and pricing calculations.

    This service provides methods to:
    1. Calculate price targets from listing adjusted prices
    2. Calculate performance value metrics ($/PassMark)
    3. Update CPU analytics fields in the database
    4. Recalculate metrics for all CPUs
    """

    @staticmethod
    async def calculate_price_targets(
        session: AsyncSession,
        cpu_id: int
    ) -> PriceTarget:
        """Calculate price targets from listing adjusted prices.

        Algorithm:
        1. Fetch all active listings with this CPU and non-null adjusted_price_usd
        2. Extract adjusted_price_usd values
        3. Calculate mean and standard deviation
        4. Set targets: good=mean, great=mean-stddev, fair=mean+stddev
        5. Determine confidence based on sample size

        Args:
            session: Async database session
            cpu_id: CPU ID to calculate price targets for

        Returns:
            PriceTarget with good/great/fair prices and confidence level
        """
        try:
            # Query active listings with this CPU and valid adjusted prices
            stmt = select(Listing.adjusted_price_usd).where(
                and_(
                    Listing.cpu_id == cpu_id,
                    Listing.status == ListingStatus.ACTIVE.value,
                    Listing.adjusted_price_usd.isnot(None),
                    Listing.adjusted_price_usd > 0
                )
            )
            result = await session.execute(stmt)
            prices = [row[0] for row in result.all()]

            sample_size = len(prices)
            logger.info(f"CPU {cpu_id}: Found {sample_size} active listings with prices")

            # Insufficient data
            if sample_size < 2:
                return PriceTarget(
                    good=None,
                    great=None,
                    fair=None,
                    sample_size=sample_size,
                    confidence='insufficient',
                    stddev=None,
                    updated_at=datetime.utcnow()
                )

            # Calculate statistics
            avg_price = mean(prices)
            price_stddev = stdev(prices) if sample_size > 1 else 0.0

            # Calculate targets
            good_price = avg_price
            great_price = max(avg_price - price_stddev, 0.0)
            fair_price = avg_price + price_stddev

            # Determine confidence level
            if sample_size >= 10:
                confidence = 'high'
            elif sample_size >= 5:
                confidence = 'medium'
            else:
                confidence = 'low'

            logger.info(
                f"CPU {cpu_id}: Calculated price targets - "
                f"good=${good_price:.2f}, great=${great_price:.2f}, fair=${fair_price:.2f}, "
                f"confidence={confidence}"
            )

            return PriceTarget(
                good=round(good_price, 2),
                great=round(great_price, 2),
                fair=round(fair_price, 2),
                sample_size=sample_size,
                confidence=confidence,
                stddev=round(price_stddev, 2),
                updated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error calculating price targets for CPU {cpu_id}: {e}", exc_info=True)
            return PriceTarget(
                good=None,
                great=None,
                fair=None,
                sample_size=0,
                confidence='insufficient',
                stddev=None,
                updated_at=datetime.utcnow()
            )

    @staticmethod
    async def calculate_performance_value(
        session: AsyncSession,
        cpu_id: int
    ) -> PerformanceValue:
        """Calculate $/PassMark metrics and percentile ranking.

        Algorithm:
        1. Get CPU benchmark scores (cpu_mark_single, cpu_mark_multi)
        2. Calculate average listing adjusted price
        3. Compute $/mark ratios (price / benchmark_score)
        4. Calculate percentile rank across all CPUs (lower is better)
        5. Assign rating based on quartiles

        Args:
            session: Async database session
            cpu_id: CPU ID to calculate performance value for

        Returns:
            PerformanceValue with $/mark metrics and rating
        """
        try:
            # Fetch CPU with benchmark scores
            cpu = await session.get(Cpu, cpu_id)
            if not cpu:
                logger.error(f"CPU {cpu_id} not found")
                return PerformanceValue(
                    dollar_per_mark_single=None,
                    dollar_per_mark_multi=None,
                    percentile=None,
                    rating=None,
                    updated_at=datetime.utcnow()
                )

            # Check if benchmark scores exist
            if not cpu.cpu_mark_single or not cpu.cpu_mark_multi:
                logger.warning(
                    f"CPU {cpu_id} ({cpu.name}): Missing benchmark scores "
                    f"(single={cpu.cpu_mark_single}, multi={cpu.cpu_mark_multi})"
                )
                return PerformanceValue(
                    dollar_per_mark_single=None,
                    dollar_per_mark_multi=None,
                    percentile=None,
                    rating=None,
                    updated_at=datetime.utcnow()
                )

            # Calculate average adjusted price from active listings
            stmt = select(func.avg(Listing.adjusted_price_usd)).where(
                and_(
                    Listing.cpu_id == cpu_id,
                    Listing.status == ListingStatus.ACTIVE.value,
                    Listing.adjusted_price_usd.isnot(None),
                    Listing.adjusted_price_usd > 0
                )
            )
            result = await session.execute(stmt)
            avg_price = result.scalar()

            if not avg_price:
                logger.warning(f"CPU {cpu_id} ({cpu.name}): No active listings with prices")
                return PerformanceValue(
                    dollar_per_mark_single=None,
                    dollar_per_mark_multi=None,
                    percentile=None,
                    rating=None,
                    updated_at=datetime.utcnow()
                )

            # Calculate $/mark ratios
            dollar_per_single = avg_price / cpu.cpu_mark_single
            dollar_per_multi = avg_price / cpu.cpu_mark_multi

            # Calculate percentile rank (lower $/mark = better value = lower percentile)
            # Count CPUs with better (lower) $/mark ratio
            better_count_stmt = select(func.count(Cpu.id)).where(
                and_(
                    Cpu.cpu_mark_multi.isnot(None),
                    Cpu.cpu_mark_multi > 0
                )
            ).select_from(Cpu).join(
                Listing,
                and_(
                    Listing.cpu_id == Cpu.id,
                    Listing.status == ListingStatus.ACTIVE.value,
                    Listing.adjusted_price_usd.isnot(None),
                    Listing.adjusted_price_usd > 0
                )
            ).group_by(Cpu.id).having(
                # Better = lower $/mark ratio
                (func.avg(Listing.adjusted_price_usd) / Cpu.cpu_mark_multi) < dollar_per_multi
            )

            # Count total CPUs with valid data
            total_count_stmt = select(func.count(func.distinct(Cpu.id))).select_from(Cpu).join(
                Listing,
                and_(
                    Listing.cpu_id == Cpu.id,
                    Listing.status == ListingStatus.ACTIVE.value,
                    Listing.adjusted_price_usd.isnot(None),
                    Listing.adjusted_price_usd > 0
                )
            ).where(
                and_(
                    Cpu.cpu_mark_multi.isnot(None),
                    Cpu.cpu_mark_multi > 0
                )
            )

            better_result = await session.execute(better_count_stmt)
            better_count = len(better_result.all())

            total_result = await session.execute(total_count_stmt)
            total_count = total_result.scalar() or 1

            # Calculate percentile (0 = best, 100 = worst)
            percentile = (better_count / total_count) * 100 if total_count > 0 else 50.0

            # Assign rating based on quartiles
            if percentile <= 25:
                rating = 'excellent'
            elif percentile <= 50:
                rating = 'good'
            elif percentile <= 75:
                rating = 'fair'
            else:
                rating = 'poor'

            logger.info(
                f"CPU {cpu_id} ({cpu.name}): Performance value calculated - "
                f"$/single=${dollar_per_single:.4f}, $/multi=${dollar_per_multi:.4f}, "
                f"percentile={percentile:.1f}%, rating={rating}"
            )

            return PerformanceValue(
                dollar_per_mark_single=round(dollar_per_single, 4),
                dollar_per_mark_multi=round(dollar_per_multi, 4),
                percentile=round(percentile, 1),
                rating=rating,
                updated_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error calculating performance value for CPU {cpu_id}: {e}", exc_info=True)
            return PerformanceValue(
                dollar_per_mark_single=None,
                dollar_per_mark_multi=None,
                percentile=None,
                rating=None,
                updated_at=datetime.utcnow()
            )

    @staticmethod
    async def update_cpu_analytics(
        session: AsyncSession,
        cpu_id: int
    ) -> None:
        """Update all analytics fields for a CPU.

        Calculates both price targets and performance value,
        then persists to database.

        Args:
            session: Async database session
            cpu_id: CPU ID to update analytics for
        """
        try:
            logger.info(f"Updating analytics for CPU {cpu_id}")

            # Fetch CPU
            cpu = await session.get(Cpu, cpu_id)
            if not cpu:
                logger.error(f"CPU {cpu_id} not found")
                return

            # Calculate price targets
            price_targets = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)

            # Update CPU price target fields
            cpu.price_target_good = price_targets.good
            cpu.price_target_great = price_targets.great
            cpu.price_target_fair = price_targets.fair
            cpu.price_target_sample_size = price_targets.sample_size
            cpu.price_target_confidence = price_targets.confidence
            cpu.price_target_stddev = price_targets.stddev
            cpu.price_target_updated_at = price_targets.updated_at

            # Calculate performance value
            perf_value = await CPUAnalyticsService.calculate_performance_value(session, cpu_id)

            # Update CPU performance value fields
            cpu.dollar_per_mark_single = perf_value.dollar_per_mark_single
            cpu.dollar_per_mark_multi = perf_value.dollar_per_mark_multi
            cpu.performance_value_percentile = perf_value.percentile
            cpu.performance_value_rating = perf_value.rating
            cpu.performance_metrics_updated_at = perf_value.updated_at

            # Flush to persist changes
            await session.flush()

            logger.info(
                f"CPU {cpu_id} ({cpu.name}): Analytics updated successfully - "
                f"price_target_confidence={cpu.price_target_confidence}, "
                f"performance_rating={cpu.performance_value_rating}"
            )

        except Exception as e:
            logger.error(f"Error updating analytics for CPU {cpu_id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def recalculate_all_cpu_metrics(
        session: AsyncSession
    ) -> dict[str, int]:
        """Background task to refresh all CPU analytics.

        Iterates through all CPUs and recalculates their analytics.
        Continues processing even if individual CPUs fail.

        Args:
            session: Async database session

        Returns:
            Summary dict with total, success, and error counts
        """
        logger.info("Starting recalculation of all CPU metrics")

        # Query all CPU IDs
        stmt = select(Cpu.id)
        result = await session.execute(stmt)
        cpu_ids = [row[0] for row in result.all()]

        total = len(cpu_ids)
        success = 0
        errors = 0

        logger.info(f"Found {total} CPUs to process")

        for cpu_id in cpu_ids:
            try:
                await CPUAnalyticsService.update_cpu_analytics(session, cpu_id)
                success += 1

                if success % 10 == 0:
                    logger.info(f"Progress: {success}/{total} CPUs processed")

            except Exception as e:
                logger.error(f"Failed to update CPU {cpu_id}: {e}", exc_info=True)
                errors += 1

        # Commit all changes
        await session.commit()

        summary = {
            'total': total,
            'success': success,
            'errors': errors
        }

        logger.info(
            f"CPU metrics recalculation complete: "
            f"{success} succeeded, {errors} failed out of {total} total"
        )

        return summary


__all__ = ["CPUAnalyticsService"]
