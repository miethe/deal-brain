"""
Bulk operation endpoints for listings.

Handles bulk updates and metric recalculation for multiple listings.
Extracted from monolithic listings.py for better modularity and maintainability.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.schemas import ListingRead

from ...db import session_dependency
from ...telemetry import get_logger
from ...services.listings import (
    bulk_update_listing_metrics,
    bulk_update_listings,
    update_listing_metrics,
)
from ..schemas.listings import (
    BulkRecalculateRequest,
    BulkRecalculateResponse,
    ListingBulkUpdateRequest,
    ListingBulkUpdateResponse,
)

router = APIRouter()
logger = get_logger("dealbrain.api.listings.bulk_operations")


@router.post("/bulk-update", response_model=ListingBulkUpdateResponse)
async def bulk_update_listings_endpoint(
    request: ListingBulkUpdateRequest,
    session: AsyncSession = Depends(session_dependency),
) -> ListingBulkUpdateResponse:
    """Bulk update multiple listings with the same field or attribute changes.

    Args:
        request: Bulk update request with listing IDs and changes
        session: Database session

    Returns:
        Response with updated listings and count

    Raises:
        404: No listings matched the provided identifiers
    """
    try:
        if not request.listing_ids:
            return ListingBulkUpdateResponse(updated=[], updated_count=0)
        listings = await bulk_update_listings(
            session,
            request.listing_ids,
            fields=request.fields or {},
            attributes=request.attributes or {},
        )
        if not listings:
            raise HTTPException(status_code=404, detail="No listings matched the provided identifiers")
        return ListingBulkUpdateResponse(
            updated=[ListingRead.model_validate(listing) for listing in listings],
            updated_count=len(listings),
        )
    except HTTPException:
        # Re-raise HTTPException without catching it
        raise
    except OperationalError as e:
        logger.error(f"Database connection error in bulk_update_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in bulk_update_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in bulk_update_listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.post("/{listing_id}/recalculate-metrics", response_model=ListingRead)
async def recalculate_listing_metrics(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency)
):
    """Recalculate all performance metrics for a single listing.

    Args:
        listing_id: ID of the listing to recalculate
        session: Database session

    Returns:
        Updated listing with recalculated metrics

    Raises:
        404: Listing not found
    """
    try:
        listing = await update_listing_metrics(session, listing_id)
        return ListingRead.model_validate(listing)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OperationalError as e:
        logger.error(f"Database connection error in recalculate_listing_metrics (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in recalculate_listing_metrics (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in recalculate_listing_metrics (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.post("/bulk-recalculate-metrics", response_model=BulkRecalculateResponse)
async def bulk_recalculate_metrics(
    request: BulkRecalculateRequest,
    session: AsyncSession = Depends(session_dependency)
):
    """Recalculate metrics for multiple listings.

    If listing_ids is None or empty, updates all listings.

    Args:
        request: Bulk recalculate request with optional listing IDs
        session: Database session

    Returns:
        Response with count of updated listings
    """
    try:
        count = await bulk_update_listing_metrics(
            session,
            request.listing_ids
        )
        return BulkRecalculateResponse(
            updated_count=count,
            message=f"Updated {count} listing(s)"
        )
    except OperationalError as e:
        logger.error(f"Database connection error in bulk_recalculate_metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in bulk_recalculate_metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in bulk_recalculate_metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )
