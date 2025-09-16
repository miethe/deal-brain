from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.schemas import ListingRead

from ..db import session_dependency
from ..models import Listing

router = APIRouter(prefix="/v1/rankings", tags=["rankings"])

VALID_METRICS = {
    "score_composite": desc,
    "score_cpu_multi": desc,
    "score_cpu_single": desc,
    "score_gpu": desc,
    "perf_per_watt": desc,
    "dollar_per_cpu_mark": asc,
    "dollar_per_single_mark": asc,
    "adjusted_price_usd": asc,
}


@router.get("", response_model=list[ListingRead])
async def rankings(
    metric: str = Query(default="score_composite"),
    limit: int = Query(default=10, le=100),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    if metric not in VALID_METRICS:
        raise HTTPException(status_code=400, detail=f"Unsupported metric '{metric}'")
    ordering = VALID_METRICS[metric]
    column = getattr(Listing, metric)
    result = await session.execute(
        select(Listing)
        .where(column.is_not(None))
        .order_by(ordering(column))
        .limit(limit)
    )
    listings = result.scalars().unique().all()
    return [ListingRead.model_validate(listing) for listing in listings]

