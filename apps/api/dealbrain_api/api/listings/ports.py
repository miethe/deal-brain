"""
Ports management endpoints for listings.

Handles listing port profiles and port data.
Extracted from monolithic listings.py for better modularity and maintainability.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import session_dependency
from ...telemetry import get_logger
from ...services import ports as ports_service
from ..schemas.listings import PortEntry, PortsResponse, UpdatePortsRequest

router = APIRouter()
logger = get_logger("dealbrain.api.listings.ports")


@router.post("/{listing_id}/ports", response_model=PortsResponse)
async def update_listing_ports(
    listing_id: int,
    request: UpdatePortsRequest,
    session: AsyncSession = Depends(session_dependency)
):
    """Create or update ports for a listing.

    Args:
        listing_id: ID of the listing
        request: Port update request with port entries
        session: Database session

    Returns:
        Updated ports response

    Raises:
        404: Listing not found
    """
    try:
        ports_data = [p.model_dump() for p in request.ports]
        await ports_service.update_listing_ports(session, listing_id, ports_data)
        ports = await ports_service.get_listing_ports(session, listing_id)
        return PortsResponse(ports=[PortEntry(**p) for p in ports])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OperationalError as e:
        logger.error(f"Database connection error in update_listing_ports (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in update_listing_ports (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in update_listing_ports (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )


@router.get("/{listing_id}/ports", response_model=PortsResponse)
async def get_listing_ports(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency)
):
    """Get ports for a listing.

    Args:
        listing_id: ID of the listing
        session: Database session

    Returns:
        Ports response with port entries
    """
    try:
        ports = await ports_service.get_listing_ports(session, listing_id)
        return PortsResponse(ports=[PortEntry(**p) for p in ports])
    except OperationalError as e:
        logger.error(f"Database connection error in get_listing_ports (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in get_listing_ports (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in get_listing_ports (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )
