"""User-to-user shares API endpoints.

This module provides REST API endpoints for user-to-user deal sharing (FR-A3):
- POST /user-shares - Create a user-to-user share
- GET /user-shares - List received shares (inbox)
- GET /user-shares/{share_token} - Preview a shared deal
- POST /user-shares/{share_token}/import - Import shared deal to collection
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from dealbrain_core.schemas.sharing import (
    CollectionItemRead,
    UserShareRead,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from opentelemetry import trace
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.integration_service import IntegrationService
from ..services.sharing_service import SharingService

router = APIRouter(prefix="/v1/user-shares", tags=["user-shares"])
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


# ==================== Auth Dependency (Placeholder) ====================


class CurrentUser(BaseModel):
    """Represents the currently authenticated user.

    TODO: This is a placeholder. Replace with actual auth implementation in Phase 4.
    """

    user_id: int
    username: str


async def get_current_user() -> CurrentUser:
    """Get currently authenticated user.

    TODO: This is a PLACEHOLDER implementation.
    In production, this should:
    1. Extract JWT from Authorization header
    2. Validate JWT signature and expiry
    3. Extract user_id from JWT claims
    4. Return CurrentUser with validated user_id

    For development/testing, this returns a hardcoded user.
    """
    # PLACEHOLDER: Return test user for development
    # In production, this would extract from JWT token
    logger.warning("Using placeholder auth - returning hardcoded user_id=1")
    return CurrentUser(user_id=1, username="testuser")


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


# ==================== Request/Response Schemas ====================


class CreateUserShareRequest(BaseModel):
    """Request body for creating a user share."""

    recipient_id: int = Field(..., description="User ID of recipient")
    listing_id: int = Field(..., description="Listing ID to share")
    message: Optional[str] = Field(None, max_length=500, description="Optional message to recipient")


class ImportShareRequest(BaseModel):
    """Request body for importing a shared deal."""

    collection_id: Optional[int] = Field(None, description="Collection ID (uses default if not provided)")


# ==================== Endpoints ====================


@router.post(
    "",
    response_model=UserShareRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create user-to-user share",
    description="Share a deal with another user. Rate limited to 10 shares per hour per user.",
    responses={
        201: {"description": "Share created successfully"},
        400: {"description": "Invalid request (user or listing not found)"},
        401: {"description": "Authentication required"},
        409: {"description": "Rate limit exceeded (10 shares/hour)"},
        500: {"description": "Internal server error"},
    },
)
async def create_user_share(
    payload: CreateUserShareRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> UserShareRead:
    """Create a user-to-user share.

    Allows users to share deals with other users, including an optional message.
    Enforces rate limiting (max 10 shares per hour per user).

    Args:
        payload: Request body with recipient_id, listing_id, and optional message
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        UserShareRead with share details including token

    Raises:
        HTTPException: 400 if recipient/listing not found, 409 if rate limit exceeded

    Example:
        POST /api/v1/user-shares
        {
            "recipient_id": 2,
            "listing_id": 123,
            "message": "Check out this deal!"
        }

        Response (201):
        {
            "id": 1,
            "sender_id": 1,
            "recipient_id": 2,
            "listing_id": 123,
            "share_token": "abc123def456...",
            "message": "Check out this deal!",
            "shared_at": "2025-11-17T12:00:00Z",
            "expires_at": "2025-12-17T12:00:00Z",
            "viewed_at": null,
            "imported_at": null,
            "is_expired": false,
            "is_viewed": false,
            "is_imported": false
        }
    """
    with tracer.start_as_current_span("user_shares.create") as span:
        span.set_attribute("sender_id", current_user.user_id)
        span.set_attribute("recipient_id", payload.recipient_id)
        span.set_attribute("listing_id", payload.listing_id)

        # Initialize sharing service
        sharing_service = SharingService(session)

        try:
            # Create share (service handles validation and rate limiting)
            share = await sharing_service.create_user_share(
                sender_id=current_user.user_id,
                recipient_id=payload.recipient_id,
                listing_id=payload.listing_id,
                message=payload.message,
                ttl_days=30
            )

            span.set_attribute("share_id", share.id)

            logger.info(
                f"User share created: id={share.id}, "
                f"sender={current_user.user_id}, "
                f"recipient={payload.recipient_id}, "
                f"listing={payload.listing_id}"
            )

            # Convert to response schema
            return UserShareRead(
                id=share.id,
                sender_id=share.sender_id,
                recipient_id=share.recipient_id,
                listing_id=share.listing_id,
                share_token=share.share_token,
                message=share.message,
                shared_at=share.shared_at,
                expires_at=share.expires_at,
                viewed_at=share.viewed_at,
                imported_at=share.imported_at,
                is_expired=share.is_expired(),
                is_viewed=share.is_viewed(),
                is_imported=share.is_imported()
            )

        except ValueError as e:
            # Recipient or listing not found
            logger.warning(f"Invalid share creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except PermissionError as e:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for user {current_user.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )


@router.get(
    "",
    response_model=list[UserShareRead],
    summary="List received shares (inbox)",
    description="Get shares received by the current user with optional filtering.",
    responses={
        200: {"description": "List of received shares"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def list_received_shares(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    skip: int = Query(0, ge=0, description="Number of shares to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of shares to return"),
    filter: str = Query("unviewed", regex="^(unviewed|all)$", description="Filter: 'unviewed' or 'all'"),
) -> list[UserShareRead]:
    """List shares received by current user.

    Retrieves the user's inbox of received shares with optional filtering.
    By default, only shows unviewed shares.

    Args:
        current_user: Currently authenticated user (injected)
        session: Database session (injected)
        skip: Number of shares to skip (pagination)
        limit: Maximum number of shares to return
        filter: Filter type ('unviewed' or 'all')

    Returns:
        List of UserShareRead ordered by shared_at (newest first)

    Example:
        GET /api/v1/user-shares?filter=all&limit=10

        Response (200):
        [
            {
                "id": 1,
                "sender_id": 2,
                "recipient_id": 1,
                "listing_id": 123,
                "share_token": "abc123...",
                "message": "Check this out!",
                "shared_at": "2025-11-17T12:00:00Z",
                "expires_at": "2025-12-17T12:00:00Z",
                "viewed_at": null,
                "imported_at": null,
                "is_expired": false,
                "is_viewed": false,
                "is_imported": false
            }
        ]
    """
    with tracer.start_as_current_span("user_shares.list_inbox") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("filter", filter)

        # Initialize sharing service
        sharing_service = SharingService(session)

        # Determine filter options
        include_expired = False
        include_imported = False
        if filter == "all":
            include_expired = True
            include_imported = True

        # Get inbox
        shares = await sharing_service.get_user_inbox(
            user_id=current_user.user_id,
            include_expired=include_expired,
            include_imported=include_imported,
            limit=limit,
            offset=skip
        )

        span.set_attribute("result_count", len(shares))

        logger.info(
            f"Listed inbox for user {current_user.user_id}: "
            f"{len(shares)} shares (filter={filter})"
        )

        # Convert to response schemas
        return [
            UserShareRead(
                id=share.id,
                sender_id=share.sender_id,
                recipient_id=share.recipient_id,
                listing_id=share.listing_id,
                share_token=share.share_token,
                message=share.message,
                shared_at=share.shared_at,
                expires_at=share.expires_at,
                viewed_at=share.viewed_at,
                imported_at=share.imported_at,
                is_expired=share.is_expired(),
                is_viewed=share.is_viewed(),
                is_imported=share.is_imported()
            )
            for share in shares
        ]


@router.get(
    "/{share_token}",
    response_model=UserShareRead,
    summary="Preview shared deal",
    description="Preview a user-to-user shared deal. Marks share as viewed if recipient is authenticated.",
    responses={
        200: {"description": "Share found and valid"},
        404: {"description": "Share not found or expired"},
        500: {"description": "Internal server error"},
    },
)
async def preview_user_share(
    share_token: str,
    session: AsyncSession = Depends(session_dependency),
    current_user: Optional[CurrentUserDep] = None,
) -> UserShareRead:
    """Preview a user-to-user shared deal.

    This endpoint allows anyone with the token to preview the share.
    If the viewer is authenticated and is the recipient, the share is marked as viewed.

    Args:
        share_token: Unique share token
        session: Database session (injected)
        current_user: Currently authenticated user (optional, injected)

    Returns:
        UserShareRead with share details

    Raises:
        HTTPException: 404 if share not found or expired

    Example:
        GET /api/v1/user-shares/abc123def456...

        Response (200):
        {
            "id": 1,
            "sender_id": 2,
            "recipient_id": 1,
            "listing_id": 123,
            "share_token": "abc123...",
            "message": "Check this out!",
            "shared_at": "2025-11-17T12:00:00Z",
            "expires_at": "2025-12-17T12:00:00Z",
            "viewed_at": "2025-11-17T13:00:00Z",
            "imported_at": null,
            "is_expired": false,
            "is_viewed": true,
            "is_imported": false
        }
    """
    with tracer.start_as_current_span("user_shares.preview") as span:
        span.set_attribute("share_token", share_token[:8])

        # Initialize sharing service
        sharing_service = SharingService(session)

        # Get share by token
        share = await sharing_service.share_repo.get_user_share_by_token(share_token)

        if not share:
            logger.info(f"Share not found for token {share_token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found"
            )

        if share.is_expired():
            logger.info(f"Share expired for token {share_token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share has expired"
            )

        # Mark as viewed if current user is the recipient
        if current_user and current_user.user_id == share.recipient_id:
            try:
                await sharing_service.mark_share_as_viewed(
                    share_id=share.id,
                    user_id=current_user.user_id
                )
                span.set_attribute("marked_viewed", True)
                logger.info(f"Marked share {share.id} as viewed by user {current_user.user_id}")
            except Exception as e:
                logger.error(f"Failed to mark share as viewed: {e}")
                # Don't fail the request if marking viewed fails
                span.set_attribute("marked_viewed", False)

        logger.info(
            f"User share previewed: id={share.id}, "
            f"token={share_token[:8]}..., "
            f"viewer={current_user.user_id if current_user else 'anonymous'}"
        )

        # Convert to response schema
        return UserShareRead(
            id=share.id,
            sender_id=share.sender_id,
            recipient_id=share.recipient_id,
            listing_id=share.listing_id,
            share_token=share.share_token,
            message=share.message,
            shared_at=share.shared_at,
            expires_at=share.expires_at,
            viewed_at=share.viewed_at,
            imported_at=share.imported_at,
            is_expired=share.is_expired(),
            is_viewed=share.is_viewed(),
            is_imported=share.is_imported()
        )


@router.post(
    "/{share_token}/import",
    response_model=CollectionItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import shared deal to collection",
    description="Import a shared deal into a collection. User must be the recipient of the share.",
    responses={
        201: {"description": "Deal imported successfully"},
        400: {"description": "Invalid request"},
        401: {"description": "Authentication required"},
        403: {"description": "User is not the recipient of this share"},
        409: {"description": "Deal already exists in collection"},
        500: {"description": "Internal server error"},
    },
)
async def import_shared_deal(
    share_token: str,
    payload: ImportShareRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionItemRead:
    """Import shared deal to collection.

    Imports a shared listing into the user's collection. If no collection is specified,
    the deal is added to the default collection. The user must be the recipient of the share.

    Args:
        share_token: Unique share token
        payload: Request body with optional collection_id
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionItemRead with imported item details

    Raises:
        HTTPException: 400 if share not found/expired, 403 if not recipient, 409 if duplicate

    Example:
        POST /api/v1/user-shares/abc123def456.../import
        {
            "collection_id": 5
        }

        Response (201):
        {
            "id": 1,
            "collection_id": 5,
            "listing_id": 123,
            "status": "undecided",
            "notes": "Shared: Check this out!",
            "position": null,
            "added_at": "2025-11-17T14:00:00Z",
            "updated_at": "2025-11-17T14:00:00Z"
        }
    """
    with tracer.start_as_current_span("user_shares.import") as span:
        span.set_attribute("share_token", share_token[:8])
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", payload.collection_id or "default")

        # Initialize integration service
        integration_service = IntegrationService(session)

        try:
            # Import shared deal (service handles all validation)
            item, collection = await integration_service.import_shared_deal(
                share_token=share_token,
                user_id=current_user.user_id,
                collection_id=payload.collection_id
            )

            span.set_attribute("item_id", item.id)
            span.set_attribute("actual_collection_id", collection.id)

            logger.info(
                f"Shared deal imported: user={current_user.user_id}, "
                f"share_token={share_token[:8]}..., "
                f"collection={collection.id}, "
                f"item={item.id}"
            )

            # Convert to response schema
            return CollectionItemRead(
                id=item.id,
                collection_id=item.collection_id,
                listing_id=item.listing_id,
                status=item.status,
                notes=item.notes,
                position=item.position,
                added_at=item.added_at,
                updated_at=item.updated_at
            )

        except ValueError as e:
            # Share not found, expired, or duplicate
            logger.warning(f"Failed to import share: {e}")
            if "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        except PermissionError as e:
            # User is not the recipient
            logger.warning(f"Permission denied for import: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


__all__ = ["router"]
