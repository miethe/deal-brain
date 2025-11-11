"""Performance metrics calculation for listings.

This module handles CPU-based performance metrics calculation,
including both base and adjusted price-per-performance metrics.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...models import Listing
from ...telemetry import get_logger

logger = get_logger("dealbrain.listings.metrics")


def calculate_cpu_performance_metrics(listing: Listing) -> dict[str, float]:
    """Calculate all CPU-based performance metrics for a listing.

    Adjusted metrics use component-based adjustment delta:
    adjusted_base_price = base_price + total_adjustment

    Where total_adjustment comes from valuation_breakdown['total_adjustment']
    (negative values decrease price, positive values increase price)

    Returns
    -------
        Dictionary with metric keys and calculated values.
        Empty dict if CPU not assigned, missing benchmark data, or price is None.

    """
    if not listing.cpu or listing.price_usd is None:
        return {}

    cpu = listing.cpu
    base_price = float(listing.price_usd)

    # Extract adjustment delta from valuation breakdown
    total_adjustment = 0.0
    if listing.valuation_breakdown:
        total_adjustment = float(listing.valuation_breakdown.get('total_adjustment', 0.0))

    adjusted_base_price = base_price - total_adjustment

    metrics = {}

    # Single-thread metrics
    if cpu.cpu_mark_single and cpu.cpu_mark_single > 0:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_base_price / cpu.cpu_mark_single

    # Multi-thread metrics
    if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_base_price / cpu.cpu_mark_multi

    return metrics


async def update_listing_metrics(
    session: AsyncSession,
    listing_id: int,
) -> Listing:
    """Recalculate and persist all performance metrics for a listing.

    Args:
    ----
        session: Database session
        listing_id: ID of listing to update

    Returns:
    -------
        Updated listing with recalculated metrics

    Raises:
    ------
        ValueError: If listing not found

    """
    # Fetch with CPU relationship
    stmt = select(Listing).where(Listing.id == listing_id).options(joinedload(Listing.cpu))
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    # Calculate metrics
    metrics = calculate_cpu_performance_metrics(listing)

    # Update listing
    for key, value in metrics.items():
        setattr(listing, key, value)

    await session.commit()
    await session.refresh(listing)
    return listing


async def bulk_update_listing_metrics(
    session: AsyncSession,
    listing_ids: list[int] | None = None,
) -> int:
    """Recalculate metrics for multiple listings.

    Args:
    ----
        session: Database session
        listing_ids: List of IDs to update. If None, updates all listings.

    Returns:
    -------
        Count of listings updated

    """
    stmt = select(Listing).options(joinedload(Listing.cpu))
    if listing_ids:
        stmt = stmt.where(Listing.id.in_(listing_ids))

    result = await session.execute(stmt)
    listings = result.scalars().all()

    updated_count = 0
    for listing in listings:
        metrics = calculate_cpu_performance_metrics(listing)
        for key, value in metrics.items():
            setattr(listing, key, value)
        updated_count += 1

    await session.commit()
    return updated_count
