"""Collections API endpoints.

This module provides REST API endpoints for managing deal collections (FR-A4):
- POST /collections - Create a collection
- GET /collections - List user's collections
- GET /collections/{id} - Get collection details with items
- PATCH /collections/{id} - Update collection metadata
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
from typing import Annotated, Optional

from dealbrain_core.schemas.sharing import (
    CollectionCreate,
    CollectionItemCreate,
    CollectionItemRead,
    CollectionItemUpdate,
    CollectionRead,
    CollectionUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from opentelemetry import trace
from pydantic import BaseModel, Field
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
                visibility=payload.visibility.value
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
                items=None
            )

        except ValueError as e:
            # Validation error
            logger.warning(f"Invalid collection creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


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
            user_id=current_user.user_id,
            limit=limit,
            offset=skip
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
                items=None
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
                collection_id=collection_id,
                user_id=current_user.user_id,
                load_items=True
            )

            if not collection:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection not found"
                )

            # Get items with details
            items = await collections_service.get_collection_items(
                collection_id=collection_id,
                user_id=current_user.user_id
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
                        updated_at=item.updated_at
                    )
                    for item in items
                ]
            )

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


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
                visibility=payload.visibility.value if payload.visibility else None
            )

            if not updated:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection not found"
                )

            logger.info(
                f"Collection updated: id={collection_id}, "
                f"user={current_user.user_id}"
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
            logger.warning(f"Invalid collection update: {e}")
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
                collection_id=collection_id,
                user_id=current_user.user_id
            )

            if not deleted:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection not found"
                )

            logger.info(
                f"Collection deleted: id={collection_id}, "
                f"user={current_user.user_id}"
            )

            return Response(status_code=status.HTTP_204_NO_CONTENT)

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


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
                position=payload.position
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
                updated_at=item.updated_at
            )

        except ValueError as e:
            # Validation error or duplicate
            logger.warning(f"Failed to add item to collection: {e}")
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
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


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
                position=payload.position
            )

            if not updated:
                logger.info(f"Collection item {item_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection item not found"
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
                updated_at=updated.updated_at
            )

        except ValueError as e:
            # Validation error
            logger.warning(f"Invalid item update: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for item {item_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


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
                item_id=item_id,
                user_id=current_user.user_id
            )

            if not removed:
                logger.info(f"Collection item {item_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection item not found"
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


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
                collection_id=collection_id,
                user_id=current_user.user_id,
                load_items=True
            )

            if not collection:
                logger.info(f"Collection {collection_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Collection not found"
                )

            # Get items with full details
            items = await collections_service.get_collection_items(
                collection_id=collection_id,
                user_id=current_user.user_id
            )

            span.set_attribute("item_count", len(items))

            if format == "csv":
                # Generate CSV
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

                # Write header
                writer.writerow([
                    "name",
                    "price",
                    "cpu",
                    "gpu",
                    "cpu_mark_ratio",
                    "score",
                    "status",
                    "notes"
                ])

                # Write rows
                for item in items:
                    listing = item.listing if hasattr(item, 'listing') else None
                    writer.writerow([
                        listing.name if listing else "",
                        listing.price if listing else "",
                        listing.cpu.model if listing and listing.cpu else "",
                        listing.gpu.model if listing and listing.gpu else "",
                        f"{listing.cpu_mark_ratio:.2f}" if listing and listing.cpu_mark_ratio else "",
                        f"{listing.overall_score:.2f}" if listing and listing.overall_score else "",
                        item.status,
                        item.notes or ""
                    ])

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
                    }
                )

            else:  # format == "json"
                # Generate JSON
                export_data = {
                    "collection": {
                        "id": collection.id,
                        "name": collection.name,
                        "description": collection.description,
                        "visibility": collection.visibility,
                        "created_at": collection.created_at.isoformat(),
                        "updated_at": collection.updated_at.isoformat(),
                        "item_count": len(items)
                    },
                    "items": [
                        {
                            "id": item.id,
                            "listing_id": item.listing_id,
                            "status": item.status,
                            "notes": item.notes,
                            "position": item.position,
                            "added_at": item.added_at.isoformat(),
                            "updated_at": item.updated_at.isoformat(),
                            "listing": {
                                "name": item.listing.name if hasattr(item, 'listing') and item.listing else None,
                                "price": float(item.listing.price) if hasattr(item, 'listing') and item.listing else None,
                                "cpu": item.listing.cpu.model if hasattr(item, 'listing') and item.listing and item.listing.cpu else None,
                                "gpu": item.listing.gpu.model if hasattr(item, 'listing') and item.listing and item.listing.gpu else None,
                                "cpu_mark_ratio": float(item.listing.cpu_mark_ratio) if hasattr(item, 'listing') and item.listing and item.listing.cpu_mark_ratio else None,
                                "score": float(item.listing.overall_score) if hasattr(item, 'listing') and item.listing and item.listing.overall_score else None
                            } if hasattr(item, 'listing') else None
                        }
                        for item in items
                    ]
                }

                logger.info(
                    f"Collection exported as JSON: id={collection_id}, "
                    f"user={current_user.user_id}, "
                    f"items={len(items)}"
                )

                # Return JSON file
                return Response(
                    content=json.dumps(export_data, indent=2),
                    media_type="application/json",
                    headers={
                        "Content-Disposition": f'attachment; filename="collection_{collection_id}.json"'
                    }
                )

        except PermissionError as e:
            # Not owner
            logger.warning(f"Permission denied for collection {collection_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )


__all__ = ["router"]
