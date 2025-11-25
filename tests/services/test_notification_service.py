"""Unit tests for NotificationService.

Tests cover:
- Creating notifications
- Retrieving user notifications with filters
- Marking notifications as read
- Counting unread notifications
- Deleting notifications
- Cleanup operations
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from dealbrain_api.models.sharing import Notification, User, UserShare
from dealbrain_api.services.notification_service import NotificationService


@pytest.fixture
async def test_users(db_session):
    """Create test users."""
    user1 = User(username="user1", email="user1@example.com", display_name="User One")
    user2 = User(username="user2", email="user2@example.com", display_name="User Two")

    db_session.add(user1)
    db_session.add(user2)
    await db_session.flush()

    return user1, user2


@pytest.fixture
async def notification_service(db_session):
    """Create NotificationService instance."""
    return NotificationService(db_session)


class TestNotificationCreation:
    """Tests for creating notifications."""

    async def test_create_notification(self, db_session, notification_service, test_users):
        """Test basic notification creation."""
        user1, user2 = test_users

        notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Test notification",
            message="This is a test notification"
        )

        assert notification.id is not None
        assert notification.user_id == user1.id
        assert notification.type == "share_received"
        assert notification.title == "Test notification"
        assert notification.message == "This is a test notification"
        assert notification.read_at is None
        assert notification.share_id is None

    async def test_create_share_received_notification(
        self, db_session, notification_service, test_users
    ):
        """Test creating share received notification with helper method."""
        user1, user2 = test_users

        notification = await notification_service.create_share_received_notification(
            recipient_id=user2.id,
            sender_name="User One",
            listing_name="Intel NUC 11 Pro",
            share_id=123
        )

        assert notification.user_id == user2.id
        assert notification.type == "share_received"
        assert "User One" in notification.title
        assert "Intel NUC 11 Pro" in notification.message
        assert notification.share_id == 123

    async def test_create_share_imported_notification(
        self, db_session, notification_service, test_users
    ):
        """Test creating share imported notification with helper method."""
        user1, user2 = test_users

        notification = await notification_service.create_share_imported_notification(
            sender_id=user1.id,
            recipient_name="User Two",
            listing_name="Intel NUC 11 Pro",
            share_id=123
        )

        assert notification.user_id == user1.id
        assert notification.type == "share_imported"
        assert "User Two" in notification.title
        assert "Intel NUC 11 Pro" in notification.message
        assert notification.share_id == 123


class TestNotificationRetrieval:
    """Tests for retrieving notifications."""

    async def test_get_user_notifications(
        self, db_session, notification_service, test_users
    ):
        """Test retrieving user notifications."""
        user1, user2 = test_users

        # Create notifications for user1
        await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Notification 1",
            message="Message 1"
        )
        await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Notification 2",
            message="Message 2"
        )

        # Create notification for user2
        await notification_service.create_notification(
            user_id=user2.id,
            type="share_received",
            title="Notification 3",
            message="Message 3"
        )

        # Get user1's notifications
        notifications = await notification_service.get_user_notifications(user_id=user1.id)

        assert len(notifications) == 2
        assert all(n.user_id == user1.id for n in notifications)

    async def test_filter_unread_notifications(
        self, db_session, notification_service, test_users
    ):
        """Test filtering unread notifications."""
        user1, user2 = test_users

        # Create notifications
        n1 = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Unread",
            message="Unread message"
        )
        n2 = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Read",
            message="Read message"
        )

        # Mark n2 as read
        await notification_service.mark_notification_as_read(n2.id, user1.id)
        await db_session.commit()

        # Get unread only
        unread = await notification_service.get_user_notifications(
            user_id=user1.id,
            unread_only=True
        )

        assert len(unread) == 1
        assert unread[0].id == n1.id

    async def test_filter_by_type(self, db_session, notification_service, test_users):
        """Test filtering notifications by type."""
        user1, user2 = test_users

        # Create different types
        await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Share",
            message="Share message"
        )
        await notification_service.create_notification(
            user_id=user1.id,
            type="system",
            title="System",
            message="System message"
        )

        # Filter by share_received
        shares = await notification_service.get_user_notifications(
            user_id=user1.id,
            notification_type="share_received"
        )

        assert len(shares) == 1
        assert shares[0].type == "share_received"

    async def test_count_unread_notifications(
        self, db_session, notification_service, test_users
    ):
        """Test counting unread notifications."""
        user1, user2 = test_users

        # Create notifications
        n1 = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Unread 1",
            message="Message"
        )
        n2 = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Unread 2",
            message="Message"
        )
        n3 = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Read",
            message="Message"
        )

        # Mark n3 as read
        await notification_service.mark_notification_as_read(n3.id, user1.id)
        await db_session.commit()

        # Count unread
        count = await notification_service.count_unread_notifications(user1.id)

        assert count == 2


class TestMarkAsRead:
    """Tests for marking notifications as read."""

    async def test_mark_notification_as_read(
        self, db_session, notification_service, test_users
    ):
        """Test marking single notification as read."""
        user1, user2 = test_users

        notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Test",
            message="Message"
        )

        # Initially unread
        assert notification.read_at is None

        # Mark as read
        success = await notification_service.mark_notification_as_read(
            notification.id, user1.id
        )

        assert success is True

        # Verify read
        await db_session.refresh(notification)
        assert notification.read_at is not None

    async def test_mark_as_read_permission_check(
        self, db_session, notification_service, test_users
    ):
        """Test that users can only mark their own notifications as read."""
        user1, user2 = test_users

        notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Test",
            message="Message"
        )

        # Try to mark as read by different user
        with pytest.raises(PermissionError):
            await notification_service.mark_notification_as_read(
                notification.id, user2.id
            )

    async def test_mark_all_as_read(self, db_session, notification_service, test_users):
        """Test marking all notifications as read."""
        user1, user2 = test_users

        # Create multiple notifications
        for i in range(3):
            await notification_service.create_notification(
                user_id=user1.id,
                type="share_received",
                title=f"Test {i}",
                message="Message"
            )

        # Mark all as read
        count = await notification_service.mark_all_as_read(user1.id)

        assert count == 3

        # Verify all read
        unread_count = await notification_service.count_unread_notifications(user1.id)
        assert unread_count == 0


class TestNotificationDeletion:
    """Tests for deleting notifications."""

    async def test_delete_notification(
        self, db_session, notification_service, test_users
    ):
        """Test deleting notification."""
        user1, user2 = test_users

        notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Test",
            message="Message"
        )

        # Delete notification
        success = await notification_service.delete_notification(
            notification.id, user1.id
        )

        assert success is True

        # Verify deleted
        result = await notification_service.get_notification_by_id(notification.id)
        assert result is None

    async def test_delete_notification_permission_check(
        self, db_session, notification_service, test_users
    ):
        """Test that users can only delete their own notifications."""
        user1, user2 = test_users

        notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Test",
            message="Message"
        )

        # Try to delete by different user
        with pytest.raises(PermissionError):
            await notification_service.delete_notification(
                notification.id, user2.id
            )

    async def test_cleanup_old_notifications(
        self, db_session, notification_service, test_users
    ):
        """Test cleaning up old read notifications."""
        user1, user2 = test_users

        # Create old read notification
        old_notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Old",
            message="Message"
        )

        # Mark as read and set old timestamp
        await notification_service.mark_notification_as_read(
            old_notification.id, user1.id
        )
        await db_session.commit()

        # Manually set old created_at (simulate old notification)
        stmt = select(Notification).where(Notification.id == old_notification.id)
        result = await db_session.execute(stmt)
        n = result.scalar_one()
        n.created_at = datetime.utcnow() - timedelta(days=100)
        await db_session.flush()

        # Create recent notification
        recent_notification = await notification_service.create_notification(
            user_id=user1.id,
            type="share_received",
            title="Recent",
            message="Message"
        )

        # Cleanup old notifications (>90 days)
        deleted_count = await notification_service.cleanup_old_notifications(
            user1.id, days_old=90
        )

        assert deleted_count == 1

        # Verify recent notification still exists
        result = await notification_service.get_notification_by_id(recent_notification.id)
        assert result is not None
