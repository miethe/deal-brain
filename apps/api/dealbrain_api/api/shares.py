"""Public shares API endpoints.

This module provides REST API endpoints for public shareable deal pages (FR-A1):
- GET /deals/{listing_id}/{share_token} - View public shared deal (no auth required)
- Includes Redis caching for link preview crawlers
- OpenGraph metadata support for social media previews
"""

from __future__ import annotations

import logging

from dealbrain_core.schemas.sharing import PublicListingShareRead
from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.caching_service import CachingService
from ..services.sharing_service import SharingService

router = APIRouter(prefix="/v1/deals", tags=["shares"])
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

# Cache TTL for public shares (24 hours)
SHARE_CACHE_TTL_SECONDS = 86400


async def get_caching_service() -> CachingService:
    """Get caching service for Redis operations.

    Returns:
        CachingService instance with graceful fallback if Redis unavailable
    """
    return CachingService()


@router.get(
    "/{listing_id}/{share_token}",
    response_model=PublicListingShareRead,
    summary="View public shared deal",
    description=(
        "View a publicly shared deal without authentication. "
        "Increments view count and supports caching for link preview crawlers."
    ),
    responses={
        200: {"description": "Shared deal found and valid"},
        404: {"description": "Share not found or expired"},
        500: {"description": "Internal server error"},
    },
)
async def get_public_shared_deal(
    listing_id: int,
    share_token: str,
    session: AsyncSession = Depends(session_dependency),
    caching_service: CachingService = Depends(get_caching_service),
) -> PublicListingShareRead:
    """View public shared deal.

    This endpoint allows anyone to view a shared deal without authentication.
    It validates the share token, checks for expiry, increments view count,
    and returns the listing data.

    For link preview crawlers (OpenGraph), responses are cached in Redis for 24 hours.

    Args:
        listing_id: ID of the listing
        share_token: Unique share token
        session: Database session (injected)
        caching_service: Redis caching service (injected)

    Returns:
        PublicListingShareRead with listing data

    Raises:
        HTTPException: 404 if share not found or expired

    Example:
        GET /api/v1/deals/123/abc123def456...

        Response:
        {
            "share_token": "abc123def456...",
            "listing_id": 123,
            "view_count": 42,
            "is_expired": false
        }
    """
    with tracer.start_as_current_span("shares.get_public_shared_deal") as span:
        span.set_attribute("listing_id", listing_id)
        span.set_attribute("share_token", share_token[:8])

        # Build cache key
        cache_key = f"share:listing:{listing_id}:{share_token}"

        # Check Redis cache first (if available)
        cached_response = await caching_service.get(cache_key, PublicListingShareRead)
        if cached_response:
            logger.debug(f"Cache hit for share {share_token[:8]}...")
            span.set_attribute("cache_hit", True)
            return cached_response

        span.set_attribute("cache_hit", False)

        # Initialize sharing service
        sharing_service = SharingService(session)

        # Validate share token
        share, is_valid = await sharing_service.validate_listing_share_token(share_token)

        if not share:
            logger.info(f"Share not found for token {share_token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found"
            )

        # Verify listing_id matches (extra security check)
        if share.listing_id != listing_id:
            logger.warning(
                f"Listing ID mismatch: URL has {listing_id}, token has {share.listing_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found"
            )

        if not is_valid:
            logger.info(f"Share expired for token {share_token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share has expired"
            )

        # Increment view count (fire and forget - don't block response)
        try:
            await sharing_service.increment_share_view(share_token)
            span.set_attribute("view_incremented", True)
        except Exception as e:
            logger.error(f"Failed to increment view count: {e}")
            # Don't fail the request if view tracking fails
            span.set_attribute("view_incremented", False)

        # Build response
        response_data = PublicListingShareRead(
            share_token=share.share_token,
            listing_id=share.listing_id,
            view_count=share.view_count + 1,  # Include the incremented count
            is_expired=share.is_expired()
        )

        # Cache response for 24 hours (graceful fallback if Redis unavailable)
        cache_success = await caching_service.set(
            cache_key,
            response_data,
            ttl_seconds=SHARE_CACHE_TTL_SECONDS
        )
        if cache_success:
            logger.debug(f"Cached response for share {share_token[:8]}... (TTL: 24h)")
            span.set_attribute("cached", True)
        else:
            span.set_attribute("cached", False)

        logger.info(
            f"Shared deal viewed: listing_id={listing_id}, "
            f"share_token={share_token[:8]}..., "
            f"view_count={response_data.view_count}"
        )

        return response_data


__all__ = ["router"]
