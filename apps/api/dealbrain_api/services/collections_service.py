"""Business logic for managing collections.

This module provides the service layer for deal collections including:
- Collection CRUD with ownership validation
- Collection item management with status tracking
- Filtering, sorting, and querying
- Position-based ordering for drag-and-drop
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sharing import Collection, CollectionItem, CollectionShareToken
from ..repositories.collection_repository import CollectionRepository
from ..repositories.collection_share_token_repository import CollectionShareTokenRepository
from ..settings import get_settings

logger = logging.getLogger(__name__)
analytics_logger = logging.getLogger("dealbrain.analytics")


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
        self.share_token_repo = CollectionShareTokenRepository(session)

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

    # ==================== Visibility Management (Task 2a-svc-1) ====================

    async def update_visibility(
        self,
        collection_id: int,
        new_visibility: str,
        user_id: int
    ) -> Optional[Collection]:
        """Update collection visibility with authorization check.

        Validates state transitions and emits telemetry event on success.
        All transitions are allowed: private ↔ unlisted ↔ public

        Args:
            collection_id: Collection ID
            new_visibility: New visibility setting (private, unlisted, public)
            user_id: User ID (must be owner)

        Returns:
            Updated Collection or None if not found

        Raises:
            PermissionError: If user doesn't own the collection
            ValueError: If visibility value is invalid

        Example:
            collection = await service.update_visibility(
                collection_id=5,
                new_visibility="public",
                user_id=1
            )
        """
        # 1. Validate new visibility value
        if new_visibility not in VALID_VISIBILITIES:
            raise ValueError(
                f"Visibility must be one of: {', '.join(VALID_VISIBILITIES)}"
            )

        # 2. Get collection with ownership check
        collection = await self.get_collection(
            collection_id=collection_id,
            user_id=user_id,
            load_items=False
        )

        if not collection:
            return None

        # 3. Store old visibility for telemetry
        old_visibility = collection.visibility

        # 4. Update visibility via repository
        updated = await self.collection_repo.update_collection(
            collection_id=collection_id,
            user_id=user_id,
            visibility=new_visibility
        )

        await self.session.commit()

        # 5. Emit telemetry event
        self._emit_event(
            "collection.visibility_changed",
            {
                "collection_id": collection_id,
                "user_id": user_id,
                "old_visibility": old_visibility,
                "new_visibility": new_visibility,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Updated collection {collection_id} visibility: {old_visibility} → {new_visibility}"
        )

        return updated

    async def get_public_collection(
        self,
        collection_id: int,
        load_items: bool = True
    ) -> Optional[Collection]:
        """Get public collection without authentication.

        Only returns collections with visibility='public'.
        No ownership check required.

        Args:
            collection_id: Collection ID
            load_items: Whether to eager load items (default: True)

        Returns:
            Collection if found and public, None otherwise

        Example:
            collection = await service.get_public_collection(
                collection_id=5
            )
            if collection:
                print(f"Public collection: {collection.name}")
        """
        # Get collection without user_id check
        collection = await self.collection_repo.get_collection_by_id(
            collection_id=collection_id,
            user_id=None,
            load_items=load_items
        )

        # Only return if public
        if collection and collection.visibility == "public":
            return collection

        return None

    async def check_access(
        self,
        collection_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """Check if user can access collection.

        Access is granted if:
        - Collection is public (anyone can access)
        - Collection is unlisted (anyone with link can access)
        - User owns the collection (regardless of visibility)

        Args:
            collection_id: Collection ID
            user_id: Optional user ID to check ownership

        Returns:
            True if user can access collection, False otherwise

        Example:
            # Check anonymous access
            can_access = await service.check_access(collection_id=5)

            # Check user access
            can_access = await service.check_access(
                collection_id=5,
                user_id=1
            )
        """
        # Get collection without ownership filter
        collection = await self.collection_repo.get_collection_by_id(
            collection_id=collection_id,
            user_id=None,
            load_items=False
        )

        if not collection:
            return False

        # Grant access if:
        # 1. Collection is public or unlisted (anyone can access)
        if collection.visibility in ("public", "unlisted"):
            return True

        # 2. User owns the collection
        if user_id and collection.user_id == user_id:
            return True

        # 3. Otherwise deny access
        return False

    # ==================== Collection Copying (Task 2a-svc-2) ====================

    async def copy_collection(
        self,
        source_collection_id: int,
        user_id: int,
        new_name: Optional[str] = None
    ) -> Collection:
        """Copy collection to user's workspace.

        Creates a new private collection with all items from the source.
        Items are copied with their notes and status, and valuation snapshots
        are created for each item.

        Args:
            source_collection_id: Source collection ID to copy from
            user_id: User ID who will own the new collection
            new_name: Optional name for new collection (default: "Copy of [original name]")

        Returns:
            Newly created Collection with all items

        Raises:
            ValueError: If source collection not found or not accessible
            PermissionError: If user cannot access source collection

        Example:
            new_collection = await service.copy_collection(
                source_collection_id=5,
                user_id=2,
                new_name="My Gaming Deals"
            )
            print(f"Copied {len(new_collection.items)} items")
        """
        # 1. Get source collection (check access)
        source = await self.collection_repo.get_collection_by_id(
            collection_id=source_collection_id,
            user_id=None,
            load_items=True
        )

        if not source:
            raise ValueError(f"Collection {source_collection_id} not found")

        # 2. Check if user can access source collection
        can_access = await self.check_access(
            collection_id=source_collection_id,
            user_id=user_id
        )

        if not can_access:
            raise PermissionError(
                f"User {user_id} cannot access collection {source_collection_id}"
            )

        # 3. Generate new name if not provided
        if new_name is None:
            new_name = f"Copy of {source.name}"

        # 4. Create new collection (always private)
        new_collection = await self.collection_repo.create_collection(
            user_id=user_id,
            name=new_name,
            description=source.description,
            visibility="private"
        )

        # 5. Copy all items with their notes and status
        from ..models.listings import Listing

        for item in source.items:
            # Get listing to create valuation snapshot
            result = await self.session.execute(
                select(Listing).where(Listing.id == item.listing_id)
            )
            listing = result.scalar_one_or_none()

            if listing:
                # Add item to new collection
                await self.collection_repo.add_item(
                    collection_id=new_collection.id,
                    listing_id=item.listing_id,
                    status=item.status,
                    notes=item.notes,
                    position=item.position
                )

        await self.session.commit()

        # 6. Refresh to get all items
        await self.session.refresh(new_collection)

        # 7. Emit telemetry event
        self._emit_event(
            "collection.copied",
            {
                "source_collection_id": source_collection_id,
                "new_collection_id": new_collection.id,
                "user_id": user_id,
                "item_count": len(source.items),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        logger.info(
            f"Copied collection {source_collection_id} to {new_collection.id} "
            f"for user {user_id} ({len(source.items)} items)"
        )

        return new_collection

    # ==================== Collection Discovery (Task 2a-svc-3) ====================

    async def list_public_collections(
        self,
        visibility_filter: str = "public",
        sort_by: str = "recent",
        limit: int = 50,
        offset: int = 0
    ) -> list[Collection]:
        """List public or unlisted collections with pagination and sorting.

        Args:
            visibility_filter: Filter by visibility (public, unlisted)
            sort_by: Sort key (recent=created_at DESC, popular=view_count DESC)
            limit: Maximum number of collections to return
            offset: Number of collections to skip (pagination)

        Returns:
            List of Collection instances

        Example:
            # Get recent public collections
            collections = await service.list_public_collections(
                visibility_filter="public",
                sort_by="recent",
                limit=20
            )
        """
        from sqlalchemy import desc

        # 1. Validate visibility filter
        if visibility_filter not in ("public", "unlisted"):
            raise ValueError("Visibility filter must be 'public' or 'unlisted'")

        # 2. Build query
        stmt = (
            select(Collection)
            .where(Collection.visibility == visibility_filter)
        )

        # 3. Apply sorting
        if sort_by == "recent":
            stmt = stmt.order_by(desc(Collection.created_at))
        elif sort_by == "popular":
            # TODO: Add view_count column to Collection model
            # For now, fallback to created_at
            stmt = stmt.order_by(desc(Collection.created_at))
        else:
            stmt = stmt.order_by(desc(Collection.created_at))

        # 4. Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # 5. Execute query
        result = await self.session.execute(stmt)
        collections = list(result.scalars().all())

        return collections

    async def search_collections(
        self,
        query: str,
        visibility_filter: str = "public",
        limit: int = 50,
        offset: int = 0
    ) -> list[Collection]:
        """Search collections with full-text search.

        Searches collection name and description.

        Args:
            query: Search query string
            visibility_filter: Filter by visibility (public, unlisted)
            limit: Maximum number of collections to return
            offset: Number of collections to skip (pagination)

        Returns:
            List of Collection instances matching search query

        Example:
            collections = await service.search_collections(
                query="gaming",
                visibility_filter="public"
            )
        """
        from sqlalchemy import desc, or_

        # 1. Validate visibility filter
        if visibility_filter not in ("public", "unlisted"):
            raise ValueError("Visibility filter must be 'public' or 'unlisted'")

        # 2. Build search query (case-insensitive LIKE)
        search_pattern = f"%{query}%"

        stmt = (
            select(Collection)
            .where(
                Collection.visibility == visibility_filter,
                or_(
                    Collection.name.ilike(search_pattern),
                    Collection.description.ilike(search_pattern)
                )
            )
            .order_by(desc(Collection.created_at))
            .limit(limit)
            .offset(offset)
        )

        # 3. Execute query
        result = await self.session.execute(stmt)
        collections = list(result.scalars().all())

        # 4. Emit telemetry event
        self._emit_event(
            "collection.discovered",
            {
                "query": query,
                "visibility_filter": visibility_filter,
                "result_count": len(collections),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return collections

    async def filter_by_owner(
        self,
        owner_id: int,
        visibility_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Collection]:
        """Filter collections by creator/owner.

        Args:
            owner_id: User ID of collection owner
            visibility_filter: Optional visibility filter (public, unlisted, private)
            limit: Maximum number of collections to return
            offset: Number of collections to skip (pagination)

        Returns:
            List of Collection instances owned by user

        Example:
            # Get all public collections by user
            collections = await service.filter_by_owner(
                owner_id=1,
                visibility_filter="public"
            )
        """
        from sqlalchemy import desc

        # 1. Build query
        conditions = [Collection.user_id == owner_id]

        if visibility_filter:
            if visibility_filter not in VALID_VISIBILITIES:
                raise ValueError(
                    f"Visibility must be one of: {', '.join(VALID_VISIBILITIES)}"
                )
            conditions.append(Collection.visibility == visibility_filter)

        stmt = (
            select(Collection)
            .where(*conditions)
            .order_by(desc(Collection.created_at))
            .limit(limit)
            .offset(offset)
        )

        # 2. Execute query
        result = await self.session.execute(stmt)
        collections = list(result.scalars().all())

        return collections

    # ==================== Token Management (Task 2a-svc-4) ====================

    async def generate_share_token(
        self,
        collection_id: int,
        user_id: int,
        expires_at: Optional[datetime] = None
    ) -> CollectionShareToken:
        """Generate unique share token for collection.

        Creates a shareable URL token for unlisted or public collections.

        Args:
            collection_id: Collection ID to share
            user_id: User ID (must be owner)
            expires_at: Optional expiry datetime (None = never expires)

        Returns:
            Created CollectionShareToken

        Raises:
            PermissionError: If user doesn't own the collection
            ValueError: If collection is private (cannot be shared)

        Example:
            token = await service.generate_share_token(
                collection_id=5,
                user_id=1,
                expires_at=None
            )
            share_url = f"/collections/shared/{token.token}"
        """
        # 1. Verify ownership
        collection = await self.get_collection(
            collection_id=collection_id,
            user_id=user_id,
            load_items=False
        )

        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        # 2. Validate visibility (private collections cannot be shared via token)
        if collection.visibility == "private":
            raise ValueError(
                "Cannot generate share token for private collection. "
                "Change visibility to 'unlisted' or 'public' first."
            )

        # 3. Generate token via repository
        token = await self.share_token_repo.generate_token(
            collection_id=collection_id,
            expires_at=expires_at
        )

        await self.session.commit()

        logger.info(
            f"Generated share token for collection {collection_id} by user {user_id}"
        )

        return token

    async def validate_share_token(self, token: str) -> Optional[Collection]:
        """Validate share token and return collection.

        Only returns collection if token is valid and not expired.

        Args:
            token: Share token to validate

        Returns:
            Collection if token is valid, None if invalid or expired

        Example:
            collection = await service.validate_share_token(token="abc123...")
            if collection:
                print(f"Valid token for: {collection.name}")
        """
        # Get token with collection loaded (exclude expired by default)
        share_token = await self.share_token_repo.get_by_token(
            token=token,
            include_expired=False
        )

        if not share_token:
            return None

        return share_token.collection

    async def increment_share_views(self, token: str) -> bool:
        """Increment view count for share token.

        Tracks how many times a shared collection has been viewed.

        Args:
            token: Share token to increment

        Returns:
            True if incremented successfully, False if token not found

        Example:
            success = await service.increment_share_views(token="abc123...")
        """
        # Increment view count (atomic operation)
        success = await self.share_token_repo.increment_view_count(token)

        if success:
            await self.session.commit()
            logger.info(f"Incremented view count for token {token[:8]}...")

        return success

    # ==================== Telemetry (Task 2a-svc-5) ====================

    def _emit_event(self, name: str, payload: dict[str, Any]) -> None:
        """Emit telemetry event for analytics.

        Args:
            name: Event name (e.g., "collection.visibility_changed")
            payload: Event payload with context data
        """
        settings = get_settings()
        if settings.analytics_enabled:
            analytics_logger.info("event=%s payload=%s", name, payload)
