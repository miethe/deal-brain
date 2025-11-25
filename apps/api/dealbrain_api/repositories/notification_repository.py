"""Repository for Notification CRUD operations.

This module provides the data access layer for user notifications including:
- Creating notifications for various event types
- Querying user notifications with filters (read/unread, type)
- Marking notifications as read (individual or bulk)
- Deleting old notifications
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.sharing import Notification


class NotificationRepository:
    """Repository for managing user notifications.

    Handles all database operations for notifications with:
    - Type-based filtering (share_received, share_imported, etc.)
    - Read/unread status management
    - Efficient querying with eager loading
    - Bulk operations for mark-all-read

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

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
            type: Notification type (share_received, share_imported, etc.)
            title: Notification title (brief summary)
            message: Notification message (full text)
            share_id: Optional ID of related UserShare

        Returns:
            Notification: Created notification instance

        Example:
            notification = await repo.create_notification(
                user_id=2,
                type="share_received",
                title="New deal shared with you",
                message="John shared a deal: Intel NUC 11 Pro",
                share_id=123
            )
        """
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            share_id=share_id
        )

        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)

        return notification

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
        stmt = (
            select(Notification)
            .options(
                joinedload(Notification.user),
                joinedload(Notification.share)
            )
            .where(Notification.id == notification_id)
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

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
            unread = await repo.get_user_notifications(
                user_id=1,
                unread_only=True,
                limit=20
            )

            # Get all share-related notifications
            shares = await repo.get_user_notifications(
                user_id=1,
                notification_type="share_received"
            )
        """
        conditions = [Notification.user_id == user_id]

        # Filter by read status
        if unread_only:
            conditions.append(Notification.read_at.is_(None))

        # Filter by type
        if notification_type:
            conditions.append(Notification.type == notification_type)

        stmt = (
            select(Notification)
            .options(
                joinedload(Notification.share)
            )
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def count_unread_notifications(self, user_id: int) -> int:
        """Count unread notifications for user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications

        Example:
            count = await repo.count_unread_notifications(user_id=1)
            print(f"You have {count} unread notifications")
        """
        from sqlalchemy import func

        stmt = (
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None)
                )
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def mark_notification_as_read(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Mark notification as read.

        Sets read_at timestamp if not already set. Includes ownership check.

        Args:
            notification_id: Notification ID to mark as read
            user_id: User ID (must be owner of notification)

        Returns:
            True if marked as read, False if not found or already read

        Example:
            success = await repo.mark_notification_as_read(
                notification_id=123,
                user_id=1
            )
        """
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None)  # Only update if not already read
                )
            )
            .values(read_at=datetime.utcnow())
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all unread notifications as read for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read

        Example:
            count = await repo.mark_all_as_read(user_id=1)
            print(f"Marked {count} notifications as read")
        """
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None)
                )
            )
            .values(read_at=datetime.utcnow())
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount

    async def delete_notification(
        self,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Delete notification.

        Includes ownership check to ensure user can only delete their own notifications.

        Args:
            notification_id: Notification ID to delete
            user_id: User ID (must be owner of notification)

        Returns:
            True if deleted, False if not found or unauthorized

        Example:
            success = await repo.delete_notification(
                notification_id=123,
                user_id=1
            )
        """
        stmt = (
            delete(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount > 0

    async def delete_old_notifications(
        self,
        user_id: int,
        days_old: int = 90
    ) -> int:
        """Delete read notifications older than specified days.

        Used for cleanup to prevent notification table from growing indefinitely.

        Args:
            user_id: User ID
            days_old: Delete notifications older than this many days (default: 90)

        Returns:
            Number of notifications deleted

        Example:
            # Delete read notifications older than 90 days
            count = await repo.delete_old_notifications(user_id=1)
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = (
            delete(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.isnot(None),  # Only delete read notifications
                    Notification.created_at < cutoff_date
                )
            )
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount
