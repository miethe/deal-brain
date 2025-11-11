"""
CRUD endpoints for listings.

Handles basic listing operations: create, read, update, delete, and pagination.
Extracted from monolithic listings.py for better modularity and maintainability.
"""
from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.schemas import ListingCreate, ListingRead

from ...db import session_dependency
from ...telemetry import get_logger
from ...models import Listing
from ...services.listings import (
    apply_listing_metrics,
    complete_partial_import,
    create_listing,
    delete_listing,
    get_paginated_listings,
    partial_update_listing,
    sync_listing_components,
    update_listing,
)
from ..schemas.listings import (
    CompletePartialImportRequest,
    CompletePartialImportResponse,
    ListingPartialUpdateRequest,
    PaginatedListingsResponse,
)

router = APIRouter()
logger = get_logger("dealbrain.api.listings.crud")


@router.get("", response_model=list[ListingRead])
async def list_listings(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    try:
        result = await session.execute(select(Listing).order_by(Listing.created_at.desc()).offset(offset).limit(limit))
        listings = result.scalars().unique().all()
        return [ListingRead.model_validate(listing) for listing in listings]
    except OperationalError as e:
        logger.error(f"Database connection error in list_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in list_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in list_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.get("/paginated", response_model=PaginatedListingsResponse)
async def get_paginated_listings_endpoint(
    limit: int = Query(default=50, ge=1, le=500, description="Number of items per page (1-500)"),
    cursor: str | None = Query(default=None, description="Pagination cursor from previous response"),
    sort_by: str = Query(default="updated_at", regex=r"^[a-z_]+$", description="Column to sort by"),
    sort_order: str = Query(default="desc", regex=r"^(asc|desc)$", description="Sort direction (asc or desc)"),
    form_factor: str | None = Query(default=None, description="Filter by form factor"),
    manufacturer: str | None = Query(default=None, description="Filter by manufacturer"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price filter"),
    session: AsyncSession = Depends(session_dependency),
) -> PaginatedListingsResponse:
    """Get paginated listings with cursor-based pagination.

    This endpoint implements high-performance cursor-based pagination with:
    - Composite key (sort_column, id) for stable pagination
    - Base64-encoded cursors to prevent client manipulation
    - Cached total count (5 minutes TTL)
    - Support for dynamic sorting and filtering

    Performance: <100ms response time for 500-row pages.

    Query Parameters:
        limit: Number of items per page (1-500, default 50)
        cursor: Pagination cursor from previous response (optional)
        sort_by: Column to sort by (default "updated_at")
        sort_order: Sort direction ("asc" or "desc", default "desc")
        form_factor: Filter by form factor (optional)
        manufacturer: Filter by manufacturer (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)

    Returns:
        PaginatedListingsResponse with:
        - items: List of listings in current page
        - total: Total count of listings (cached)
        - limit: Requested page size
        - next_cursor: Cursor for next page (null if last page)
        - has_next: Whether more pages are available

    Example:
        GET /v1/listings/paginated?limit=50&sort_by=price_usd&sort_order=asc
        GET /v1/listings/paginated?cursor=eyJpZCI6MTIzLCJzb3J0X3ZhbHVlIjoiMjAyNC0wMS0wMVQwMDowMDowMCJ9&limit=50

    Raises:
        400: Invalid parameters (invalid sort column, cursor format, etc.)
        500: Server error
    """
    try:
        result = await get_paginated_listings(
            session,
            limit=limit,
            cursor=cursor,
            sort_by=sort_by,
            sort_order=sort_order,
            form_factor=form_factor,
            manufacturer=manufacturer,
            min_price=min_price,
            max_price=max_price,
        )

        return PaginatedListingsResponse(
            items=[ListingRead.model_validate(listing) for listing in result["items"]],
            total=result["total"],
            limit=result["limit"],
            next_cursor=result["next_cursor"],
            has_next=result["has_next"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OperationalError as e:
        logger.error(f"Database connection error in get_paginated_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in get_paginated_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in get_paginated_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.post("", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing_endpoint(
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    try:
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
    except OperationalError as e:
        logger.error(f"Database connection error in create_listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in create_listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in create_listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.get("/{listing_id}", response_model=ListingRead)
async def get_listing(listing_id: int, session: AsyncSession = Depends(session_dependency)) -> ListingRead:
    try:
        listing = await session.get(Listing, listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return ListingRead.model_validate(listing)
    except HTTPException:
        # Re-raise HTTPException without catching it
        raise
    except OperationalError as e:
        logger.error(f"Database connection error in get_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in get_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in get_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.put("/{listing_id}", response_model=ListingRead)
async def update_listing_endpoint(
    listing_id: int,
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    try:
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
    except HTTPException:
        # Re-raise HTTPException without catching it
        raise
    except OperationalError as e:
        logger.error(f"Database connection error in update_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in update_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in update_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.patch("/{listing_id}", response_model=ListingRead)
async def patch_listing_endpoint(
    listing_id: int,
    request: ListingPartialUpdateRequest,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    try:
        listing = await session.get(Listing, listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        updated = await partial_update_listing(
            session,
            listing,
            fields=request.fields or {},
            attributes=request.attributes or {},
        )
        return ListingRead.model_validate(updated)
    except HTTPException:
        # Re-raise HTTPException without catching it
        raise
    except OperationalError as e:
        logger.error(f"Database connection error in patch_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in patch_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in patch_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_listing_endpoint(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> None:
    """Delete a listing and all related data.

    Cascade deletes:
    - ListingComponent records
    - ListingScoreSnapshot records
    - RawPayload records
    - EntityFieldValue records for this listing

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: Listing not found
    """
    try:
        await delete_listing(session, listing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OperationalError as e:
        logger.error(f"Database connection error in delete_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in delete_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in delete_listing (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.patch(
    "/{listing_id}/complete",
    response_model=CompletePartialImportResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_partial_import_endpoint(
    listing_id: int,
    request: CompletePartialImportRequest,
    session: AsyncSession = Depends(session_dependency),
    # current_user: dict = Depends(get_current_user),  # TODO: Add auth when available
) -> CompletePartialImportResponse:
    """
    Complete a partial import by providing missing fields.

    This endpoint allows users to fill in missing data (typically price)
    for listings that were partially imported from URL extraction. After
    completion, the listing's quality is updated to "full" and metrics
    are calculated.

    Args:
        listing_id: ID of the partial listing to complete
        request: Completion data (at minimum, price)
        session: Database session
        current_user: Authenticated user (TODO)

    Returns:
        Updated listing with metrics calculated and quality="full"

    Raises:
        404: Listing not found
        400: Listing is not partial or validation failed
        422: Invalid request data

    Example:
        PATCH /v1/listings/123/complete
        {"price": 299.99}

        → Returns: {"id": 123, "quality": "full", ...}
    """
    try:
        updated_listing = await complete_partial_import(
            session=session,
            listing_id=listing_id,
            completion_data=request.model_dump(),
            user_id="system",  # TODO: Use current_user["id"] when auth is available
        )
        await session.commit()

        return CompletePartialImportResponse(
            id=updated_listing.id,
            title=updated_listing.title,
            price_usd=updated_listing.price_usd,
            quality=updated_listing.quality,
            missing_fields=updated_listing.missing_fields or [],
            adjusted_price_usd=updated_listing.adjusted_price_usd,
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except OperationalError as e:
        logger.error(f"Database connection error in complete_partial_import (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in complete_partial_import (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in complete_partial_import (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error completing partial import for listing {listing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete import"
        )
