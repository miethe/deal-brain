"""Repository for Collection and CollectionItem CRUD operations.

This module provides the data access layer for deal collections including:
- Collection CRUD with ownership validation
- Collection item management with deduplication
- Position-based ordering for drag-and-drop support
- Query optimization with eager loading
"""

from __future__ import annotations

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.sharing import Collection, CollectionItem, CollectionShareToken


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
        visibility: str = "private",
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
            user_id=user_id, name=name, description=description, visibility=visibility
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
            load_items: If True, eager load collection items and listings with all relationships

        Returns:
            Collection instance if found and accessible, None otherwise
        """
        # Build query with optional eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            # Eager load collection items with all listing relationships to prevent N+1 queries
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

        stmt = select(Collection).options(*options).where(Collection.id == collection_id)

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
        visibility: Optional[str] = None,
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
        self, user_id: int, limit: int = 50, offset: int = 0, load_items: bool = False
    ) -> list[Collection]:
        """Find all collections for a user with pagination.

        Args:
            user_id: Owner user ID
            limit: Maximum number of collections to return
            offset: Number of collections to skip for pagination
            load_items: If True, eager load collection items with all relationships

        Returns:
            List of Collection instances ordered by created_at (newest first)
        """
        # Build query with optional eager loading
        options = []

        if load_items:
            # Eager load collection items with all listing relationships to prevent N+1 queries
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

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
        position: Optional[int] = None,
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
            raise ValueError(f"Listing {listing_id} already exists in collection {collection_id}")

        # Get next position if not provided
        if position is None:
            position = await self.get_next_position(collection_id)

        # Create item instance
        item = CollectionItem(
            collection_id=collection_id,
            listing_id=listing_id,
            status=status,
            notes=notes,
            position=position,
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
        position: Optional[int] = None,
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
        load_listings: bool = True,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[CollectionItem]:
        """Get items in collection with optional listing data and pagination.

        Args:
            collection_id: Collection ID to get items from
            load_listings: If True, eager load listing data with all relationships
            limit: Optional maximum number of items to return (None = unlimited)
            offset: Number of items to skip for pagination

        Returns:
            List of CollectionItem instances ordered by position
        """
        # Build query with optional eager loading
        options = []

        if load_listings:
            # Eager load listing with all relationships to prevent N+1 queries
            listing_loader = joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(listing_loader)

        stmt = (
            select(CollectionItem)
            .options(*options)
            .where(CollectionItem.collection_id == collection_id)
            .order_by(CollectionItem.position.asc().nullsfirst())
        )

        # Add pagination if limit is provided
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset > 0:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_collection_items_count(self, collection_id: int) -> int:
        """Get total count of items in a collection.

        Args:
            collection_id: Collection ID to count items from

        Returns:
            Total number of items in collection
        """
        stmt = select(func.count(CollectionItem.id)).where(
            CollectionItem.collection_id == collection_id
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

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
                CollectionItem.listing_id == listing_id,
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

    # ==================== Visibility & Discovery Methods (Phase 2a) ====================

    async def get_by_id_and_visibility(
        self,
        collection_id: int,
        visibility: str,
        user_id: int | None = None,
        load_items: bool = False
    ) -> Collection | None:
        """Get collection by ID with visibility filtering and optional ownership check.

        Access control rules:
        - Public collections: accessible to anyone
        - Unlisted collections: accessible to anyone (but not discoverable)
        - Private collections: only accessible to owner (requires user_id match)

        Args:
            collection_id: Collection ID to retrieve
            visibility: Required visibility level ('private', 'unlisted', 'public')
            user_id: Optional user ID for ownership validation
            load_items: If True, eager load collection items and listings

        Returns:
            Collection instance if found and accessible, None otherwise
        """
        # Build query with optional eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            # Eager load collection items with all listing relationships
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

        stmt = (
            select(Collection)
            .options(*options)
            .where(
                and_(
                    Collection.id == collection_id,
                    Collection.visibility == visibility
                )
            )
        )

        result = await self.session.execute(stmt)
        collection = result.unique().scalar_one_or_none()

        if not collection:
            return None

        # Apply ownership check for private collections
        if visibility == "private" and user_id is not None and collection.user_id != user_id:
            return None  # Access denied

        return collection

    async def list_public(
        self,
        limit: int = 50,
        offset: int = 0,
        load_items: bool = False
    ) -> list[Collection]:
        """List all public collections with pagination.

        Args:
            limit: Maximum number of collections to return (default: 50)
            offset: Number of collections to skip for pagination
            load_items: If True, eager load collection items with all relationships

        Returns:
            List of public Collection instances ordered by created_at (newest first)
        """
        # Build query with optional eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            # Eager load collection items with all listing relationships
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

        stmt = (
            select(Collection)
            .options(*options)
            .where(Collection.visibility == "public")
            .order_by(Collection.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_visibility(
        self,
        visibility: str,
        limit: int = 50,
        offset: int = 0,
        load_items: bool = False
    ) -> list[Collection]:
        """List collections filtered by visibility status with pagination.

        Args:
            visibility: Visibility level to filter by ('private', 'unlisted', 'public')
            limit: Maximum number of collections to return (default: 50)
            offset: Number of collections to skip for pagination
            load_items: If True, eager load collection items with all relationships

        Returns:
            List of Collection instances matching visibility, ordered by created_at (newest first)
        """
        # Build query with optional eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            # Eager load collection items with all listing relationships
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

        stmt = (
            select(Collection)
            .options(*options)
            .where(Collection.visibility == visibility)
            .order_by(Collection.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def count_public_collections(self) -> int:
        """Count total number of public collections.

        Useful for displaying stats and calculating pagination metadata.

        Returns:
            Total count of public collections
        """
        stmt = select(func.count(Collection.id)).where(
            Collection.visibility == "public"
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def discover_collections(
        self,
        search_query: str | None = None,
        sort_by: str = "recent",
        limit: int = 50,
        offset: int = 0,
        load_items: bool = False
    ) -> list[Collection]:
        """Discover public collections with filtering, search, and sorting.

        Main discovery endpoint for browsing public collections. Supports:
        - Full-text search on name and description
        - Sorting by recency (created_at) or popularity (total view_count)
        - Pagination with limit and offset
        - Optional eager loading of collection items

        Uses database indexes for efficient queries:
        - idx_collection_visibility for visibility filtering
        - idx_collection_share_token_collection_id for view count aggregation

        Args:
            search_query: Optional text search on collection name and description
            sort_by: Sort order - 'recent' (default) or 'popular' (by view count)
            limit: Maximum number of collections to return (default: 50)
            offset: Number of collections to skip for pagination
            load_items: If True, eager load collection items with all relationships

        Returns:
            List of public Collection instances matching search criteria
        """
        # Build base query with eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            # Eager load collection items with all listing relationships
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

        # For popularity sorting, we need to aggregate view counts from share tokens
        if sort_by == "popular":
            # Subquery to get total view count per collection
            view_count_subquery = (
                select(
                    CollectionShareToken.collection_id,
                    func.sum(CollectionShareToken.view_count).label("total_views")
                )
                .group_by(CollectionShareToken.collection_id)
                .subquery()
            )

            # Main query with left join to get view counts (collections without tokens get 0)
            stmt = (
                select(Collection)
                .outerjoin(
                    view_count_subquery,
                    Collection.id == view_count_subquery.c.collection_id
                )
                .options(*options)
                .where(Collection.visibility == "public")
            )

            # Add search filter if provided
            if search_query:
                search_pattern = f"%{search_query}%"
                stmt = stmt.where(
                    or_(
                        Collection.name.ilike(search_pattern),
                        Collection.description.ilike(search_pattern)
                    )
                )

            # Order by total views (nulls last for collections with no shares)
            stmt = stmt.order_by(
                case(
                    (view_count_subquery.c.total_views.is_(None), 0),
                    else_=view_count_subquery.c.total_views
                ).desc(),
                Collection.created_at.desc()  # Secondary sort by recency
            )

        else:  # sort_by == "recent" (default)
            # Simple query ordered by created_at
            stmt = (
                select(Collection)
                .options(*options)
                .where(Collection.visibility == "public")
            )

            # Add search filter if provided
            if search_query:
                search_pattern = f"%{search_query}%"
                stmt = stmt.where(
                    or_(
                        Collection.name.ilike(search_pattern),
                        Collection.description.ilike(search_pattern)
                    )
                )

            stmt = stmt.order_by(Collection.created_at.desc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    # ==================== Authorization & Access Control (RLS) ====================

    def can_access_collection(
        self,
        collection: Collection,
        user_id: int | None = None
    ) -> bool:
        """Check if user can access a collection based on visibility and ownership.

        Row Level Security (RLS) rules:
        - Public collections: accessible to everyone (authenticated or not)
        - Unlisted collections: accessible to everyone who has the link
        - Private collections: only accessible to owner

        Args:
            collection: Collection instance to check access for
            user_id: Optional authenticated user ID

        Returns:
            True if user can access collection, False otherwise
        """
        # Public and unlisted collections are accessible to everyone
        if collection.visibility in ("public", "unlisted"):
            return True

        # Private collections require authentication and ownership
        if collection.visibility == "private":
            if user_id is None:
                return False  # Not authenticated
            return collection.user_id == user_id

        # Unknown visibility - deny access
        return False

    async def validate_collection_access(
        self,
        collection_id: int,
        user_id: int | None = None,
        require_ownership: bool = False
    ) -> Collection | None:
        """Validate access to a collection with optional ownership requirement.

        Combines fetching and access validation in a single method. Useful for
        API endpoints that need to verify access before performing operations.

        Args:
            collection_id: Collection ID to validate access for
            user_id: Optional authenticated user ID
            require_ownership: If True, only allow access to collection owner

        Returns:
            Collection instance if access is allowed, None otherwise
        """
        # Fetch collection
        stmt = (
            select(Collection)
            .options(joinedload(Collection.user))
            .where(Collection.id == collection_id)
        )

        result = await self.session.execute(stmt)
        collection = result.unique().scalar_one_or_none()

        if not collection:
            return None  # Not found

        # Check ownership requirement
        if require_ownership:
            if user_id is None or collection.user_id != user_id:
                return None  # Access denied

        # Check general access permissions
        if not self.can_access_collection(collection, user_id):
            return None  # Access denied

        return collection

    async def get_collection_with_access_check(
        self,
        collection_id: int,
        user_id: int | None = None,
        load_items: bool = False
    ) -> Collection | None:
        """Get collection with RLS access validation.

        Combines the functionality of get_collection_by_id with explicit
        access control checks. Enforces visibility-based access rules.

        Args:
            collection_id: Collection ID to retrieve
            user_id: Optional authenticated user ID
            load_items: If True, eager load collection items and listings

        Returns:
            Collection instance if found and accessible, None otherwise
        """
        # Build query with optional eager loading
        options = [joinedload(Collection.user)]

        if load_items:
            # Eager load collection items with all listing relationships
            items_loader = selectinload(Collection.items)
            listing_loader = items_loader.joinedload(CollectionItem.listing)

            # Load all Listing relationships in one go
            listing_loader.joinedload("cpu")
            listing_loader.joinedload("gpu")
            listing_loader.joinedload("ports_profile")
            listing_loader.joinedload("active_profile")
            listing_loader.joinedload("ruleset")
            listing_loader.joinedload("ram_spec")
            listing_loader.joinedload("primary_storage_profile")
            listing_loader.joinedload("secondary_storage_profile")

            options.append(items_loader)

        stmt = (
            select(Collection)
            .options(*options)
            .where(Collection.id == collection_id)
        )

        result = await self.session.execute(stmt)
        collection = result.unique().scalar_one_or_none()

        if not collection:
            return None  # Not found

        # Apply RLS access validation
        if not self.can_access_collection(collection, user_id):
            return None  # Access denied

        return collection
