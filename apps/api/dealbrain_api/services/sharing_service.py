"""Business logic for managing shares.

This module provides the service layer for deal sharing features including:
- Public listing shares with token generation and validation
- User-to-user deal sharing with notifications
- Rate limiting and security controls
- Share status tracking (viewed, imported)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sharing import Collection, CollectionItem, ListingShare, UserShare
from ..repositories.collection_repository import CollectionRepository
from ..repositories.share_repository import ShareRepository
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class SharingService:
    """Business logic for managing shares.

    Provides high-level operations for:
    - Generating shareable links with tokens
    - Validating share tokens and permissions
    - Creating user-to-user shares
    - Tracking share views and imports
    - Enforcing rate limits

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.share_repo = ShareRepository(session)
        self.collection_repo = CollectionRepository(session)
        self.notification_service = NotificationService(session)

    # ==================== ListingShare Methods ====================

    async def generate_listing_share_token(
        self, listing_id: int, user_id: Optional[int] = None, ttl_days: int = 180
    ) -> ListingShare:
        """Generate shareable link for listing.

        Creates a public share token that allows anyone to view the listing
        without authentication. Tokens can have an optional expiry.

        Args:
            listing_id: ID of listing to share
            user_id: Optional user ID who created the share
            ttl_days: Time-to-live in days (0 = never expires)

        Returns:
            Created ListingShare with token

        Raises:
            ValueError: If listing doesn't exist

        Example:
            share = await service.generate_listing_share_token(
                listing_id=123,
                user_id=1,
                ttl_days=30
            )
            print(f"Share URL: /deals/{share.listing_id}/{share.share_token}")
        """
        # 1. Validate listing exists
        from ..models.listings import Listing

        result = await self.session.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # 2. Calculate expiry
        expires_at = None
        if ttl_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)

        # 3. Create share via repository
        share = await self.share_repo.create_listing_share(
            listing_id=listing_id, created_by=user_id, expires_at=expires_at
        )

        await self.session.commit()

        logger.info(
            f"Created listing share {share.id} for listing {listing_id} "
            f"by user {user_id}, expires: {expires_at}"
        )

        return share

    async def validate_listing_share_token(self, token: str) -> tuple[Optional[ListingShare], bool]:
        """Validate share token and return (share, is_valid).

        Checks if the token exists and whether it has expired.

        Args:
            token: Share token to validate

        Returns:
            Tuple of (share, is_valid) where:
            - share: ListingShare if found, None otherwise
            - is_valid: True if share exists and not expired

        Example:
            share, is_valid = await service.validate_listing_share_token(token)
            if is_valid:
                # Show listing
                pass
            elif share:
                # Show "expired" message
                pass
            else:
                # Show 404
                pass
        """
        # 1. Get share by token
        share = await self.share_repo.get_listing_share_by_token(token)

        # 2. If not found
        if not share:
            return (None, False)

        # 3. Check if expired
        is_valid = not share.is_expired()

        return (share, is_valid)

    async def increment_share_view(self, token: str) -> bool:
        """Increment view count for share.

        Atomically increments the view counter if the share is valid
        and not expired.

        Args:
            token: Share token

        Returns:
            True if view count incremented, False if invalid/expired

        Example:
            success = await service.increment_share_view(token)
            if success:
                print("View tracked")
        """
        # 1. Validate token
        share, is_valid = await self.validate_listing_share_token(token)

        # 2. If valid, increment
        if is_valid and share:
            await self.share_repo.increment_view_count(share.id)
            await self.session.commit()
            return True

        return False

    # ==================== UserShare Methods ====================

    async def create_user_share(
        self,
        sender_id: int,
        recipient_id: int,
        listing_id: int,
        message: Optional[str] = None,
        ttl_days: int = 30,
    ) -> UserShare:
        """Share listing with specific user.

        Creates a user-to-user share with optional message. Enforces
        rate limiting (max 10 shares/hour per user).

        Args:
            sender_id: User ID sending the share
            recipient_id: User ID receiving the share
            listing_id: Listing ID to share
            message: Optional message to recipient
            ttl_days: Time-to-live in days (default: 30)

        Returns:
            Created UserShare

        Raises:
            ValueError: If sender, recipient, or listing doesn't exist
            PermissionError: If rate limit exceeded

        Example:
            share = await service.create_user_share(
                sender_id=1,
                recipient_id=2,
                listing_id=123,
                message="Check this out!"
            )
        """
        # 1. Validate sender exists
        from ..models.sharing import User
        from ..models.listings import Listing

        sender_result = await self.session.execute(select(User).where(User.id == sender_id))
        sender = sender_result.scalar_one_or_none()
        if not sender:
            raise ValueError(f"Sender user {sender_id} not found")

        # 2. Validate recipient exists
        recipient_result = await self.session.execute(select(User).where(User.id == recipient_id))
        recipient = recipient_result.scalar_one_or_none()
        if not recipient:
            raise ValueError(f"Recipient user {recipient_id} not found")

        # 3. Validate listing exists
        listing_result = await self.session.execute(select(Listing).where(Listing.id == listing_id))
        listing = listing_result.scalar_one_or_none()
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # 4. Check rate limit
        rate_limit_ok = await self.check_share_rate_limit(sender_id)
        if not rate_limit_ok:
            raise PermissionError(f"User {sender_id} has exceeded share rate limit (10/hour)")

        # 5. Create share via repository (repository calculates expiry)
        share = await self.share_repo.create_user_share(
            sender_id=sender_id,
            recipient_id=recipient_id,
            listing_id=listing_id,
            message=message,
            expires_in_days=ttl_days,
        )

        await self.session.commit()

        logger.info(
            f"Created user share {share.id} from user {sender_id} "
            f"to user {recipient_id} for listing {listing_id}"
        )

        # Create in-app notification for recipient
        try:
            sender_display_name = sender.display_name or sender.username
            listing_name = listing.name if hasattr(listing, 'name') else f"Listing #{listing.id}"

            await self.notification_service.create_share_received_notification(
                recipient_id=recipient_id,
                sender_name=sender_display_name,
                listing_name=listing_name,
                share_id=share.id
            )
            await self.session.commit()

            logger.info(
                f"Created notification for user {recipient_id} "
                f"about share {share.id}"
            )
        except Exception as e:
            # Log error but don't fail share creation
            logger.error(
                f"Failed to create notification for share {share.id}: {e}",
                exc_info=True
            )

        # Trigger async email notification task
        try:
            from ..tasks.notifications import send_share_notification_email
            send_share_notification_email.delay(share.id)

            logger.info(
                f"Queued email notification task for share {share.id}"
            )
        except Exception as e:
            # Log error but don't fail share creation
            logger.error(
                f"Failed to queue email notification for share {share.id}: {e}",
                exc_info=True
            )

        return share

    async def get_user_inbox(
        self,
        user_id: int,
        include_expired: bool = False,
        include_imported: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UserShare]:
        """Get shares received by user.

        Retrieves user's inbox of received shares with optional filtering.

        Args:
            user_id: User ID to get inbox for
            include_expired: Include expired shares (default: False)
            include_imported: Include already imported shares (default: False)
            limit: Maximum number of shares to return
            offset: Number of shares to skip (pagination)

        Returns:
            List of UserShare objects ordered by shared_at (newest first)

        Example:
            # Get unread, active shares
            shares = await service.get_user_inbox(user_id=1, limit=20)

            # Get all shares including expired
            all_shares = await service.get_user_inbox(
                user_id=1,
                include_expired=True,
                include_imported=True
            )
        """
        shares = await self.share_repo.get_user_received_shares(
            user_id=user_id,
            include_expired=include_expired,
            include_imported=include_imported,
            limit=limit,
            offset=offset,
        )

        return shares

    async def mark_share_as_viewed(self, share_id: int, user_id: int) -> bool:
        """Mark user share as viewed.

        Sets the viewed_at timestamp if the user is the recipient.

        Args:
            share_id: UserShare ID
            user_id: User ID (must be recipient)

        Returns:
            True if marked viewed, False if not found or unauthorized

        Raises:
            PermissionError: If user is not the recipient

        Example:
            success = await service.mark_share_as_viewed(
                share_id=123,
                user_id=2
            )
        """
        # 1. Get share
        share = await self.share_repo.get_user_share_by_id(share_id)

        if not share:
            return False

        # 2. Verify user is recipient
        if share.recipient_id != user_id:
            raise PermissionError(f"User {user_id} is not the recipient of share {share_id}")

        # 3. Mark viewed via repository
        await self.share_repo.mark_share_viewed(share_id)
        await self.session.commit()

        logger.info(f"User share {share_id} marked as viewed by user {user_id}")

        return True

    async def import_share_to_collection(
        self, share_token: str, user_id: int, collection_id: Optional[int] = None
    ) -> CollectionItem:
        """Import shared deal to collection.

        Imports a shared listing into a user's collection. If no collection
        is specified, uses or creates a default collection.

        Args:
            share_token: UserShare token
            user_id: User ID (must be recipient)
            collection_id: Optional collection ID (creates default if None)

        Returns:
            Created CollectionItem

        Raises:
            ValueError: If share not found or already imported
            PermissionError: If user is not the recipient

        Example:
            item = await service.import_share_to_collection(
                share_token="abc123...",
                user_id=2,
                collection_id=5
            )
        """
        # 1. Validate share token
        share = await self.share_repo.get_user_share_by_token(share_token)

        if not share:
            raise ValueError(f"Share with token '{share_token}' not found")

        if share.is_expired():
            raise ValueError(f"Share with token '{share_token}' has expired")

        # 2. Verify user is recipient
        if share.recipient_id != user_id:
            raise PermissionError(f"User {user_id} is not the recipient of this share")

        # 3. Get or create collection
        if collection_id is None:
            collection = await self.get_or_create_default_collection(user_id)
            collection_id = collection.id
        else:
            # Verify ownership
            collection = await self.collection_repo.get_collection_by_id(
                collection_id, load_items=False
            )
            if not collection or collection.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own collection {collection_id}")

        # 4. Check for duplicate
        exists = await self.collection_repo.check_item_exists(
            collection_id=collection_id, listing_id=share.listing_id
        )

        if exists:
            raise ValueError(f"Listing {share.listing_id} already in collection {collection_id}")

        # 5. Add item to collection
        item = await self.collection_repo.add_item(
            collection_id=collection_id,
            listing_id=share.listing_id,
            status="undecided",
            notes=f"Shared by user {share.sender_id}: {share.message or '(no message)'}",
        )

        # 6. Mark share as imported
        await self.share_repo.mark_share_imported(share.id)

        await self.session.commit()

        logger.info(
            f"Imported share {share.id} (listing {share.listing_id}) "
            f"to collection {collection_id} for user {user_id}"
        )

        return item

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

    # ==================== Token Security & Rate Limiting ====================

    async def check_share_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded share rate limit (10/hour).

        Enforces a rate limit of 10 shares per user per hour to prevent
        abuse and spam.

        Args:
            user_id: User ID to check

        Returns:
            True if under limit, False if exceeded

        Example:
            if await service.check_share_rate_limit(user_id=1):
                # Allow share creation
                pass
            else:
                # Show error message
                pass
        """
        # Calculate one hour ago
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        # Query shares created in last hour
        result = await self.session.execute(
            select(func.count(UserShare.id)).where(
                UserShare.sender_id == user_id, UserShare.created_at >= one_hour_ago
            )
        )
        count = result.scalar_one()

        # Rate limit: 10 shares per hour
        return count < 10
