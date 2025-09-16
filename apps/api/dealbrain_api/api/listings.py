from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.schemas import ListingCreate, ListingRead

from ..db import session_dependency
from ..models import Listing
from ..services.listings import (
    apply_listing_metrics,
    create_listing,
    sync_listing_components,
    update_listing,
)

router = APIRouter(prefix="/v1/listings", tags=["listings"])


@router.get("", response_model=list[ListingRead])
async def list_listings(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    result = await session.execute(select(Listing).order_by(Listing.created_at.desc()).offset(offset).limit(limit))
    listings = result.scalars().unique().all()
    return [ListingRead.model_validate(listing) for listing in listings]


@router.post("", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing_endpoint(
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    listing_data = payload.model_dump(exclude={"components"}, exclude_none=True)
    listing = await create_listing(session, listing_data)
    await sync_listing_components(
        session,
        listing,
        [component.model_dump(exclude_none=True) for component in (payload.components or [])],
    )
    await apply_listing_metrics(session, listing)
    await session.refresh(listing)
    return ListingRead.model_validate(listing)


@router.get("/{listing_id}", response_model=ListingRead)
async def get_listing(listing_id: int, session: AsyncSession = Depends(session_dependency)) -> ListingRead:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingRead.model_validate(listing)


@router.put("/{listing_id}", response_model=ListingRead)
async def update_listing_endpoint(
    listing_id: int,
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing_data = payload.model_dump(exclude={"components"}, exclude_none=True)
    await update_listing(session, listing, listing_data)
    await sync_listing_components(
        session,
        listing,
        [component.model_dump(exclude_none=True) for component in (payload.components or [])],
    )
    await apply_listing_metrics(session, listing)
    await session.refresh(listing)
    return ListingRead.model_validate(listing)

