"""Repository for ListingShare and UserShare CRUD operations.

This module provides the data access layer for deal sharing features including:
- Public listing shares with token-based access
- User-to-user deal sharing with expiry and tracking
- View count tracking and share status management
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.sharing import ListingShare, UserShare


class ShareRepository:
    """Repository for managing listing shares and user shares.

    Handles all database operations for shares with:
    - Token-based access control
    - Expiry validation and cleanup
    - View and import tracking
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

    # ==================== ListingShare Methods ====================

    async def create_listing_share(
        self,
        listing_id: int,
        created_by: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> ListingShare:
        """Create a new public listing share.

        Generates a unique share token and creates a shareable link for the listing.
        If no expiry is provided, the share will never expire.

        Args:
            listing_id: ID of listing to share
            created_by: Optional user ID who created the share
            expires_at: Optional expiry datetime (None = never expires)

        Returns:
            ListingShare: Created share instance with token and timestamps
        """
        # Generate unique token
        share_token = ListingShare.generate_token()

        # Create share instance
        share = ListingShare(
            listing_id=listing_id,
            created_by=created_by,
            share_token=share_token,
            expires_at=expires_at,
            view_count=0,
        )

        # Add to session and flush to get ID
        self.session.add(share)
        await self.session.flush()

        # Refresh to get created_at from database
        await self.session.refresh(share)

        return share

    async def get_listing_share_by_token(self, token: str) -> ListingShare | None:
        """Get listing share by token, including expired shares.

        This method retrieves shares regardless of expiry status.
        Use get_active_listing_share_by_token() to filter out expired shares.

        Args:
            token: Share token to look up

        Returns:
            ListingShare instance if found, None otherwise
        """
        # Eager load listing with all relationships to prevent N+1 queries
        listing_loader = joinedload(ListingShare.listing)
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(ListingShare)
            .options(
                listing_loader,
                joinedload(ListingShare.creator)
            )
            .where(ListingShare.share_token == token)
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_active_listing_share_by_token(self, token: str) -> ListingShare | None:
        """Get listing share by token, only if not expired.

        Validates expiry and returns None for expired shares.

        Args:
            token: Share token to look up

        Returns:
            ListingShare instance if found and active, None if expired or not found
        """
        # Eager load listing with all relationships to prevent N+1 queries
        listing_loader = joinedload(ListingShare.listing)
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(ListingShare)
            .options(
                listing_loader,
                joinedload(ListingShare.creator)
            )
            .where(
                and_(
                    ListingShare.share_token == token,
                    or_(
                        ListingShare.expires_at.is_(None),  # Never expires
                        ListingShare.expires_at > datetime.utcnow(),  # Not expired
                    ),
                )
            )
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def increment_view_count(self, share_id: int) -> None:
        """Increment view count for a listing share.

        Uses atomic update to avoid race conditions.

        Args:
            share_id: ID of share to increment
        """
        stmt = (
            update(ListingShare)
            .where(ListingShare.id == share_id)
            .values(view_count=ListingShare.view_count + 1)
        )

        await self.session.execute(stmt)
        await self.session.flush()

    async def find_expired_listing_shares(self, limit: int = 100) -> list[ListingShare]:
        """Find expired listing shares for cleanup.

        Used by scheduled tasks to clean up expired shares.

        Args:
            limit: Maximum number of expired shares to return

        Returns:
            List of expired ListingShare instances
        """
        stmt = (
            select(ListingShare)
            .where(
                and_(
                    ListingShare.expires_at.isnot(None),
                    ListingShare.expires_at <= datetime.utcnow(),
                )
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ==================== UserShare Methods ====================

    async def create_user_share(
        self,
        sender_id: int,
        recipient_id: int,
        listing_id: int,
        message: Optional[str] = None,
        expires_in_days: int = 30,
    ) -> UserShare:
        """Create a new user-to-user share.

        Args:
            sender_id: User ID of sender
            recipient_id: User ID of recipient
            listing_id: ID of listing to share
            message: Optional message from sender
            expires_in_days: Number of days until expiry (default: 30)

        Returns:
            UserShare: Created share instance with token and expiry
        """
        # Generate unique token
        share_token = UserShare.generate_token()

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Create share instance
        share = UserShare(
            sender_id=sender_id,
            recipient_id=recipient_id,
            listing_id=listing_id,
            share_token=share_token,
            message=message,
            expires_at=expires_at,
        )

        # Add to session and flush to get ID
        self.session.add(share)
        await self.session.flush()

        # Refresh to get timestamps from database
        await self.session.refresh(share)

        return share

    async def get_user_share_by_token(self, token: str) -> UserShare | None:
        """Get user share by token.

        Retrieves share with eager loading of sender, recipient, and listing.

        Args:
            token: Share token to look up

        Returns:
            UserShare instance if found, None otherwise
        """
        # Eager load listing with all relationships to prevent N+1 queries
        listing_loader = joinedload(UserShare.listing)
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(UserShare)
            .options(
                joinedload(UserShare.sender),
                joinedload(UserShare.recipient),
                listing_loader
            )
            .where(UserShare.share_token == token)
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_share_by_id(self, share_id: int) -> UserShare | None:
        """Get user share by ID.

        Retrieves share with eager loading of sender, recipient, and listing.

        Args:
            share_id: UserShare ID to look up

        Returns:
            UserShare instance if found, None otherwise
        """
        # Eager load listing with all relationships to prevent N+1 queries
        listing_loader = joinedload(UserShare.listing)
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(UserShare)
            .options(
                joinedload(UserShare.sender),
                joinedload(UserShare.recipient),
                listing_loader
            )
            .where(UserShare.id == share_id)
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_received_shares(
        self,
        user_id: int,
        include_expired: bool = False,
        include_imported: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserShare]:
        """Get shares received by user with filtering.

        Args:
            user_id: Recipient user ID
            include_expired: If False, exclude expired shares
            include_imported: If False, exclude imported shares
            limit: Maximum number of shares to return
            offset: Number of shares to skip for pagination

        Returns:
            List of UserShare instances ordered by shared_at (newest first)
        """
        conditions = [UserShare.recipient_id == user_id]

        # Filter expired shares
        if not include_expired:
            conditions.append(UserShare.expires_at > datetime.utcnow())

        # Filter imported shares
        if not include_imported:
            conditions.append(UserShare.imported_at.is_(None))

        # Eager load listing with all relationships to prevent N+1 queries
        listing_loader = joinedload(UserShare.listing)
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(UserShare)
            .options(
                joinedload(UserShare.sender),
                listing_loader
            )
            .where(and_(*conditions))
            .order_by(UserShare.shared_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_user_sent_shares(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[UserShare]:
        """Get shares sent by user.

        Args:
            user_id: Sender user ID
            limit: Maximum number of shares to return
            offset: Number of shares to skip for pagination

        Returns:
            List of UserShare instances ordered by shared_at (newest first)
        """
        # Eager load listing with all relationships to prevent N+1 queries
        listing_loader = joinedload(UserShare.listing)
        listing_loader.joinedload("cpu")
        listing_loader.joinedload("gpu")
        listing_loader.joinedload("ports_profile")
        listing_loader.joinedload("active_profile")
        listing_loader.joinedload("ruleset")
        listing_loader.joinedload("ram_spec")
        listing_loader.joinedload("primary_storage_profile")
        listing_loader.joinedload("secondary_storage_profile")

        stmt = (
            select(UserShare)
            .options(
                joinedload(UserShare.recipient),
                listing_loader
            )
            .where(UserShare.sender_id == user_id)
            .order_by(UserShare.shared_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def mark_share_viewed(self, share_id: int) -> None:
        """Mark user share as viewed.

        Sets viewed_at timestamp if not already set.

        Args:
            share_id: ID of share to mark as viewed
        """
        stmt = (
            update(UserShare)
            .where(
                and_(
                    UserShare.id == share_id,
                    UserShare.viewed_at.is_(None),  # Only update if not already viewed
                )
            )
            .values(viewed_at=datetime.utcnow())
        )

        await self.session.execute(stmt)
        await self.session.flush()

    async def mark_share_imported(self, share_id: int) -> None:
        """Mark user share as imported to collection.

        Sets imported_at timestamp if not already set.

        Args:
            share_id: ID of share to mark as imported
        """
        stmt = (
            update(UserShare)
            .where(
                and_(
                    UserShare.id == share_id,
                    UserShare.imported_at.is_(None),  # Only update if not already imported
                )
            )
            .values(imported_at=datetime.utcnow())
        )

        await self.session.execute(stmt)
        await self.session.flush()

    async def find_expired_user_shares(self, limit: int = 100) -> list[UserShare]:
        """Find expired user shares for cleanup.

        Used by scheduled tasks to clean up expired shares.

        Args:
            limit: Maximum number of expired shares to return

        Returns:
            List of expired UserShare instances
        """
        stmt = select(UserShare).where(UserShare.expires_at <= datetime.utcnow()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
