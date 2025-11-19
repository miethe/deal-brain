"""Repository for CollectionShareToken CRUD operations.

This module provides the data access layer for collection share token management:
- Token generation with cryptographically secure random values
- Token-based collection access with expiry validation
- View count tracking with atomic updates
- Token expiration (soft-delete) functionality
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.sharing import Collection, CollectionItem, CollectionShareToken


class CollectionShareTokenRepository:
    """Repository for managing collection share tokens.

    Handles all database operations for share tokens with:
    - Secure token generation
    - Expiry validation and soft-delete
    - View count tracking with atomic updates
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

    async def generate_token(
        self,
        collection_id: int,
        expires_at: datetime | None = None
    ) -> CollectionShareToken:
        """Create new share token for collection.

        Generates a cryptographically secure URL-safe token and creates a new
        share token record for the collection. Tokens can optionally have an
        expiry date.

        Args:
            collection_id: ID of collection to create share token for
            expires_at: Optional expiry datetime (None = never expires)

        Returns:
            CollectionShareToken: Created token instance with token string and timestamps
        """
        # Generate unique secure token
        token_string = CollectionShareToken.generate_token()

        # Create share token instance
        share_token = CollectionShareToken(
            collection_id=collection_id,
            token=token_string,
            view_count=0,
            expires_at=expires_at
        )

        # Add to session and flush to get ID
        self.session.add(share_token)
        await self.session.flush()

        # Refresh to get created_at and updated_at from database
        await self.session.refresh(share_token)

        return share_token

    async def get_by_token(
        self,
        token: str,
        include_expired: bool = False
    ) -> CollectionShareToken | None:
        """Get share token by token string with optional expiry filtering.

        Retrieves share token with eager loading of collection and items.
        By default, filters out expired tokens.

        Args:
            token: Share token string to look up
            include_expired: If True, include expired tokens (default: False)

        Returns:
            CollectionShareToken instance if found and valid, None otherwise
        """
        # Build query conditions
        conditions = [CollectionShareToken.token == token]

        # Filter out expired tokens unless explicitly included
        if not include_expired:
            conditions.append(
                or_(
                    CollectionShareToken.expires_at.is_(None),  # Never expires
                    CollectionShareToken.expires_at > datetime.now(timezone.utc)  # Not expired
                )
            )

        # Eager load collection with items and all listing relationships
        collection_loader = joinedload(CollectionShareToken.collection)
        items_loader = selectinload(CollectionShareToken.collection).selectinload(Collection.items)
        listing_loader = items_loader.joinedload(CollectionItem.listing)

        # Load all Listing relationships in one go to prevent N+1 queries
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(CollectionShareToken)
            .options(
                collection_loader,
                items_loader
            )
            .where(and_(*conditions))
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def increment_view_count(self, token: str) -> bool:
        """Increment view count for a share token atomically.

        Uses atomic update operation to safely increment view count even
        with concurrent access. Only increments for non-expired tokens.

        Args:
            token: Share token string to increment view count for

        Returns:
            True if view count was incremented, False if token not found or expired
        """
        stmt = (
            update(CollectionShareToken)
            .where(
                and_(
                    CollectionShareToken.token == token,
                    or_(
                        CollectionShareToken.expires_at.is_(None),  # Never expires
                        CollectionShareToken.expires_at > datetime.now(timezone.utc)  # Not expired
                    )
                )
            )
            .values(view_count=CollectionShareToken.view_count + 1)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        # Return True if a row was updated, False otherwise
        return result.rowcount > 0

    async def expire_token(self, token: str) -> bool:
        """Expire a share token by setting expires_at to current time.

        Implements soft-delete by setting expires_at timestamp. This allows
        maintaining audit trail while preventing future access.

        Args:
            token: Share token string to expire

        Returns:
            True if token was expired, False if token not found or already expired
        """
        stmt = (
            update(CollectionShareToken)
            .where(
                and_(
                    CollectionShareToken.token == token,
                    or_(
                        CollectionShareToken.expires_at.is_(None),  # Never expires
                        CollectionShareToken.expires_at > datetime.now(timezone.utc)  # Not expired
                    )
                )
            )
            .values(expires_at=datetime.now(timezone.utc))
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        # Return True if a row was updated, False otherwise
        return result.rowcount > 0

    async def get_by_collection_id(
        self,
        collection_id: int,
        include_expired: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[CollectionShareToken]:
        """Get all share tokens for a collection with pagination.

        Args:
            collection_id: Collection ID to get tokens for
            include_expired: If True, include expired tokens (default: False)
            limit: Maximum number of tokens to return (default: 50)
            offset: Number of tokens to skip for pagination

        Returns:
            List of CollectionShareToken instances ordered by created_at (newest first)
        """
        # Build query conditions
        conditions = [CollectionShareToken.collection_id == collection_id]

        # Filter out expired tokens unless explicitly included
        if not include_expired:
            conditions.append(
                or_(
                    CollectionShareToken.expires_at.is_(None),  # Never expires
                    CollectionShareToken.expires_at > datetime.now(timezone.utc)  # Not expired
                )
            )

        stmt = (
            select(CollectionShareToken)
            .options(joinedload(CollectionShareToken.collection))
            .where(and_(*conditions))
            .order_by(CollectionShareToken.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def delete_token(self, token: str) -> bool:
        """Hard delete a share token.

        Permanently removes the token from the database. Use expire_token()
        for soft-delete to maintain audit trail.

        Args:
            token: Share token string to delete

        Returns:
            True if deleted successfully, False if not found
        """
        # Get token
        stmt = select(CollectionShareToken).where(CollectionShareToken.token == token)
        result = await self.session.execute(stmt)
        share_token = result.scalar_one_or_none()

        if not share_token:
            return False

        # Delete token
        await self.session.delete(share_token)
        await self.session.flush()

        return True
