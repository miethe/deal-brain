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


@router.get(
    "",
    response_model=list[CPUWithAnalytics],
    summary="List all CPUs with analytics",
    description="""
    Retrieve a comprehensive list of all CPUs in the catalog with embedded analytics data.

    **Analytics Data Included:**
    - **Price Targets**: Great/Good/Fair pricing benchmarks calculated from active marketplace listings
      - Great: One standard deviation below average (better deals)
      - Good: Average adjusted price (typical market price)
      - Fair: One standard deviation above average (premium pricing)
      - Confidence levels based on sample size: high (10+), medium (5-9), low (2-4), insufficient (<2)

    - **Performance Value Metrics**: Dollar-per-PassMark efficiency ratings
      - Single-thread and multi-thread price efficiency ratios
      - Percentile rankings (0 = best value, 100 = worst value)
      - Value ratings: excellent (0-25th), good (25-50th), fair (50-75th), poor (75-100th)

    - **Market Data**: Count of active listings for each CPU

    **Performance Notes:**
    - Analytics fields are pre-computed and stored in the CPU table for fast queries
    - No performance penalty when `include_analytics=true` (default)
    - Results are sorted alphabetically by CPU name

    **Use Cases:**
    - CPU catalog browsing with price intelligence
    - Performance value comparison across CPUs
    - Market availability analysis
    - Building filter dropdowns and search interfaces

    **Query Parameters:**
    - `include_analytics`: Set to `false` to exclude price targets and performance metrics (returns base CPU data only)
    """,
    response_description="List of CPUs with embedded analytics (price targets, performance value, active listings count)",
    responses={
        200: {
            "description": "Successful response with CPU list",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Intel Core i5-12400",
                            "manufacturer": "Intel",
                            "socket": "LGA1700",
                            "cores": 6,
                            "threads": 12,
                            "tdp_w": 65,
                            "igpu_model": "Intel UHD Graphics 730",
                            "cpu_mark_multi": 19450,
                            "cpu_mark_single": 3485,
                            "igpu_mark": 1450,
                            "release_year": 2022,
                            "notes": "12th Gen Alder Lake",
                            "passmark_slug": "intel-core-i5-12400",
                            "passmark_category": "desktop",
                            "passmark_id": "4821",
                            "attributes_json": {},
                            "created_at": "2025-01-15T10:30:00Z",
                            "updated_at": "2025-11-06T08:15:00Z",
                            "price_target_good": 350.00,
                            "price_target_great": 325.00,
                            "price_target_fair": 375.00,
                            "price_target_sample_size": 15,
                            "price_target_confidence": "high",
                            "price_target_stddev": 25.50,
                            "price_target_updated_at": "2025-11-06T08:15:00Z",
                            "dollar_per_mark_single": 0.100,
                            "dollar_per_mark_multi": 0.018,
                            "performance_value_percentile": 35.5,
                            "performance_value_rating": "good",
                            "performance_metrics_updated_at": "2025-11-06T08:15:00Z",
                            "listings_count": 12
                        },
                        {
                            "id": 2,
                            "name": "AMD Ryzen 5 5600X",
                            "manufacturer": "AMD",
                            "socket": "AM4",
                            "cores": 6,
                            "threads": 12,
                            "tdp_w": 65,
                            "igpu_model": None,
                            "cpu_mark_multi": 22141,
                            "cpu_mark_single": 3570,
                            "igpu_mark": None,
                            "release_year": 2020,
                            "notes": "Zen 3 architecture",
                            "passmark_slug": "amd-ryzen-5-5600x",
                            "passmark_category": "desktop",
                            "passmark_id": "4275",
                            "attributes_json": {},
                            "created_at": "2025-01-15T10:30:00Z",
                            "updated_at": "2025-11-06T08:15:00Z",
                            "price_target_good": 180.00,
                            "price_target_great": 160.00,
                            "price_target_fair": 200.00,
                            "price_target_sample_size": 8,
                            "price_target_confidence": "medium",
                            "price_target_stddev": 20.00,
                            "price_target_updated_at": "2025-11-06T08:15:00Z",
                            "dollar_per_mark_single": 0.050,
                            "dollar_per_mark_multi": 0.008,
                            "performance_value_percentile": 15.2,
                            "performance_value_rating": "excellent",
                            "performance_metrics_updated_at": "2025-11-06T08:15:00Z",
                            "listings_count": 6
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Internal server error during CPU retrieval",
            "content": {
                "application/json": {
                    "example": {"detail": "Error listing CPUs: Database connection failed"}
                }
            }
        }
    }
)
async def list_cpus(
    session: AsyncSession = Depends(session_dependency),
    include_analytics: bool = Query(
        default=True, description="Include price targets and performance metrics"
    ),
) -> Sequence[CPUWithAnalytics]:
    """List all CPUs with optional analytics data.

    Analytics fields are pre-computed and stored in CPU table,
    so this query is fast even with analytics enabled.

    Args:
        session: Async database session for queries
        include_analytics: Whether to include price targets and performance metrics (default: True)

    Returns:
        List of CPUs with embedded analytics (price targets, performance value, listings count)

    Raises:
        HTTPException(500): Error listing CPUs from database
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


@router.get(
    "/{cpu_id}",
    response_model=dict,
    summary="Get CPU detail with market data",
    description="""
    Retrieve comprehensive CPU information including specifications, analytics, and associated marketplace listings.

    **Response Data Structure:**

    **1. CPU Specifications:**
    - Complete technical specifications (name, manufacturer, socket, cores, threads, TDP, etc.)
    - PassMark benchmark scores (multi-thread, single-thread, iGPU)
    - Release year and metadata

    **2. Analytics Data:**
    - **Price Targets**: Great/Good/Fair pricing benchmarks with confidence levels and sample size
    - **Performance Value**: Dollar-per-PassMark metrics with percentile rankings and value ratings
    - **Active Listings Count**: Total number of active marketplace listings

    **3. Associated Listings (Top 10):**
    - Best-priced active listings sorted by adjusted price (cheapest first)
    - Includes: title, prices (base and adjusted), condition, URL, marketplace, status
    - Limited to 10 results for performance

    **4. Market Data:**
    - **Price Distribution**: Array of all adjusted prices from active listings for histogram visualization
    - Useful for understanding price variance and market trends

    **Use Cases:**
    - CPU detail page with comprehensive market intelligence
    - Price distribution visualization (histograms)
    - Finding best deals for a specific CPU
    - Market analysis and price trend monitoring

    **Performance Considerations:**
    - Listings are limited to top 10 by price for fast response
    - Price distribution includes all active listings for accurate market view
    - Analytics data is pre-computed for efficiency
    """,
    response_description="CPU detail with specifications, analytics, associated listings, and market data",
    responses={
        200: {
            "description": "Successful response with CPU detail",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Intel Core i5-12400",
                        "manufacturer": "Intel",
                        "socket": "LGA1700",
                        "cores": 6,
                        "threads": 12,
                        "tdp_w": 65,
                        "igpu_model": "Intel UHD Graphics 730",
                        "cpu_mark_multi": 19450,
                        "cpu_mark_single": 3485,
                        "igpu_mark": 1450,
                        "release_year": 2022,
                        "notes": "12th Gen Alder Lake",
                        "passmark_slug": "intel-core-i5-12400",
                        "passmark_category": "desktop",
                        "passmark_id": "4821",
                        "attributes_json": {},
                        "created_at": "2025-01-15T10:30:00Z",
                        "updated_at": "2025-11-06T08:15:00Z",
                        "price_target_good": 350.00,
                        "price_target_great": 325.00,
                        "price_target_fair": 375.00,
                        "price_target_sample_size": 15,
                        "price_target_confidence": "high",
                        "price_target_stddev": 25.50,
                        "price_target_updated_at": "2025-11-06T08:15:00Z",
                        "dollar_per_mark_single": 0.100,
                        "dollar_per_mark_multi": 0.018,
                        "performance_value_percentile": 35.5,
                        "performance_value_rating": "good",
                        "performance_metrics_updated_at": "2025-11-06T08:15:00Z",
                        "listings_count": 12,
                        "associated_listings": [
                            {
                                "id": 101,
                                "title": "Intel i5-12400 Desktop CPU - Like New",
                                "adjusted_price_usd": 320.00,
                                "base_price_usd": 340.00,
                                "condition": "refurbished",
                                "url": "https://example.com/listing/101",
                                "marketplace": "ebay",
                                "status": "active"
                            },
                            {
                                "id": 102,
                                "title": "i5-12400 Processor 6-Core",
                                "adjusted_price_usd": 325.00,
                                "base_price_usd": 325.00,
                                "condition": "new",
                                "url": "https://example.com/listing/102",
                                "marketplace": "amazon",
                                "status": "active"
                            }
                        ],
                        "market_data": {
                            "price_distribution": [320.00, 325.00, 330.00, 335.00, 340.00, 345.00, 350.00, 355.00, 360.00, 365.00, 370.00, 375.00]
                        }
                    }
                }
            }
        },
        404: {
            "description": "CPU not found with the given ID",
            "content": {
                "application/json": {
                    "example": {"detail": "CPU with id 99999 not found"}
                }
            }
        },
        422: {
            "description": "Validation error - invalid CPU ID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "cpu_id"],
                                "msg": "value is not a valid integer",
                                "type": "type_error.integer"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during CPU detail retrieval",
            "content": {
                "application/json": {
                    "example": {"detail": "Error getting CPU detail: Database query failed"}
                }
            }
        }
    }
)
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

    Args:
        cpu_id: Unique identifier of the CPU to retrieve
        session: Async database session for queries

    Returns:
        Dictionary containing CPU data, analytics, associated listings, and market data

    Raises:
        HTTPException(404): CPU not found with the given ID
        HTTPException(500): Error retrieving CPU detail from database
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


@router.get(
    "/statistics/global",
    response_model=CPUStatistics,
    summary="Get CPU catalog statistics",
    description="""
    Retrieve global statistics about the CPU catalog for building filter UI controls and understanding catalog coverage.

    **Statistics Included:**

    **1. Enumerated Options (for dropdowns):**
    - **Manufacturers**: Unique CPU manufacturers in the catalog (e.g., Intel, AMD)
      - Sorted alphabetically
      - Excludes null values
      - Used for manufacturer filter dropdowns

    - **Sockets**: Unique CPU socket types (e.g., LGA1700, AM4, AM5)
      - Sorted alphabetically
      - Excludes null values
      - Used for socket filter dropdowns

    **2. Numeric Ranges (for sliders):**
    - **Core Range**: Minimum and maximum core counts across all CPUs
      - Default range: (2, 64)
      - Used for core count range sliders

    - **TDP Range**: Minimum and maximum TDP values in watts
      - Default range: (15, 280)
      - Used for power consumption filters

    - **Year Range**: Minimum and maximum CPU release years
      - Default range: (2015, 2025)
      - Used for release year filters

    **3. Catalog Metrics:**
    - **Total Count**: Total number of CPUs in the catalog
      - Used for displaying catalog size
      - Useful for pagination calculations

    **Use Cases:**
    - Building dynamic filter controls in CPU browsing UI
    - Populating dropdown options for manufacturer and socket filters
    - Configuring range sliders for cores, TDP, and release year
    - Displaying catalog coverage statistics
    - Validating filter input ranges

    **Performance Notes:**
    - Statistics are computed on-demand from database
    - Consider caching results for production use (data changes infrequently)
    - All queries use indexed columns for fast execution
    - Response is lightweight and suitable for frequent polling
    """,
    response_description="Global CPU statistics including unique values, ranges, and total count",
    responses={
        200: {
            "description": "Successful response with CPU statistics",
            "content": {
                "application/json": {
                    "example": {
                        "manufacturers": ["AMD", "Intel"],
                        "sockets": ["AM4", "AM5", "LGA1200", "LGA1700"],
                        "core_range": [2, 64],
                        "tdp_range": [15, 280],
                        "year_range": [2015, 2025],
                        "total_count": 156
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during statistics calculation",
            "content": {
                "application/json": {
                    "example": {"detail": "Error getting CPU statistics: Database aggregation failed"}
                }
            }
        }
    }
)
async def get_cpu_statistics(
    session: AsyncSession = Depends(session_dependency),
) -> CPUStatistics:
    """Get global CPU statistics for filter options.

    Returns:
    - Unique manufacturers and sockets
    - Min/max ranges for cores, TDP, years
    - Total CPU count

    Args:
        session: Async database session for queries

    Returns:
        CPUStatistics object with unique values, ranges, and total count

    Raises:
        HTTPException(500): Error calculating CPU statistics from database

    Note:
        Results are computed on-demand but can be cached for performance.
        All queries use indexed columns for fast aggregation.
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


@router.post(
    "/recalculate-metrics",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger CPU metrics recalculation",
    description="""
    Trigger background recalculation of all CPU analytics metrics including price targets and performance values.

    **What Gets Recalculated:**

    **1. Price Targets (for each CPU):**
    - Good, Great, Fair price benchmarks from active listings
    - Sample size and confidence levels
    - Standard deviation of prices
    - Updated timestamps

    **2. Performance Value Metrics (for each CPU):**
    - Dollar-per-PassMark ratios (single-thread and multi-thread)
    - Percentile rankings across entire catalog
    - Value ratings (excellent, good, fair, poor)
    - Updated timestamps

    **Behavior:**
    - **Asynchronous Processing**: Returns immediately with `202 Accepted` status
    - **Background Execution**: Actual recalculation runs in background thread
    - **Non-Blocking**: API remains responsive during processing
    - **Duration**: Typically 1-3 minutes for full catalog depending on size

    **When to Use:**
    - After bulk listing imports or updates
    - When listing prices change significantly
    - After PassMark benchmark data updates
    - As part of scheduled maintenance (e.g., daily cron job)
    - When analytics appear stale or incorrect

    **Admin Considerations:**
    - Should be restricted to admin users only (not currently enforced)
    - Consider rate limiting to prevent abuse
    - Monitor background task queue for completion
    - Check logs for task success/failure

    **Response Format:**
    - Returns status message confirming task has been queued
    - Does not wait for completion
    - Check logs for final results (success/error counts)

    **Performance Impact:**
    - Low during queueing (immediate response)
    - Moderate database load during background processing
    - Queries use indexed columns for efficiency
    - Consider running during off-peak hours for large catalogs
    """,
    response_description="Confirmation that recalculation task has been queued",
    responses={
        202: {
            "description": "Task accepted and queued for background processing",
            "content": {
                "application/json": {
                    "example": {
                        "status": "accepted",
                        "message": "CPU metrics recalculation task has been queued and will run in the background"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during task queueing",
            "content": {
                "application/json": {
                    "example": {"detail": "Error queueing recalculation task: Task queue full"}
                }
            }
        }
    }
)
async def trigger_metric_recalculation(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(session_dependency),
) -> dict[str, str]:
    """Trigger background recalculation of all CPU metrics.

    Admin-only endpoint. Returns immediately with 202 Accepted.
    Actual processing happens in background.

    Args:
        background_tasks: FastAPI background tasks manager
        session: Async database session (for validation, not used by background task)

    Returns:
        Status message confirming task has been queued

    Raises:
        HTTPException(500): Error queueing recalculation task

    Note:
        Background task uses a new database session for safety.
        Check application logs for recalculation results and errors.
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
