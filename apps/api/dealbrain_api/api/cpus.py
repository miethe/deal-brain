"""CPU API endpoints with analytics integration."""

from __future__ import annotations

import logging
from typing import Sequence

from dealbrain_core.enums import ListingStatus
from dealbrain_core.schemas.cpu import CPUStatistics, CPUWithAnalytics
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..models.core import Cpu, Listing
from ..services.cpu_analytics import CPUAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/cpus", tags=["cpus"])


@router.get("", response_model=list[CPUWithAnalytics])
async def list_cpus(
    session: AsyncSession = Depends(session_dependency),
    include_analytics: bool = Query(
        default=True, description="Include price targets and performance metrics"
    ),
) -> Sequence[CPUWithAnalytics]:
    """List all CPUs with optional analytics data.

    Analytics fields are pre-computed and stored in CPU table,
    so this query is fast even with analytics enabled.

    Returns:
        List of CPUs with embedded analytics (price targets, performance value, listings count)
    """
    try:
        # Query all CPUs ordered by name
        stmt = select(Cpu).order_by(Cpu.name)
        result = await session.execute(stmt)
        cpus = result.scalars().all()

        cpu_with_analytics_list = []

        for cpu in cpus:
            # Count active listings for this CPU
            count_stmt = select(func.count(Listing.id)).where(
                and_(
                    Listing.cpu_id == cpu.id,
                    Listing.status == ListingStatus.ACTIVE.value,
                )
            )
            count_result = await session.execute(count_stmt)
            listings_count = count_result.scalar() or 0

            # Build CPUWithAnalytics response
            cpu_dict = {
                "id": cpu.id,
                "name": cpu.name,
                "manufacturer": cpu.manufacturer,
                "socket": cpu.socket,
                "cores": cpu.cores,
                "threads": cpu.threads,
                "tdp_w": cpu.tdp_w,
                "igpu_model": cpu.igpu_model,
                "cpu_mark_multi": cpu.cpu_mark_multi,
                "cpu_mark_single": cpu.cpu_mark_single,
                "igpu_mark": cpu.igpu_mark,
                "release_year": cpu.release_year,
                "notes": cpu.notes,
                "passmark_slug": cpu.passmark_slug,
                "passmark_category": cpu.passmark_category,
                "passmark_id": cpu.passmark_id,
                "attributes_json": cpu.attributes_json,
                "created_at": cpu.created_at,
                "updated_at": cpu.updated_at,
                "listings_count": listings_count,
            }

            if include_analytics:
                # Add price target fields
                cpu_dict.update({
                    "price_target_good": cpu.price_target_good,
                    "price_target_great": cpu.price_target_great,
                    "price_target_fair": cpu.price_target_fair,
                    "price_target_sample_size": cpu.price_target_sample_size,
                    "price_target_confidence": cpu.price_target_confidence or "insufficient",
                    "price_target_stddev": cpu.price_target_stddev,
                    "price_target_updated_at": cpu.price_target_updated_at,
                    # Add performance value fields
                    "dollar_per_mark_single": cpu.dollar_per_mark_single,
                    "dollar_per_mark_multi": cpu.dollar_per_mark_multi,
                    "performance_value_percentile": cpu.performance_value_percentile,
                    "performance_value_rating": cpu.performance_value_rating,
                    "performance_metrics_updated_at": cpu.performance_metrics_updated_at,
                })
            else:
                # Set default values when analytics not included
                cpu_dict.update({
                    "price_target_good": None,
                    "price_target_great": None,
                    "price_target_fair": None,
                    "price_target_sample_size": 0,
                    "price_target_confidence": "insufficient",
                    "price_target_stddev": None,
                    "price_target_updated_at": None,
                    "dollar_per_mark_single": None,
                    "dollar_per_mark_multi": None,
                    "performance_value_percentile": None,
                    "performance_value_rating": None,
                    "performance_metrics_updated_at": None,
                })

            cpu_with_analytics_list.append(CPUWithAnalytics(**cpu_dict))

        logger.info(f"Listed {len(cpu_with_analytics_list)} CPUs with analytics={include_analytics}")
        return cpu_with_analytics_list

    except Exception as e:
        logger.error(f"Error listing CPUs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing CPUs: {str(e)}",
        )


@router.get("/{cpu_id}", response_model=dict)
async def get_cpu_detail(
    cpu_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    """Get detailed CPU information with analytics and market data.

    Includes:
    - Full CPU specifications
    - Price targets and performance metrics
    - Top 10 associated listings by adjusted price
    - Price distribution for histogram

    Raises:
        HTTPException(404): CPU not found
    """
    try:
        # Fetch CPU by ID
        cpu = await session.get(Cpu, cpu_id)
        if not cpu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CPU with id {cpu_id} not found",
            )

        # Count active listings
        count_stmt = select(func.count(Listing.id)).where(
            and_(
                Listing.cpu_id == cpu.id,
                Listing.status == ListingStatus.ACTIVE.value,
            )
        )
        count_result = await session.execute(count_stmt)
        listings_count = count_result.scalar() or 0

        # Build base CPU data
        cpu_data = {
            "id": cpu.id,
            "name": cpu.name,
            "manufacturer": cpu.manufacturer,
            "socket": cpu.socket,
            "cores": cpu.cores,
            "threads": cpu.threads,
            "tdp_w": cpu.tdp_w,
            "igpu_model": cpu.igpu_model,
            "cpu_mark_multi": cpu.cpu_mark_multi,
            "cpu_mark_single": cpu.cpu_mark_single,
            "igpu_mark": cpu.igpu_mark,
            "release_year": cpu.release_year,
            "notes": cpu.notes,
            "passmark_slug": cpu.passmark_slug,
            "passmark_category": cpu.passmark_category,
            "passmark_id": cpu.passmark_id,
            "attributes_json": cpu.attributes_json,
            "created_at": cpu.created_at,
            "updated_at": cpu.updated_at,
            "price_target_good": cpu.price_target_good,
            "price_target_great": cpu.price_target_great,
            "price_target_fair": cpu.price_target_fair,
            "price_target_sample_size": cpu.price_target_sample_size,
            "price_target_confidence": cpu.price_target_confidence or "insufficient",
            "price_target_stddev": cpu.price_target_stddev,
            "price_target_updated_at": cpu.price_target_updated_at,
            "dollar_per_mark_single": cpu.dollar_per_mark_single,
            "dollar_per_mark_multi": cpu.dollar_per_mark_multi,
            "performance_value_percentile": cpu.performance_value_percentile,
            "performance_value_rating": cpu.performance_value_rating,
            "performance_metrics_updated_at": cpu.performance_metrics_updated_at,
            "listings_count": listings_count,
        }

        # Query top 10 active listings by adjusted_price_usd (ascending - cheapest first)
        listings_stmt = (
            select(Listing)
            .where(
                and_(
                    Listing.cpu_id == cpu_id,
                    Listing.status == ListingStatus.ACTIVE.value,
                    Listing.adjusted_price_usd.isnot(None),
                )
            )
            .order_by(Listing.adjusted_price_usd.asc())
            .limit(10)
        )
        listings_result = await session.execute(listings_stmt)
        listings = listings_result.scalars().all()

        associated_listings = [
            {
                "id": listing.id,
                "title": listing.title,
                "adjusted_price_usd": listing.adjusted_price_usd,
                "base_price_usd": listing.base_price_usd,
                "condition": listing.condition,
                "url": listing.url,
                "marketplace": listing.marketplace,
                "status": listing.status,
            }
            for listing in listings
        ]

        # Query all adjusted prices for price distribution (histogram)
        prices_stmt = select(Listing.adjusted_price_usd).where(
            and_(
                Listing.cpu_id == cpu_id,
                Listing.status == ListingStatus.ACTIVE.value,
                Listing.adjusted_price_usd.isnot(None),
                Listing.adjusted_price_usd > 0,
            )
        )
        prices_result = await session.execute(prices_stmt)
        price_distribution = [row[0] for row in prices_result.all()]

        # Build response with market data
        response = {
            **cpu_data,
            "associated_listings": associated_listings,
            "market_data": {
                "price_distribution": price_distribution,
            },
        }

        logger.info(
            f"Retrieved CPU detail for {cpu_id} with {len(associated_listings)} listings"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CPU detail for {cpu_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting CPU detail: {str(e)}",
        )


@router.get("/statistics/global", response_model=CPUStatistics)
async def get_cpu_statistics(
    session: AsyncSession = Depends(session_dependency),
) -> CPUStatistics:
    """Get global CPU statistics for filter options.

    Returns:
    - Unique manufacturers and sockets
    - Min/max ranges for cores, TDP, years
    - Total CPU count

    Results are computed on-demand but can be cached for performance.
    """
    try:
        # Query distinct manufacturers (non-null, sorted)
        manufacturers_stmt = select(distinct(Cpu.manufacturer)).where(
            Cpu.manufacturer.isnot(None)
        ).order_by(Cpu.manufacturer)
        manufacturers_result = await session.execute(manufacturers_stmt)
        manufacturers = [row[0] for row in manufacturers_result.all()]

        # Query distinct sockets (non-null, sorted)
        sockets_stmt = select(distinct(Cpu.socket)).where(
            Cpu.socket.isnot(None)
        ).order_by(Cpu.socket)
        sockets_result = await session.execute(sockets_stmt)
        sockets = [row[0] for row in sockets_result.all()]

        # Query min/max for cores, tdp, release_year
        ranges_stmt = select(
            func.min(Cpu.cores),
            func.max(Cpu.cores),
            func.min(Cpu.tdp_w),
            func.max(Cpu.tdp_w),
            func.min(Cpu.release_year),
            func.max(Cpu.release_year),
        )
        ranges_result = await session.execute(ranges_stmt)
        ranges = ranges_result.one()

        min_cores = ranges[0] or 2
        max_cores = ranges[1] or 64
        min_tdp = ranges[2] or 15
        max_tdp = ranges[3] or 280
        min_year = ranges[4] or 2015
        max_year = ranges[5] or 2025

        # Query total CPU count
        count_stmt = select(func.count(Cpu.id))
        count_result = await session.execute(count_stmt)
        total_count = count_result.scalar() or 0

        statistics = CPUStatistics(
            manufacturers=manufacturers,
            sockets=sockets,
            core_range=(min_cores, max_cores),
            tdp_range=(min_tdp, max_tdp),
            year_range=(min_year, max_year),
            total_count=total_count,
        )

        logger.info(
            f"Retrieved CPU statistics: {total_count} CPUs, "
            f"{len(manufacturers)} manufacturers, {len(sockets)} sockets"
        )
        return statistics

    except Exception as e:
        logger.error(f"Error getting CPU statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting CPU statistics: {str(e)}",
        )


@router.post("/recalculate-metrics", status_code=status.HTTP_202_ACCEPTED)
async def trigger_metric_recalculation(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(session_dependency),
) -> dict[str, str]:
    """Trigger background recalculation of all CPU metrics.

    Admin-only endpoint. Returns immediately with 202 Accepted.
    Actual processing happens in background.

    Returns:
        Status message with task acceptance
    """
    try:
        # Define background task function
        async def recalculate_task():
            """Background task to recalculate all CPU metrics."""
            # Note: We need a new session for the background task
            from ..db import session_scope
            async with session_scope() as bg_session:
                try:
                    summary = await CPUAnalyticsService.recalculate_all_cpu_metrics(bg_session)
                    logger.info(
                        f"CPU metrics recalculation completed: "
                        f"{summary['success']} succeeded, {summary['errors']} failed, "
                        f"{summary['total']} total"
                    )
                except Exception as e:
                    logger.error(f"Background CPU metrics recalculation failed: {e}", exc_info=True)

        # Add task to background tasks
        background_tasks.add_task(recalculate_task)

        logger.info("CPU metrics recalculation task queued")
        return {
            "status": "accepted",
            "message": "CPU metrics recalculation task has been queued and will run in the background",
        }

    except Exception as e:
        logger.error(f"Error queueing CPU metrics recalculation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error queueing recalculation task: {str(e)}",
        )


__all__ = ["router"]
