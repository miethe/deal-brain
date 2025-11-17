"""Repository for Collection and CollectionItem CRUD operations.

This module provides the data access layer for deal collections including:
- Collection CRUD with ownership validation
- Collection item management with deduplication
- Position-based ordering for drag-and-drop support
- Query optimization with eager loading
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.sharing import Collection, CollectionItem


class CollectionRepository:
    """Repository for managing collections and collection items.

    Handles all database operations for collections with:
    - Ownership validation and access control
    - Item deduplication within collections
    - Position management for ordering
    - Query optimization with eager loading

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    # ==================== Collection CRUD ====================

    async def create_collection(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        visibility: str = "private"
    ) -> Collection:
        """Create a new collection.

        Args:
            user_id: Owner user ID
            name: Collection name (1-100 characters)
            description: Optional collection description
            visibility: Visibility setting ('private', 'unlisted', 'public')

        Returns:
            Collection: Created collection instance with ID and timestamps
        """
        # Create collection instance
        collection = Collection(
            user_id=user_id,
            name=name,
            description=description,
            visibility=visibility
        )

        # Add to session and flush to get ID
        self.session.add(collection)
        await self.session.flush()

        # Refresh to get timestamps from database
        await self.session.refresh(collection)

        return collection

    async def get_collection_by_id(
        self,
        collection_id: int,
        user_id: Optional[int] = None,
        load_items: bool = False
    ) -> Optional[Collection]:
        """Get collection by ID with optional ownership check and item loading.

        Args:
            collection_id: Collection ID to retrieve
            user_id: Optional user ID for ownership validation
            load_items: If True, eager load collection items and listings

        Returns:
            Collection instance if found and accessible, None otherwise
        """
        # Build query with optional eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            options.append(
                selectinload(Collection.items).joinedload(CollectionItem.listing)
            )

        stmt = (
            select(Collection)
            .options(*options)
            .where(Collection.id == collection_id)
        )

        result = await self.session.execute(stmt)
        collection = result.unique().scalar_one_or_none()

        if not collection:
            return None

        # Apply ownership check if user_id provided
        if user_id is not None and collection.user_id != user_id:
            return None  # Access denied

        return collection

    async def update_collection(
        self,
        collection_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[str] = None
    ) -> Optional[Collection]:
        """Update collection metadata.

        Validates ownership before allowing updates. Only the collection owner can update.

        Args:
            collection_id: Collection ID to update
            user_id: User ID for ownership validation
            name: Optional new name
            description: Optional new description
            visibility: Optional new visibility setting

        Returns:
            Updated Collection instance

        Raises:
            ValueError: If collection not found or access denied
        """
        # Get collection with ownership check
        collection = await self.get_collection_by_id(collection_id, user_id)

        if not collection:
            raise ValueError(f"Collection {collection_id} not found or access denied")

        # Update fields if provided
        if name is not None:
            collection.name = name
        if description is not None:
            collection.description = description
        if visibility is not None:
            collection.visibility = visibility

        # Flush changes to database
        await self.session.flush()

        return collection

    async def delete_collection(self, collection_id: int, user_id: int) -> bool:
        """Delete collection (cascade deletes items).

        Validates ownership before deleting. All items in the collection are also deleted
        due to cascade delete configuration.

        Args:
            collection_id: Collection ID to delete
            user_id: User ID for ownership validation

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If collection not found or access denied
        """
        # Get collection with ownership check
        collection = await self.get_collection_by_id(collection_id, user_id)

        if not collection:
            raise ValueError(f"Collection {collection_id} not found or access denied")

        # Delete collection (items cascade deleted automatically)
        await self.session.delete(collection)
        await self.session.flush()

        return True

    async def find_user_collections(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        load_items: bool = False
    ) -> list[Collection]:
        """Find all collections for a user with pagination.

        Args:
            user_id: Owner user ID
            limit: Maximum number of collections to return
            offset: Number of collections to skip for pagination
            load_items: If True, eager load collection items

        Returns:
            List of Collection instances ordered by created_at (newest first)
        """
        # Build query with optional eager loading
        options = []

        if load_items:
            options.append(
                selectinload(Collection.items).joinedload(CollectionItem.listing)
            )

        stmt = (
            select(Collection)
            .options(*options)
            .where(Collection.user_id == user_id)
            .order_by(Collection.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    # ==================== Collection Item Methods ====================

    async def add_item(
        self,
        collection_id: int,
        listing_id: int,
        status: str = "undecided",
        notes: Optional[str] = None,
        position: Optional[int] = None
    ) -> CollectionItem:
        """Add item to collection with deduplication.

        Checks if listing already exists in collection before adding.

        Args:
            collection_id: Collection ID to add item to
            listing_id: Listing ID to add
            status: Item status ('undecided', 'shortlisted', 'rejected', 'bought')
            notes: Optional user notes
            position: Optional position value (auto-generated if not provided)

        Returns:
            CollectionItem: Created item instance

        Raises:
            ValueError: If listing already exists in collection
        """
        # Check for duplicates
        exists = await self.check_item_exists(collection_id, listing_id)
        if exists:
            raise ValueError(
                f"Listing {listing_id} already exists in collection {collection_id}"
            )

        # Get next position if not provided
        if position is None:
            position = await self.get_next_position(collection_id)

        # Create item instance
        item = CollectionItem(
            collection_id=collection_id,
            listing_id=listing_id,
            status=status,
            notes=notes,
            position=position
        )

        # Add to session and flush to get ID
        self.session.add(item)
        await self.session.flush()

        # Refresh to get timestamps from database
        await self.session.refresh(item)

        return item

    async def update_item(
        self,
        item_id: int,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        position: Optional[int] = None
    ) -> Optional[CollectionItem]:
        """Update collection item.

        Args:
            item_id: Item ID to update
            status: Optional new status
            notes: Optional new notes
            position: Optional new position

        Returns:
            Updated CollectionItem instance, None if not found
        """
        # Get item
        stmt = select(CollectionItem).where(CollectionItem.id == item_id)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Update fields if provided
        if status is not None:
            item.status = status
        if notes is not None:
            item.notes = notes
        if position is not None:
            item.position = position

        # Flush changes to database
        await self.session.flush()

        return item

    async def remove_item(self, item_id: int) -> bool:
        """Remove item from collection.

        Args:
            item_id: Item ID to remove

        Returns:
            True if deleted successfully, False if not found
        """
        # Get item
        stmt = select(CollectionItem).where(CollectionItem.id == item_id)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return False

        # Delete item
        await self.session.delete(item)
        await self.session.flush()

        return True

    async def get_collection_items(
        self,
        collection_id: int,
        load_listings: bool = True
    ) -> list[CollectionItem]:
        """Get all items in collection with optional listing data.

        Args:
            collection_id: Collection ID to get items from
            load_listings: If True, eager load listing data

        Returns:
            List of CollectionItem instances ordered by position
        """
        # Build query with optional eager loading
        options = []

        if load_listings:
            options.append(joinedload(CollectionItem.listing))

        stmt = (
            select(CollectionItem)
            .options(*options)
            .where(CollectionItem.collection_id == collection_id)
            .order_by(CollectionItem.position.asc().nullsfirst())
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def check_item_exists(
        self,
        collection_id: int,
        listing_id: int
    ) -> bool:
        """Check if listing already exists in collection.

        Args:
            collection_id: Collection ID to check
            listing_id: Listing ID to check

        Returns:
            True if listing exists in collection, False otherwise
        """
        stmt = select(CollectionItem).where(
            and_(
                CollectionItem.collection_id == collection_id,
                CollectionItem.listing_id == listing_id
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_next_position(self, collection_id: int) -> int:
        """Get next available position value for new item.

        Calculates max(position) + 1 for the collection.
        Returns 0 if collection is empty.

        Args:
            collection_id: Collection ID to get next position for

        Returns:
            Next position value
        """
        stmt = select(func.max(CollectionItem.position)).where(
            CollectionItem.collection_id == collection_id
        )

        result = await self.session.execute(stmt)
        max_position = result.scalar_one_or_none()

        # Return 0 if collection is empty, otherwise max + 1
        return 0 if max_position is None else max_position + 1
