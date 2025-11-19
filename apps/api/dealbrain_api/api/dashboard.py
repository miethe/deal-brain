from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.schemas import ListingRead

from ..db import session_dependency
from ..models import Listing

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("", response_model=dict)
async def dashboard(
    budget: float = Query(default=400.0),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    top_value = await _fetch_listing(session, Listing.dollar_per_cpu_mark, asc)
    top_perf_watt = await _fetch_listing(session, Listing.perf_per_watt, desc)
    under_budget = await _fetch_under_budget(session, budget)
    return {
        "best_value": ListingRead.model_validate(top_value).model_dump() if top_value else None,
        "best_perf_per_watt": (
            ListingRead.model_validate(top_perf_watt).model_dump() if top_perf_watt else None
        ),
        "best_under_budget": [
            ListingRead.model_validate(item).model_dump() for item in under_budget
        ],
    }


async def _fetch_listing(session: AsyncSession, column, ordering):
    result = await session.execute(
        select(Listing).where(column.is_not(None)).order_by(ordering(column)).limit(1)
    )
    return result.scalars().first()


async def _fetch_under_budget(session: AsyncSession, budget: float):
    result = await session.execute(
        select(Listing)
        .where(Listing.adjusted_price_usd.is_not(None))
        .where(Listing.adjusted_price_usd <= budget)
        .order_by(Listing.score_composite.desc())
        .limit(5)
    )
    return result.scalars().unique().all()
