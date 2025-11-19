"""Business logic for managing collections.

This module provides the service layer for deal collections including:
- Collection CRUD with ownership validation
- Collection item management with status tracking
- Filtering, sorting, and querying
- Position-based ordering for drag-and-drop
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sharing import Collection, CollectionItem
from ..repositories.collection_repository import CollectionRepository

logger = logging.getLogger(__name__)


# Valid status values (matching database check constraint)
VALID_STATUSES = {"undecided", "shortlisted", "rejected", "bought"}

# Valid visibility values (matching database check constraint)
VALID_VISIBILITIES = {"private", "unlisted", "public"}


class CollectionsService:
    """Business logic for managing collections.

    Provides high-level operations for:
    - Creating and managing collections
    - Adding, updating, and removing items
    - Filtering and sorting collection items
    - Ownership validation and access control

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.collection_repo = CollectionRepository(session)

    # ==================== Collection CRUD ====================

    async def create_collection(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        visibility: str = "private",
    ) -> Collection:
        """Create new collection.

        Args:
            user_id: User ID who owns the collection
            name: Collection name (1-100 chars)
            description: Optional description
            visibility: Visibility setting (private, unlisted, public)

        Returns:
            Created Collection

        Raises:
            ValueError: If name is invalid or visibility is invalid

        Example:
            collection = await service.create_collection(
                user_id=1,
                name="Gaming PCs",
                description="Best deals on gaming builds",
                visibility="private"
            )
        """
        # 1. Validate name
        if not name or len(name) < 1 or len(name) > 100:
            raise ValueError("Collection name must be 1-100 characters")

        # 2. Validate visibility
        if visibility not in VALID_VISIBILITIES:
            raise ValueError(f"Visibility must be one of: {', '.join(VALID_VISIBILITIES)}")

        # 3. Create via repository
        collection = await self.collection_repo.create_collection(
            user_id=user_id, name=name, description=description, visibility=visibility
        )

        await self.session.commit()

        logger.info(f"Created collection {collection.id} '{name}' for user {user_id}")

        return collection

    async def get_collection(
        self, collection_id: int, user_id: int, load_items: bool = True
    ) -> Optional[Collection]:
        """Get collection by ID with ownership check.

        Args:
            collection_id: Collection ID
            user_id: User ID (must be owner)
            load_items: Whether to eager load items (default: True)

        Returns:
            Collection if found and owned by user, None otherwise

        Raises:
            PermissionError: If user doesn't own the collection

        Example:
            collection = await service.get_collection(
                collection_id=5,
                user_id=1
            )
            if collection:
                print(f"Collection has {len(collection.items)} items")
        """
        # 1. Get collection via repository
        collection = await self.collection_repo.get_collection_by_id(
            collection_id=collection_id, load_items=load_items
        )

        # 2. If not found
        if not collection:
            return None

        # 3. Verify ownership
        if collection.user_id != user_id:
            raise PermissionError(f"User {user_id} does not own collection {collection_id}")

        return collection

    async def update_collection(
        self,
        collection_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Optional[Collection]:
        """Update collection metadata.

        Args:
            collection_id: Collection ID
            user_id: User ID (must be owner)
            name: New name (optional)
            description: New description (optional)
            visibility: New visibility (optional)

        Returns:
            Updated Collection or None if not found

        Raises:
            PermissionError: If user doesn't own the collection
            ValueError: If name or visibility is invalid

        Example:
            collection = await service.update_collection(
                collection_id=5,
                user_id=1,
                name="Best Gaming PCs",
                visibility="public"
            )
        """
        # 1. Verify ownership
        collection = await self.get_collection(
            collection_id=collection_id, user_id=user_id, load_items=False
        )

        if not collection:
            return None

        # 2. Validate inputs
        if name is not None:
            if len(name) < 1 or len(name) > 100:
                raise ValueError("Collection name must be 1-100 characters")

        if visibility is not None:
            if visibility not in VALID_VISIBILITIES:
                raise ValueError(f"Visibility must be one of: {', '.join(VALID_VISIBILITIES)}")

        # 3. Update via repository
        updated = await self.collection_repo.update_collection(
            collection_id=collection_id,
            user_id=user_id,
            name=name,
            description=description,
            visibility=visibility,
        )

        await self.session.commit()

        logger.info(f"Updated collection {collection_id} by user {user_id}")

        return updated

    async def delete_collection(self, collection_id: int, user_id: int) -> bool:
        """Delete collection (cascade deletes items).

        Args:
            collection_id: Collection ID
            user_id: User ID (must be owner)

        Returns:
            True if deleted, False if not found

        Raises:
            PermissionError: If user doesn't own the collection

        Example:
            success = await service.delete_collection(
                collection_id=5,
                user_id=1
            )
        """
        # 1. Verify ownership
        collection = await self.get_collection(
            collection_id=collection_id, user_id=user_id, load_items=False
        )

        if not collection:
            return False

        # 2. Delete via repository
        deleted = await self.collection_repo.delete_collection(collection_id, user_id)

        await self.session.commit()

        logger.info(
            f"Deleted collection {collection_id} by user {user_id} " f"(cascade deleted items)"
        )

        return deleted

    async def list_user_collections(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Collection]:
        """List all user's collections.

        Args:
            user_id: User ID
            limit: Maximum number of collections to return
            offset: Number of collections to skip (pagination)

        Returns:
            List of collections ordered by created_at (newest first)

        Example:
            collections = await service.list_user_collections(
                user_id=1,
                limit=20
            )
            for c in collections:
                print(f"{c.name}: {len(c.items)} items")
        """
        collections = await self.collection_repo.find_user_collections(
            user_id=user_id, limit=limit, offset=offset
        )

        return collections

    # ==================== Item Management ====================

    async def add_item_to_collection(
        self,
        collection_id: int,
        listing_id: int,
        user_id: int,
        status: str = "undecided",
        notes: Optional[str] = None,
        position: Optional[int] = None,
    ) -> CollectionItem:
        """Add item to collection with deduplication.

        Args:
            collection_id: Collection ID
            listing_id: Listing ID to add
            user_id: User ID (must be collection owner)
            status: Item status (default: undecided)
            notes: Optional notes
            position: Optional position (auto-generated if None)

        Returns:
            Created CollectionItem

        Raises:
            PermissionError: If user doesn't own the collection
            ValueError: If item already exists or status invalid

        Example:
            item = await service.add_item_to_collection(
                collection_id=5,
                listing_id=123,
                user_id=1,
                status="shortlisted",
                notes="Great deal on this one"
            )
        """
        # 1. Verify collection ownership
        collection = await self.get_collection(
            collection_id=collection_id, user_id=user_id, load_items=False
        )

        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        # 2. Validate listing exists
        from ..models.listings import Listing
        from sqlalchemy import select

        result = await self.session.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # 3. Validate status
        if status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")

        # 4. Check for duplicates
        exists = await self.collection_repo.check_item_exists(
            collection_id=collection_id, listing_id=listing_id
        )

        if exists:
            raise ValueError(f"Listing {listing_id} already exists in collection {collection_id}")

        # 5. Add item via repository
        item = await self.collection_repo.add_item(
            collection_id=collection_id,
            listing_id=listing_id,
            status=status,
            notes=notes,
            position=position,
        )

        await self.session.commit()

        logger.info(
            f"Added listing {listing_id} to collection {collection_id} " f"by user {user_id}"
        )

        return item

    async def update_collection_item(
        self,
        item_id: int,
        user_id: int,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Optional[CollectionItem]:
        """Update collection item.

        Args:
            item_id: CollectionItem ID
            user_id: User ID (must be collection owner)
            status: New status (optional)
            notes: New notes (optional)
            position: New position (optional)

        Returns:
            Updated CollectionItem or None if not found

        Raises:
            PermissionError: If user doesn't own the collection
            ValueError: If status is invalid

        Example:
            item = await service.update_collection_item(
                item_id=10,
                user_id=1,
                status="bought",
                notes="Purchased on 2025-11-17"
            )
        """
        # 1. Get item and verify collection ownership
        from sqlalchemy import select

        result = await self.session.execute(
            select(CollectionItem).where(CollectionItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Verify collection ownership
        collection = await self.get_collection(
            collection_id=item.collection_id, user_id=user_id, load_items=False
        )

        if not collection:
            raise PermissionError(f"User {user_id} does not own collection {item.collection_id}")

        # 2. Validate status if provided
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")

        # 3. Update via repository
        updated = await self.collection_repo.update_item(
            item_id=item_id, status=status, notes=notes, position=position
        )

        await self.session.commit()

        logger.info(f"Updated collection item {item_id} by user {user_id}")

        return updated

    async def remove_item_from_collection(self, item_id: int, user_id: int) -> bool:
        """Remove item from collection.

        Args:
            item_id: CollectionItem ID
            user_id: User ID (must be collection owner)

        Returns:
            True if removed, False if not found

        Raises:
            PermissionError: If user doesn't own the collection

        Example:
            success = await service.remove_item_from_collection(
                item_id=10,
                user_id=1
            )
        """
        # 1. Get item and verify collection ownership
        from sqlalchemy import select

        result = await self.session.execute(
            select(CollectionItem).where(CollectionItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return False

        # Verify collection ownership
        collection = await self.get_collection(
            collection_id=item.collection_id, user_id=user_id, load_items=False
        )

        if not collection:
            raise PermissionError(f"User {user_id} does not own collection {item.collection_id}")

        # 2. Remove via repository
        removed = await self.collection_repo.remove_item(item_id)

        await self.session.commit()

        logger.info(f"Removed collection item {item_id} by user {user_id}")

        return removed

    # ==================== Queries & Filtering ====================

    async def get_collection_items(
        self,
        collection_id: int,
        user_id: int,
        status_filter: Optional[str] = None,
        sort_by: str = "position",
    ) -> list[CollectionItem]:
        """Get collection items with optional filtering and sorting.

        Args:
            collection_id: Collection ID
            user_id: User ID (must be collection owner)
            status_filter: Optional status to filter by
            sort_by: Sort key (position, added_at, or custom field)

        Returns:
            List of CollectionItem objects

        Raises:
            PermissionError: If user doesn't own the collection

        Example:
            # Get all items
            items = await service.get_collection_items(
                collection_id=5,
                user_id=1
            )

            # Get only shortlisted items
            shortlisted = await service.get_collection_items(
                collection_id=5,
                user_id=1,
                status_filter="shortlisted"
            )

            # Sort by added date
            recent = await service.get_collection_items(
                collection_id=5,
                user_id=1,
                sort_by="added_at"
            )
        """
        # 1. Verify collection ownership
        collection = await self.get_collection(
            collection_id=collection_id, user_id=user_id, load_items=False
        )

        if not collection:
            raise PermissionError(f"User {user_id} does not own collection {collection_id}")

        # 2. Get items via repository
        items = await self.collection_repo.get_collection_items(
            collection_id=collection_id, load_listings=True
        )

        # 3. Apply status filter if provided
        if status_filter:
            items = [item for item in items if item.status == status_filter]

        # 4. Sort items
        if sort_by == "position":
            # Already sorted by position from repository
            pass
        elif sort_by == "added_at":
            items.sort(key=lambda x: x.added_at, reverse=True)
        else:
            # Custom sorting (e.g., by listing price, score, etc.)
            # For now, default to position
            pass

        return items

    async def get_or_create_default_collection(self, user_id: int) -> Collection:
        """Get user's default collection or create if doesn't exist.

        Looks for a collection named "My Deals" or "Default". If none exists,
        creates a new default collection.

        Args:
            user_id: User ID

        Returns:
            Default Collection

        Example:
            collection = await service.get_or_create_default_collection(user_id=1)
        """
        from sqlalchemy import select

        # Query for default collection
        result = await self.session.execute(
            select(Collection)
            .where(Collection.user_id == user_id, Collection.name.in_(["My Deals", "Default"]))
            .limit(1)
        )
        collection = result.scalar_one_or_none()

        if collection:
            return collection

        # Create default collection
        collection = await self.collection_repo.create_collection(
            user_id=user_id,
            name="My Deals",
            description="Default collection for saved deals",
            visibility="private",
        )

        await self.session.commit()

        logger.info(f"Created default collection for user {user_id}")

        return collection
