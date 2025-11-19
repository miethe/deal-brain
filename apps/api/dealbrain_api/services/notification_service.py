"""Business logic for managing user notifications.

This module provides the service layer for notification features including:
- Creating notifications for share events
- Retrieving user inbox with filtering
- Marking notifications as read (individual or bulk)
- Notification cleanup and management
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sharing import Notification
from ..repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Business logic for managing user notifications.

    Provides high-level operations for:
    - Creating notifications for various event types
    - Retrieving user notifications with filters
    - Managing read/unread status
    - Notification cleanup

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.notification_repo = NotificationRepository(session)

    async def create_notification(
        self,
        user_id: int,
        type: str,
        title: str,
        message: str,
        share_id: Optional[int] = None
    ) -> Notification:
        """Create a new notification.

        Args:
            user_id: Recipient user ID
            type: Notification type (share_received, share_imported, system, etc.)
            title: Notification title (brief summary)
            message: Notification message (full text)
            share_id: Optional ID of related UserShare

        Returns:
            Created Notification instance

        Example:
            notification = await service.create_notification(
                user_id=2,
                type="share_received",
                title="New deal shared with you",
                message="John shared 'Intel NUC 11 Pro' with you",
                share_id=123
            )
        """
        notification = await self.notification_repo.create_notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            share_id=share_id
        )

        logger.info(
            f"Created notification {notification.id} for user {user_id} "
            f"(type: {type}, share_id: {share_id})"
        )

        return notification

    async def create_share_received_notification(
        self,
        recipient_id: int,
        sender_name: str,
        listing_name: str,
        share_id: int
    ) -> Notification:
        """Create notification for received share.

        Convenience method for creating share_received notifications with
        standardized formatting.

        Args:
            recipient_id: User ID who received the share
            sender_name: Display name of sender
            listing_name: Name of the listing being shared
            share_id: UserShare ID

        Returns:
            Created Notification instance

        Example:
            notification = await service.create_share_received_notification(
                recipient_id=2,
                sender_name="John Doe",
                listing_name="Intel NUC 11 Pro",
                share_id=123
            )
        """
        title = f"New deal from {sender_name}"
        message = f"{sender_name} shared a deal with you: {listing_name}"

        return await self.create_notification(
            user_id=recipient_id,
            type="share_received",
            title=title,
            message=message,
            share_id=share_id
        )

    async def create_share_imported_notification(
        self,
        sender_id: int,
        recipient_name: str,
        listing_name: str,
        share_id: int
    ) -> Notification:
        """Create notification for imported share.

        Notifies the original sender when recipient imports their shared deal.

        Args:
            sender_id: User ID who originally sent the share
            recipient_name: Display name of recipient who imported
            listing_name: Name of the listing that was imported
            share_id: UserShare ID

        Returns:
            Created Notification instance

        Example:
            notification = await service.create_share_imported_notification(
                sender_id=1,
                recipient_name="Jane Smith",
                listing_name="Intel NUC 11 Pro",
                share_id=123
            )
        """
        title = f"{recipient_name} saved your deal"
        message = f"{recipient_name} imported the deal you shared: {listing_name}"

        return await self.create_notification(
            user_id=sender_id,
            type="share_imported",
            title=title,
            message=message,
            share_id=share_id
        )

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Notification]:
        """Get user's notifications with filtering.

        Args:
            user_id: User ID to get notifications for
            unread_only: If True, only return unread notifications
            notification_type: If provided, filter by notification type
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip (pagination)

        Returns:
            List of Notification instances ordered by created_at (newest first)

        Example:
            # Get unread notifications
            unread = await service.get_user_notifications(
                user_id=1,
                unread_only=True
            )

            # Get all share notifications
            shares = await service.get_user_notifications(
                user_id=1,
                notification_type="share_received",
                limit=20
            )
        """
        notifications = await self.notification_repo.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            notification_type=notification_type,
            limit=limit,
            offset=offset
        )

        return notifications

    async def get_notification_by_id(
        self,
        notification_id: int
    ) -> Optional[Notification]:
        """Get notification by ID.

        Args:
            notification_id: Notification ID

        Returns:
            Notification instance if found, None otherwise
        """
        return await self.notification_repo.get_notification_by_id(notification_id)

    async def count_unread_notifications(self, user_id: int) -> int:
        """Count unread notifications for user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications

        Example:
            count = await service.count_unread_notifications(user_id=1)
            # Use in API response or badge count
        """
        return await self.notification_repo.count_unread_notifications(user_id)

    async def mark_notification_as_read(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Mark notification as read.

        Includes ownership check to ensure user can only mark their own
        notifications as read.

        Args:
            notification_id: Notification ID to mark as read
            user_id: User ID (must be owner of notification)

        Returns:
            True if marked as read, False if not found or already read

        Raises:
            PermissionError: If user doesn't own the notification

        Example:
            success = await service.mark_notification_as_read(
                notification_id=123,
                user_id=1
            )
        """
        # Verify ownership
        notification = await self.notification_repo.get_notification_by_id(notification_id)

        if not notification:
            return False

        if notification.user_id != user_id:
            raise PermissionError(
                f"User {user_id} does not own notification {notification_id}"
            )

        success = await self.notification_repo.mark_notification_as_read(
            notification_id, user_id
        )

        if success:
            logger.info(f"Notification {notification_id} marked as read by user {user_id}")

        return success

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all unread notifications as read for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read

        Example:
            count = await service.mark_all_as_read(user_id=1)
            print(f"Marked {count} notifications as read")
        """
        count = await self.notification_repo.mark_all_as_read(user_id)

        logger.info(f"Marked {count} notifications as read for user {user_id}")

        return count

    async def delete_notification(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Delete notification.

        Includes ownership check to ensure user can only delete their own
        notifications.

        Args:
            notification_id: Notification ID to delete
            user_id: User ID (must be owner of notification)

        Returns:
            True if deleted, False if not found

        Raises:
            PermissionError: If user doesn't own the notification

        Example:
            success = await service.delete_notification(
                notification_id=123,
                user_id=1
            )
        """
        # Verify ownership
        notification = await self.notification_repo.get_notification_by_id(notification_id)

        if not notification:
            return False

        if notification.user_id != user_id:
            raise PermissionError(
                f"User {user_id} does not own notification {notification_id}"
            )

        success = await self.notification_repo.delete_notification(
            notification_id, user_id
        )

        if success:
            logger.info(f"Notification {notification_id} deleted by user {user_id}")

        return success

    async def cleanup_old_notifications(
        self,
        user_id: int,
        days_old: int = 90
    ) -> int:
        """Delete read notifications older than specified days.

        Used for periodic cleanup to prevent notification table from growing
        indefinitely. Only deletes read notifications.

        Args:
            user_id: User ID
            days_old: Delete notifications older than this many days (default: 90)

        Returns:
            Number of notifications deleted

        Example:
            # Delete read notifications older than 90 days
            count = await service.cleanup_old_notifications(user_id=1)
        """
        count = await self.notification_repo.delete_old_notifications(
            user_id, days_old
        )

        logger.info(
            f"Cleaned up {count} old notifications for user {user_id} "
            f"(older than {days_old} days)"
        )

        return count
