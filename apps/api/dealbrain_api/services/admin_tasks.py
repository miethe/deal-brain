"""Administrative maintenance helpers for backend-triggered jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Listing


@dataclass(frozen=True, slots=True)
class CpuMetricSummary:
    total: int
    updated: int
    skipped_no_cpu: int
    skipped_no_adjusted_price: int
    skipped_no_metrics: int

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "updated": self.updated,
            "skipped_no_cpu": self.skipped_no_cpu,
            "skipped_no_adjusted_price": self.skipped_no_adjusted_price,
            "skipped_no_metrics": self.skipped_no_metrics,
        }


async def recalculate_cpu_mark_metrics(
    session: AsyncSession,
    listing_ids: Sequence[int] | None = None,
) -> CpuMetricSummary:
    """Recalculate CPU dollar-per-mark metrics for listings with CPUs."""
    stmt = select(Listing).options(selectinload(Listing.cpu)).where(Listing.cpu_id.is_not(None))
    if listing_ids:
        stmt = stmt.where(Listing.id.in_(listing_ids))

    result = await session.execute(stmt)
    listings: Iterable[Listing] = result.scalars().all()

    total = 0
    updated = 0
    skipped_no_cpu = 0
    skipped_no_adjusted_price = 0
    skipped_no_metrics = 0

    for listing in listings:
        total += 1
        cpu = listing.cpu

        if not cpu:
            skipped_no_cpu += 1
            continue

        if not listing.adjusted_price_usd:
            skipped_no_adjusted_price += 1
            continue

        updated_flag = False

        if cpu.cpu_mark_single:
            listing.dollar_per_cpu_mark_single = listing.adjusted_price_usd / cpu.cpu_mark_single
            updated_flag = True

        if cpu.cpu_mark_multi:
            listing.dollar_per_cpu_mark_multi = listing.adjusted_price_usd / cpu.cpu_mark_multi
            updated_flag = True

        if updated_flag:
            updated += 1
        else:
            skipped_no_metrics += 1

    await session.flush()

    return CpuMetricSummary(
        total=total,
        updated=updated,
        skipped_no_cpu=skipped_no_cpu,
        skipped_no_adjusted_price=skipped_no_adjusted_price,
        skipped_no_metrics=skipped_no_metrics,
    )
