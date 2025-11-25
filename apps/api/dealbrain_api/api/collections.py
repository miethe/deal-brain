"""Collections API endpoints.

This module provides REST API endpoints for managing deal collections (FR-A4):
- POST /collections - Create a collection
- GET /collections - List user's collections
- GET /collections/{id} - Get collection details with items
- PATCH /collections/{id} - Update collection metadata
- PATCH /collections/{id}/visibility - Update collection visibility (Phase 2a)
- GET /collections/public/{id} - Get public collection (no auth) (Phase 2a)
- POST /collections/{id}/copy - Copy collection to workspace (Phase 2a)
- GET /collections/discover - Discover public collections (Phase 2a)
- DELETE /collections/{id} - Delete collection (cascade deletes items)
- POST /collections/{id}/items - Add item to collection
- PATCH /collections/{id}/items/{item_id} - Update collection item
- DELETE /collections/{id}/items/{item_id} - Remove item from collection
- GET /collections/{id}/export - Export collection as CSV or JSON
"""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Annotated

from dealbrain_core.schemas.sharing import (
    CollectionCreate,
    CollectionItemCreate,
    CollectionItemRead,
    CollectionItemUpdate,
    CollectionRead,
    CollectionUpdate,
    CollectionVisibilityUpdate,
    CollectionCopyRequest,
    PublicCollectionRead,
)
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from opentelemetry import trace
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.collections_service import CollectionsService

router = APIRouter(prefix="/v1/collections", tags=["collections"])
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


# ==================== Collection Endpoints ====================


@router.post(
    "",
    response_model=CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection",
    description="Create a new deal collection with specified visibility.",
    responses={
        201: {"description": "Collection created successfully"},
        400: {"description": "Invalid request (validation error)"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def create_collection(
    payload: CollectionCreate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionRead:
    """Create a new collection.

    Allows users to create named collections for organizing deals.
    Supports private, unlisted, and public visibility options.

    Args:
        payload: Request body with name, description, and visibility
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionRead with created collection details

    Raises:
        HTTPException: 400 if validation fails

    Example:
        POST /api/v1/collections
        {
            "name": "Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "private"
        }

        Response (201):
        {
            "id": 1,
            "user_id": 1,
            "name": "Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "private",
            "created_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T12:00:00Z",
            "item_count": 0,
            "items": null
        }
    """
    with tracer.start_as_current_span("collections.create") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_name", payload.name)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Create collection (service handles validation)
            collection = await collections_service.create_collection(
                user_id=current_user.user_id,
                name=payload.name,
                description=payload.description,
                visibility=payload.visibility.value,
            )

            span.set_attribute("collection_id", collection.id)

            logger.info(
                f"Collection created: id={collection.id}, "
                f"name='{collection.name}', "
                f"user={current_user.user_id}"
            )

            # Convert to response schema
            return CollectionRead(
                id=collection.id,
                user_id=collection.user_id,
                name=collection.name,
                description=collection.description,
                visibility=collection.visibility,
                created_at=collection.created_at,
                updated_at=collection.updated_at,
                item_count=0,
                items=None,
            )

        except ValueError as e:
            # Validation error
            logger.warning(f"Invalid collection creation: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=list[CollectionRead],
    summary="List user's collections",
    description="Get all collections owned by the current user with pagination.",
    responses={
        200: {"description": "List of collections"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"},
    },
)
async def list_collections(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    skip: int = Query(0, ge=0, description="Number of collections to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of collections to return"),
) -> list[CollectionRead]:
    """List user's collections.

    Retrieves all collections owned by the current user, ordered by creation date (newest first).
    Includes item counts for each collection.

    Args:
        current_user: Currently authenticated user (injected)
        session: Database session (injected)
        skip: Number of collections to skip (pagination)
        limit: Maximum number of collections to return

    Returns:
        List of CollectionRead ordered by created_at DESC

    Example:
        GET /api/v1/collections?limit=10

        Response (200):
        [
            {
                "id": 1,
                "user_id": 1,
                "name": "Gaming PCs",
                "description": "Best gaming deals",
                "visibility": "private",
                "created_at": "2025-11-17T12:00:00Z",
                "updated_at": "2025-11-17T12:00:00Z",
                "item_count": 5,
                "items": null
            }
        ]
    """
    with tracer.start_as_current_span("collections.list") as span:
        span.set_attribute("user_id", current_user.user_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        # Get user's collections
        collections = await collections_service.list_user_collections(
            user_id=current_user.user_id, limit=limit, offset=skip
        )

        span.set_attribute("result_count", len(collections))

        logger.info(
            f"Listed collections for user {current_user.user_id}: "
            f"{len(collections)} collections"
        )

        # Convert to response schemas
        return [
            CollectionRead(
                id=collection.id,
                user_id=collection.user_id,
                name=collection.name,
                description=collection.description,
                visibility=collection.visibility,
                created_at=collection.created_at,
                updated_at=collection.updated_at,
                item_count=len(collection.items) if collection.items else 0,
                items=None,
            )
            for collection in collections
        ]


@router.get(
    "/{collection_id}",
    response_model=CollectionRead,
    summary="Get collection details",
    description="Get collection details with all items. User must own the collection.",
    responses={
        200: {"description": "Collection found"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Collection not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_collection(
    collection_id: int,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionRead:
    """Get collection details with items.

    Retrieves a collection with all its items, including listing details.
    User must be the owner of the collection.

    Args:
        collection_id: Collection ID
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionRead with items array populated

    Raises:
        HTTPException: 403 if not owner, 404 if not found

    Example:
        GET /api/v1/collections/1

        Response (200):
        {
            "id": 1,
            "user_id": 1,
            "name": "Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "private",
            "created_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T12:00:00Z",
            "item_count": 2,
            "items": [
                {
                    "id": 1,
                    "collection_id": 1,
                    "listing_id": 123,
                    "status": "shortlisted",
                    "notes": "Great deal",
                    "position": null,
                    "added_at": "2025-11-17T12:00:00Z",
                    "updated_at": "2025-11-17T12:00:00Z"
                }
            ]
        }
    """
    with tracer.start_as_current_span("collections.get") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Get collection with items (service handles ownership check)
            collection = await collections_service.get_collection(
                collection_id=collection_id, user_id=current_user.user_id, load_items=True
            )

            if not collection:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
                )

            # Get items with details
            items = await collections_service.get_collection_items(
                collection_id=collection_id, user_id=current_user.user_id
            )

            span.set_attribute("item_count", len(items))

            logger.info(
                f"Collection retrieved: id={collection.id}, "
                f"user={current_user.user_id}, "
                f"items={len(items)}"
            )

            # Convert to response schema
            return CollectionRead(
                id=collection.id,
                user_id=collection.user_id,
                name=collection.name,
                description=collection.description,
                visibility=collection.visibility,
                created_at=collection.created_at,
                updated_at=collection.updated_at,
                item_count=len(items),
                items=[
                    CollectionItemRead(
                        id=item.id,
                        collection_id=item.collection_id,
                        listing_id=item.listing_id,
                        status=item.status,
                        notes=item.notes,
                        position=item.position,
                        added_at=item.added_at,
                        updated_at=item.updated_at,
                    )
                    for item in items
                ],
            )

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/{collection_id}",
    response_model=CollectionRead,
    summary="Update collection",
    description="Update collection metadata (name, description, visibility). User must own the collection.",
    responses={
        200: {"description": "Collection updated successfully"},
        400: {"description": "Invalid request (validation error)"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Collection not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_collection(
    collection_id: int,
    payload: CollectionUpdate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionRead:
    """Update collection metadata.

    Updates collection name, description, or visibility.
    All fields are optional (partial update).
    User must be the owner of the collection.

    Args:
        collection_id: Collection ID
        payload: Request body with optional updates
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionRead with updated collection details

    Raises:
        HTTPException: 400 if validation fails, 403 if not owner, 404 if not found

    Example:
        PATCH /api/v1/collections/1
        {
            "name": "Best Gaming PCs",
            "visibility": "public"
        }

        Response (200):
        {
            "id": 1,
            "user_id": 1,
            "name": "Best Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "public",
            "created_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T13:00:00Z",
            "item_count": 5,
            "items": null
        }
    """
    with tracer.start_as_current_span("collections.update") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Update collection (service handles ownership check and validation)
            updated = await collections_service.update_collection(
                collection_id=collection_id,
                user_id=current_user.user_id,
                name=payload.name,
                description=payload.description,
                visibility=payload.visibility.value if payload.visibility else None,
            )

            if not updated:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
                )

            logger.info(f"Collection updated: id={collection_id}, " f"user={current_user.user_id}")

            # Convert to response schema
            return CollectionRead(
                id=updated.id,
                user_id=updated.user_id,
                name=updated.name,
                description=updated.description,
                visibility=updated.visibility,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
                item_count=len(updated.items) if updated.items else 0,
                items=None,
            )

        except ValueError as e:
            # Validation error
            logger.warning(f"Invalid collection update: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== Task 2a-api-1: Update Visibility ====================


@router.patch(
    "/{collection_id}/visibility",
    response_model=CollectionRead,
    summary="Update collection visibility",
    description="Update collection visibility setting (private, unlisted, public). User must own the collection.",
    responses={
        200: {"description": "Visibility updated successfully"},
        400: {"description": "Invalid visibility value"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Collection not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_collection_visibility(
    collection_id: int,
    payload: CollectionVisibilityUpdate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionRead:
    """Update collection visibility.

    Updates the visibility setting for a collection.
    All transitions are allowed: private ↔ unlisted ↔ public

    Args:
        collection_id: Collection ID
        payload: Request body with new visibility setting
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionRead with updated collection details

    Raises:
        HTTPException: 400 if invalid visibility, 403 if not owner, 404 if not found

    Example:
        PATCH /api/v1/collections/1/visibility
        {
            "visibility": "public"
        }

        Response (200):
        {
            "id": 1,
            "user_id": 1,
            "name": "Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "public",
            "created_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T13:00:00Z",
            "item_count": 5,
            "items": null
        }
    """
    with tracer.start_as_current_span("collections.update_visibility") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)
        span.set_attribute("new_visibility", payload.visibility.value)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Update visibility (service handles ownership check and validation)
            updated = await collections_service.update_visibility(
                collection_id=collection_id,
                new_visibility=payload.visibility.value,
                user_id=current_user.user_id
            )

            if not updated:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection not found"
                )

            logger.info(
                f"Collection {collection_id} visibility updated to {payload.visibility.value} "
                f"by user {current_user.user_id}"
            )

            # Convert to response schema
            return CollectionRead(
                id=updated.id,
                user_id=updated.user_id,
                name=updated.name,
                description=updated.description,
                visibility=updated.visibility,
                created_at=updated.created_at,
                updated_at=updated.updated_at,
                item_count=len(updated.items) if updated.items else 0,
                items=None
            )

        except ValueError as e:
            # Validation error
            logger.warning(f"Invalid visibility update: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


# ==================== Task 2a-api-2: Public Collection View ====================


@router.get(
    "/public/{collection_id}",
    response_model=PublicCollectionRead,
    summary="Get public collection",
    description="Get public collection details without authentication. Only returns public collections.",
    responses={
        200: {"description": "Public collection found"},
        404: {"description": "Collection not found or not public"},
        500: {"description": "Internal server error"},
    },
)
async def get_public_collection(
    collection_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> PublicCollectionRead:
    """Get public collection without authentication.

    Returns collection details if visibility is 'public'.
    No authentication required. Does not return private or unlisted collections.

    Args:
        collection_id: Collection ID
        session: Database session (injected)

    Returns:
        PublicCollectionRead with collection details and items

    Raises:
        HTTPException: 404 if collection not found or not public

    Example:
        GET /api/v1/collections/public/1

        Response (200):
        {
            "id": 1,
            "name": "Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "public",
            "created_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T13:00:00Z",
            "item_count": 5,
            "items": [...],
            "owner_username": "testuser"
        }
    """
    with tracer.start_as_current_span("collections.get_public") as span:
        span.set_attribute("collection_id", collection_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        # Get public collection (no auth required)
        collection = await collections_service.get_public_collection(
            collection_id=collection_id,
            load_items=True
        )

        if not collection:
            logger.info(f"Public collection {collection_id} not found or not public")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found or not public"
            )

        # Get items with details
        items = await collections_service.get_collection_items(
            collection_id=collection_id,
            user_id=collection.user_id  # Use owner ID to bypass permission check
        )

        span.set_attribute("item_count", len(items))
        span.set_attribute("visibility", collection.visibility)

        logger.info(
            f"Public collection retrieved: id={collection.id}, "
            f"visibility={collection.visibility}, "
            f"items={len(items)}"
        )

        # Convert to response schema
        return PublicCollectionRead(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            visibility=collection.visibility,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
            item_count=len(items),
            items=[
                CollectionItemRead(
                    id=item.id,
                    collection_id=item.collection_id,
                    listing_id=item.listing_id,
                    status=item.status,
                    notes=item.notes,
                    position=item.position,
                    added_at=item.added_at,
                    updated_at=item.updated_at
                )
                for item in items
            ],
            owner_username="testuser"  # TODO: Replace with actual user lookup
        )


# ==================== Task 2a-api-3: Copy Collection ====================


@router.post(
    "/{collection_id}/copy",
    response_model=CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Copy collection",
    description="Copy a public or unlisted collection to user's workspace. Requires authentication.",
    responses={
        201: {"description": "Collection copied successfully"},
        400: {"description": "Invalid request or source collection not accessible"},
        401: {"description": "Authentication required"},
        403: {"description": "Cannot access source collection"},
        404: {"description": "Source collection not found"},
        500: {"description": "Internal server error"},
    },
)
async def copy_collection(
    collection_id: int,
    payload: CollectionCopyRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionRead:
    """Copy collection to user's workspace.

    Creates a new private collection with all items from the source collection.
    User must have access to the source collection (public, unlisted, or owned by user).

    Args:
        collection_id: Source collection ID to copy
        payload: Optional request body with custom name
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionRead with newly created collection details

    Raises:
        HTTPException: 400 if invalid, 403 if no access, 404 if not found

    Example:
        POST /api/v1/collections/1/copy
        {
            "name": "My Copy of Gaming PCs"
        }

        Response (201):
        {
            "id": 2,
            "user_id": 2,
            "name": "My Copy of Gaming PCs",
            "description": "Best gaming deals",
            "visibility": "private",
            "created_at": "2025-11-19T12:00:00Z",
            "updated_at": "2025-11-19T12:00:00Z",
            "item_count": 5,
            "items": null
        }
    """
    with tracer.start_as_current_span("collections.copy") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("source_collection_id", collection_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Copy collection (service handles access check and item copying)
            new_collection = await collections_service.copy_collection(
                source_collection_id=collection_id,
                user_id=current_user.user_id,
                new_name=payload.name
            )

            span.set_attribute("new_collection_id", new_collection.id)
            span.set_attribute("item_count", len(new_collection.items) if new_collection.items else 0)

            logger.info(
                f"Collection {collection_id} copied to {new_collection.id} "
                f"by user {current_user.user_id} "
                f"({len(new_collection.items) if new_collection.items else 0} items)"
            )

            # Convert to response schema
            return CollectionRead(
                id=new_collection.id,
                user_id=new_collection.user_id,
                name=new_collection.name,
                description=new_collection.description,
                visibility=new_collection.visibility,
                created_at=new_collection.created_at,
                updated_at=new_collection.updated_at,
                item_count=len(new_collection.items) if new_collection.items else 0,
                items=None
            )

        except ValueError as e:
            # Collection not found
            logger.warning(f"Failed to copy collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

        except PermissionError as e:
            # No access to source collection
            logger.warning(f"Permission denied for copying collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection",
    description="Delete collection and all its items (cascade). User must own the collection.",
    responses={
        204: {"description": "Collection deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Collection not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_collection(
    collection_id: int,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete collection.

    Deletes a collection and all its items (cascade delete handled by database).
    User must be the owner of the collection.

    Args:
        collection_id: Collection ID
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 403 if not owner, 404 if not found

    Example:
        DELETE /api/v1/collections/1

        Response (204): (no content)
    """
    with tracer.start_as_current_span("collections.delete") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Delete collection (service handles ownership check)
            deleted = await collections_service.delete_collection(
                collection_id=collection_id, user_id=current_user.user_id
            )

            if not deleted:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
                )

            logger.info(f"Collection deleted: id={collection_id}, " f"user={current_user.user_id}")

            return Response(status_code=status.HTTP_204_NO_CONTENT)

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== Collection Item Endpoints ====================


@router.post(
    "/{collection_id}/items",
    response_model=CollectionItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to collection",
    description="Add a listing to a collection. Deduplication prevents duplicate listings.",
    responses={
        201: {"description": "Item added successfully"},
        400: {"description": "Invalid request (listing not found)"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        409: {"description": "Listing already exists in collection"},
        500: {"description": "Internal server error"},
    },
)
async def add_collection_item(
    collection_id: int,
    payload: CollectionItemCreate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionItemRead:
    """Add item to collection.

    Adds a listing to a collection with optional status and notes.
    Deduplication check prevents adding the same listing twice.
    User must be the owner of the collection.

    Args:
        collection_id: Collection ID
        payload: Request body with listing_id, status, and notes
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionItemRead with created item details

    Raises:
        HTTPException: 400 if listing not found, 403 if not owner, 409 if duplicate

    Example:
        POST /api/v1/collections/1/items
        {
            "listing_id": 123,
            "status": "shortlisted",
            "notes": "Great deal on this one"
        }

        Response (201):
        {
            "id": 1,
            "collection_id": 1,
            "listing_id": 123,
            "status": "shortlisted",
            "notes": "Great deal on this one",
            "position": null,
            "added_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T12:00:00Z"
        }
    """
    with tracer.start_as_current_span("collections.add_item") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)
        span.set_attribute("listing_id", payload.listing_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Add item (service handles ownership, validation, and deduplication)
            item = await collections_service.add_item_to_collection(
                collection_id=collection_id,
                listing_id=payload.listing_id,
                user_id=current_user.user_id,
                status=payload.status.value,
                notes=payload.notes,
                position=payload.position,
            )

            span.set_attribute("item_id", item.id)

            logger.info(
                f"Item added to collection: collection={collection_id}, "
                f"listing={payload.listing_id}, "
                f"item={item.id}, "
                f"user={current_user.user_id}"
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
                updated_at=item.updated_at,
            )

        except ValueError as e:
            # Validation error or duplicate
            logger.warning(f"Failed to add item to collection: {e}")
            if "already exists" in str(e).lower():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/{collection_id}/items/{item_id}",
    response_model=CollectionItemRead,
    summary="Update collection item",
    description="Update item status, notes, or position. User must own the collection.",
    responses={
        200: {"description": "Item updated successfully"},
        400: {"description": "Invalid request (validation error)"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Item not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_collection_item(
    collection_id: int,
    item_id: int,
    payload: CollectionItemUpdate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionItemRead:
    """Update collection item.

    Updates item status, notes, or position.
    All fields are optional (partial update).
    User must be the owner of the collection.

    Args:
        collection_id: Collection ID (for path consistency)
        item_id: CollectionItem ID
        payload: Request body with optional updates
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        CollectionItemRead with updated item details

    Raises:
        HTTPException: 400 if validation fails, 403 if not owner, 404 if not found

    Example:
        PATCH /api/v1/collections/1/items/1
        {
            "status": "bought",
            "notes": "Purchased on 2025-11-17"
        }

        Response (200):
        {
            "id": 1,
            "collection_id": 1,
            "listing_id": 123,
            "status": "bought",
            "notes": "Purchased on 2025-11-17",
            "position": null,
            "added_at": "2025-11-17T12:00:00Z",
            "updated_at": "2025-11-17T14:00:00Z"
        }
    """
    with tracer.start_as_current_span("collections.update_item") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)
        span.set_attribute("item_id", item_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Update item (service handles ownership check and validation)
            updated = await collections_service.update_collection_item(
                item_id=item_id,
                user_id=current_user.user_id,
                status=payload.status.value if payload.status else None,
                notes=payload.notes,
                position=payload.position,
            )

            if not updated:
                logger.info(f"Collection item {item_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found"
                )

            logger.info(
                f"Item updated: id={item_id}, "
                f"collection={collection_id}, "
                f"user={current_user.user_id}"
            )

            # Convert to response schema
            return CollectionItemRead(
                id=updated.id,
                collection_id=updated.collection_id,
                listing_id=updated.listing_id,
                status=updated.status,
                notes=updated.notes,
                position=updated.position,
                added_at=updated.added_at,
                updated_at=updated.updated_at,
            )

        except ValueError as e:
            # Validation error
            logger.warning(f"Invalid item update: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for item {item_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/{collection_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from collection",
    description="Remove an item from a collection. User must own the collection.",
    responses={
        204: {"description": "Item removed successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Item not found"},
        500: {"description": "Internal server error"},
    },
)
async def remove_collection_item(
    collection_id: int,
    item_id: int,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Remove item from collection.

    Removes an item from a collection.
    User must be the owner of the collection.

    Args:
        collection_id: Collection ID (for path consistency)
        item_id: CollectionItem ID
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 403 if not owner, 404 if not found

    Example:
        DELETE /api/v1/collections/1/items/1

        Response (204): (no content)
    """
    with tracer.start_as_current_span("collections.remove_item") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)
        span.set_attribute("item_id", item_id)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Remove item (service handles ownership check)
            removed = await collections_service.remove_item_from_collection(
                item_id=item_id, user_id=current_user.user_id
            )

            if not removed:
                logger.info(f"Collection item {item_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Collection item not found"
                )

            logger.info(
                f"Item removed: id={item_id}, "
                f"collection={collection_id}, "
                f"user={current_user.user_id}"
            )

            return Response(status_code=status.HTTP_204_NO_CONTENT)

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for item {item_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== Export Endpoint ====================


@router.get(
    "/{collection_id}/export",
    summary="Export collection",
    description="Export collection as CSV or JSON file. User must own the collection.",
    responses={
        200: {"description": "Collection exported successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not own this collection"},
        404: {"description": "Collection not found"},
        500: {"description": "Internal server error"},
    },
)
async def export_collection(
    collection_id: int,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    format: str = Query("json", regex="^(csv|json)$", description="Export format: csv or json"),
) -> Response:
    """Export collection.

    Exports a collection with all items and listing details as CSV or JSON.
    User must be the owner of the collection.

    CSV format includes columns: name, price, CPU, GPU, $/CPU Mark, score, status, notes
    JSON format includes full collection and item metadata.

    Args:
        collection_id: Collection ID
        current_user: Currently authenticated user (injected)
        session: Database session (injected)
        format: Export format (csv or json)

    Returns:
        File download (CSV or JSON)

    Raises:
        HTTPException: 403 if not owner, 404 if not found

    Example:
        GET /api/v1/collections/1/export?format=csv

        Response (200):
        Content-Type: text/csv
        Content-Disposition: attachment; filename="collection_1.csv"

        name,price,cpu,gpu,cpu_mark,score,status,notes
        "Gaming PC",599.99,"i5-12400","GTX 1650",85.5,4.2,"shortlisted","Great deal"
    """
    with tracer.start_as_current_span("collections.export") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("collection_id", collection_id)
        span.set_attribute("format", format)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Get collection with items (service handles ownership check)
            collection = await collections_service.get_collection(
                collection_id=collection_id, user_id=current_user.user_id, load_items=True
            )

            if not collection:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
                )

            # Get items with full details
            items = await collections_service.get_collection_items(
                collection_id=collection_id, user_id=current_user.user_id
            )

            span.set_attribute("item_count", len(items))

            if format == "csv":
                # Generate CSV
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

                # Write header
                writer.writerow(
                    [
                        "title",
                        "price_usd",
                        "cpu",
                        "gpu",
                        "dollar_per_cpu_mark",
                        "score",
                        "status",
                        "notes",
                    ]
                )

                # Write rows
                for item in items:
                    listing = item.listing if hasattr(item, "listing") else None
                    writer.writerow(
                        [
                            listing.title if listing else "",
                            (
                                f"{listing.price_usd:.2f}"
                                if listing and listing.price_usd is not None
                                else ""
                            ),
                            listing.cpu.name if listing and listing.cpu else "",
                            listing.gpu.name if listing and listing.gpu else "",
                            (
                                f"{listing.dollar_per_cpu_mark:.2f}"
                                if listing and listing.dollar_per_cpu_mark is not None
                                else ""
                            ),
                            (
                                f"{listing.score_composite:.2f}"
                                if listing and listing.score_composite is not None
                                else ""
                            ),
                            item.status,
                            item.notes or "",
                        ]
                    )

                logger.info(
                    f"Collection exported as CSV: id={collection_id}, "
                    f"user={current_user.user_id}, "
                    f"items={len(items)}"
                )

                # Return CSV file
                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f'attachment; filename="collection_{collection_id}.csv"'
                    },
                )

            else:  # format == "json"
                # Use ExportImportService for portable v1.0.0 JSON export
                from ..services.export_import import ExportImportService
                from datetime import datetime

                export_service = ExportImportService(session)

                try:
                    # Export using v1.0.0 portable schema
                    portable_export = await export_service.export_collection_as_json(
                        collection_id=collection_id,
                        user_id=current_user.user_id
                    )

                    # Generate filename with current date
                    current_date = datetime.utcnow().strftime("%Y-%m-%d")
                    filename = f"deal-brain-collection-{collection.name.replace(' ', '-')}-{current_date}.json"

                    # Serialize to JSON
                    json_content = portable_export.model_dump_json(indent=2, exclude_none=True)

                    logger.info(
                        f"Collection exported as JSON (v1.0.0): id={collection_id}, "
                        f"user={current_user.user_id}, "
                        f"items={len(items)}, "
                        f"size={len(json_content)} bytes"
                    )

                    # Return JSON file
                    return Response(
                        content=json_content,
                        media_type="application/json",
                        headers={
                            "Content-Disposition": f'attachment; filename="{filename}"'
                        }
                    )

                except ValueError as e:
                    logger.error(f"Export service error: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Export failed: {str(e)}"
                    )

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==================== Task 2a-api-4: Discovery Endpoint ====================


@router.get(
    "/discover",
    response_model=list[PublicCollectionRead],
    summary="Discover public collections",
    description="Search and browse public collections with filtering and pagination. No authentication required.",
    responses={
        200: {"description": "List of public collections"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"},
    },
)
async def discover_collections(
    session: AsyncSession = Depends(session_dependency),
    q: str | None = Query(None, description="Search query for name/description"),
    owner_id: int | None = Query(None, description="Filter by owner user ID"),
    sort: str = Query("recent", regex="^(recent|popular)$", description="Sort order: recent or popular"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip (pagination)"),
) -> list[PublicCollectionRead]:
    """Discover public collections.

    Browse and search public collections without authentication.
    Supports filtering by search query, owner, and sorting options.

    Args:
        session: Database session (injected)
        q: Optional search query for name/description
        owner_id: Optional filter by collection owner
        sort: Sort order (recent=created_at DESC, popular=view_count DESC)
        limit: Maximum number of results (default 20, max 100)
        offset: Pagination offset (default 0)

    Returns:
        List of PublicCollectionRead ordered by specified criteria

    Example:
        GET /api/v1/collections/discover?q=gaming&sort=recent&limit=10

        Response (200):
        [
            {
                "id": 1,
                "name": "Gaming PCs",
                "description": "Best gaming deals",
                "visibility": "public",
                "created_at": "2025-11-17T12:00:00Z",
                "updated_at": "2025-11-17T13:00:00Z",
                "item_count": 5,
                "items": null,
                "owner_username": "testuser"
            }
        ]
    """
    with tracer.start_as_current_span("collections.discover") as span:
        span.set_attribute("search_query", q or "")
        span.set_attribute("owner_id", owner_id or 0)
        span.set_attribute("sort", sort)
        span.set_attribute("limit", limit)
        span.set_attribute("offset", offset)

        # Initialize collections service
        collections_service = CollectionsService(session)

        try:
            # Handle different query scenarios
            if q:
                # Search collections by query
                collections = await collections_service.search_collections(
                    query=q,
                    visibility_filter="public",
                    limit=limit,
                    offset=offset
                )
            elif owner_id:
                # Filter by owner
                collections = await collections_service.filter_by_owner(
                    owner_id=owner_id,
                    visibility_filter="public",
                    limit=limit,
                    offset=offset
                )
            else:
                # List all public collections
                collections = await collections_service.list_public_collections(
                    visibility_filter="public",
                    sort_by=sort,
                    limit=limit,
                    offset=offset
                )

            span.set_attribute("result_count", len(collections))

            logger.info(
                f"Collections discovered: query={q}, owner={owner_id}, "
                f"sort={sort}, results={len(collections)}"
            )

            # Convert to response schemas
            return [
                PublicCollectionRead(
                    id=collection.id,
                    name=collection.name,
                    description=collection.description,
                    visibility=collection.visibility,
                    created_at=collection.created_at,
                    updated_at=collection.updated_at,
                    item_count=len(collection.items) if collection.items else 0,
                    items=None,  # Don't include items in list view for performance
                    owner_username="testuser"  # TODO: Replace with actual user lookup
                )
                for collection in collections
            ]

        except ValueError as e:
            # Invalid query parameters
            logger.warning(f"Invalid discover query: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


# ==================== Task 2c-api-4: POST /collections/import ====================


@router.post(
    "/import",
    status_code=status.HTTP_200_OK,
    summary="Import collection from JSON (preview)",
    description="Import a collection from JSON file or data. Returns preview with duplicate detection. User must confirm via /import/confirm.",
    responses={
        200: {"description": "Import preview created successfully"},
        400: {"description": "Invalid JSON format or schema validation failed"},
        401: {"description": "Authentication required"},
        422: {"description": "Unprocessable entity (invalid schema)"},
        500: {"description": "Internal server error"},
    },
)
async def import_collection(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    file: UploadFile = File(..., description="JSON file upload (multipart/form-data)"),
) -> dict:
    """Import collection from JSON with preview and duplicate detection.

    Accepts a JSON file upload. Validates against v1.0.0 schema,
    detects potential duplicate collections, and returns a preview for user confirmation.

    Args:
        current_user: Currently authenticated user (injected)
        session: Database session (injected)
        file: JSON file upload (multipart/form-data)

    Returns:
        Import preview with preview_id, collection data, and duplicates

    Raises:
        HTTPException: 400 if invalid format, 422 if schema validation fails

    Example:
        POST /api/v1/collections/import
        Content-Type: multipart/form-data
        file: collection.json

        Response (200):
        {
            "preview_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "collection",
            "collection_data": {
                "name": "Gaming Deals",
                "description": "Best gaming PC deals",
                "item_count": 5
            },
            "duplicates": [
                {
                    "entity_id": 10,
                    "entity_type": "collection",
                    "match_score": 1.0,
                    "match_reason": "Exact name match",
                    "entity_data": { "id": 10, "name": "Gaming Deals", ... }
                }
            ],
            "expires_at": "2025-11-19T12:30:00Z"
        }
    """
    with tracer.start_as_current_span("collections.import") as span:
        span.set_attribute("user_id", current_user.user_id)

        logger.info(f"Importing collection for user {current_user.user_id}")

        # Parse JSON from uploaded file
        try:
            # Read file content
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty file uploaded"
                )

            # Decode and parse JSON
            try:
                json_text = content.decode("utf-8")
                json_data = json.loads(json_text)
            except UnicodeDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid encoding, expected UTF-8: {e}"
                )
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON format: {e}"
                )

            logger.info(f"Parsed JSON from file: {file.filename}")

        except HTTPException:
            # Re-raise HTTPException without wrapping
            raise

        except Exception as e:
            logger.exception("Error parsing JSON input")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse input: {str(e)}"
            )

        # Initialize export service
        from ..services.export_import import ExportImportService, _preview_cache

        export_service = ExportImportService(session)

        try:
            # Validate schema and create preview with duplicate detection
            preview_id = await export_service.import_collection_from_json(
                json_data=json_data,
                user_id=current_user.user_id
            )

            # Retrieve preview to build response
            preview = _preview_cache.get(preview_id)

            if not preview:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create preview"
                )

            span.set_attribute("preview_id", preview_id)
            span.set_attribute("duplicate_count", len(preview.duplicates))

            logger.info(
                f"Import preview created: preview_id={preview_id}, "
                f"collection='{preview.data.data.collection.name}', "
                f"items={len(preview.data.data.items)}, "
                f"duplicates={len(preview.duplicates)}, "
                f"user={current_user.user_id}"
            )

            # Build response
            return {
                "preview_id": preview_id,
                "type": preview.type,
                "collection_data": {
                    "name": preview.data.data.collection.name,
                    "description": preview.data.data.collection.description,
                    "item_count": len(preview.data.data.items)
                },
                "duplicates": [
                    {
                        "entity_id": dup.entity_id,
                        "entity_type": dup.entity_type,
                        "match_score": dup.match_score,
                        "match_reason": dup.match_reason,
                        "entity_data": dup.entity_data
                    }
                    for dup in preview.duplicates
                ],
                "expires_at": preview.expires_at.isoformat()
            }

        except ValueError as e:
            # Schema validation error
            logger.warning(f"Schema validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )

        except Exception as e:
            logger.exception("Failed to import collection")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Import failed: {str(e)}"
            )


# ==================== Task 2c-api-4b: POST /collections/import/confirm ====================


class ConfirmCollectionImportRequest(BaseModel):
    """Request to confirm and execute a collection import."""

    preview_id: str
    merge_strategy: str = "create_new"  # create_new | merge_items | skip
    target_collection_id: int | None = None


@router.post(
    "/import/confirm",
    response_model=CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm collection import",
    description="Confirm and execute a collection import from preview. Creates new collection or merges items based on strategy.",
    responses={
        201: {"description": "Collection imported successfully"},
        400: {"description": "Invalid preview_id or merge strategy"},
        401: {"description": "Authentication required"},
        404: {"description": "Preview not found or expired"},
        500: {"description": "Internal server error"},
    },
)
async def confirm_import_collection(
    request: ConfirmCollectionImportRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> CollectionRead:
    """Confirm and execute collection import.

    Executes the import operation from a preview, applying the specified merge strategy.
    Preview must not be expired (30 minute TTL).

    Args:
        request: Confirmation request with preview_id and merge strategy
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        Created or updated collection details

    Raises:
        HTTPException: 400 if invalid, 404 if preview not found

    Merge Strategies:
        - create_new: Always create new collection (default)
        - merge_items: Add items to existing collection (requires target_collection_id)
        - skip: Don't import (returns error)

    Example:
        POST /api/v1/collections/import/confirm
        {
            "preview_id": "550e8400-e29b-41d4-a716-446655440000",
            "merge_strategy": "create_new"
        }

        Response (201):
        {
            "id": 10,
            "user_id": 1,
            "name": "Gaming Deals",
            "description": "Best gaming PC deals",
            "visibility": "private",
            "created_at": "2025-11-19T12:00:00Z",
            "updated_at": "2025-11-19T12:00:00Z",
            "item_count": 5,
            "items": null
        }
    """
    with tracer.start_as_current_span("collections.import_confirm") as span:
        span.set_attribute("user_id", current_user.user_id)
        span.set_attribute("preview_id", request.preview_id)
        span.set_attribute("merge_strategy", request.merge_strategy)

        logger.info(
            f"Confirming collection import: preview_id={request.preview_id}, "
            f"strategy={request.merge_strategy}, "
            f"user={current_user.user_id}"
        )

        # Initialize export service
        from ..services.export_import import ExportImportService

        export_service = ExportImportService(session)

        try:
            # Confirm and execute import
            collection = await export_service.confirm_import_collection(
                preview_id=request.preview_id,
                merge_strategy=request.merge_strategy,
                target_collection_id=request.target_collection_id,
                user_id=current_user.user_id
            )

            span.set_attribute("collection_id", collection.id)
            span.set_attribute("item_count", len(collection.items) if collection.items else 0)

            logger.info(
                f"Collection imported successfully: id={collection.id}, "
                f"name='{collection.name}', "
                f"items={len(collection.items) if collection.items else 0}, "
                f"strategy={request.merge_strategy}, "
                f"user={current_user.user_id}"
            )

            # Convert to response schema
            return CollectionRead(
                id=collection.id,
                user_id=collection.user_id,
                name=collection.name,
                description=collection.description,
                visibility=collection.visibility,
                created_at=collection.created_at,
                updated_at=collection.updated_at,
                item_count=len(collection.items) if collection.items else 0,
                items=None
            )

        except ValueError as e:
            # Preview not found or invalid merge strategy
            logger.warning(f"Import confirmation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except Exception as e:
            logger.exception("Failed to confirm collection import")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Import confirmation failed: {str(e)}"
            )


__all__ = ["router"]
