"""API endpoints for user notifications.

This module provides REST endpoints for:
- Listing user notifications with filters
- Marking notifications as read
- Deleting notifications
- Getting unread notification count
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency as get_session
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ==================== Request/Response Schemas ====================


class NotificationResponse(BaseModel):
    """Response schema for notification data."""

    id: int
    user_id: int
    type: str
    title: str
    message: str
    read_at: Optional[str] = None
    share_id: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for notification list."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int
    limit: int
    offset: int


class MarkAsReadRequest(BaseModel):
    """Request schema for marking notification as read."""

    notification_id: int = Field(..., description="Notification ID to mark as read")


class MarkAllAsReadResponse(BaseModel):
    """Response schema for mark all as read."""

    marked_count: int = Field(..., description="Number of notifications marked as read")


class UnreadCountResponse(BaseModel):
    """Response schema for unread count."""

    unread_count: int = Field(..., description="Number of unread notifications")


# ==================== Endpoints ====================


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    user_id: int = Query(..., description="User ID to get notifications for"),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    notification_type: Optional[str] = Query(
        None,
        description="Filter by notification type (share_received, share_imported, etc.)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip (pagination)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get user's notifications with filtering.

    Returns paginated list of notifications with unread count.

    Query Parameters:
    - user_id: User ID (required)
    - unread_only: If true, only return unread notifications (default: false)
    - notification_type: Filter by type (optional)
    - limit: Max results per page (default: 50, max: 100)
    - offset: Pagination offset (default: 0)

    Example:
        GET /api/v1/notifications?user_id=1&unread_only=true&limit=20

    Returns:
        {
            "notifications": [...],
            "total": 150,
            "unread_count": 5,
            "limit": 50,
            "offset": 0
        }
    """
    service = NotificationService(session)

    # Get notifications
    notifications = await service.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        notification_type=notification_type,
        limit=limit,
        offset=offset
    )

    # Get unread count
    unread_count = await service.count_unread_notifications(user_id)

    # Convert to response format
    notification_responses = [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            title=n.title,
            message=n.message,
            read_at=n.read_at.isoformat() if n.read_at else None,
            share_id=n.share_id,
            created_at=n.created_at.isoformat(),
            updated_at=n.updated_at.isoformat()
        )
        for n in notifications
    ]

    return {
        "notifications": notification_responses,
        "total": len(notification_responses),
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    user_id: int = Query(..., description="User ID to get unread count for"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get count of unread notifications for user.

    Useful for displaying notification badge counts in UI.

    Query Parameters:
    - user_id: User ID (required)

    Example:
        GET /api/v1/notifications/unread-count?user_id=1

    Returns:
        {
            "unread_count": 5
        }
    """
    service = NotificationService(session)

    unread_count = await service.count_unread_notifications(user_id)

    return {
        "unread_count": unread_count
    }


@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    user_id: int = Query(..., description="User ID (for ownership verification)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Mark notification as read.

    Sets read_at timestamp for the notification. Includes ownership check.

    Path Parameters:
    - notification_id: Notification ID to mark as read

    Query Parameters:
    - user_id: User ID (required for ownership verification)

    Example:
        PATCH /api/v1/notifications/123/read?user_id=1

    Returns:
        {
            "success": true,
            "notification_id": 123
        }

    Raises:
        403: If user doesn't own the notification
        404: If notification not found
    """
    service = NotificationService(session)

    try:
        success = await service.mark_notification_as_read(notification_id, user_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notification_id} not found"
            )

        await session.commit()

        return {
            "success": True,
            "notification_id": notification_id
        }

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/mark-all-read", response_model=MarkAllAsReadResponse)
async def mark_all_notifications_as_read(
    user_id: int = Query(..., description="User ID to mark all notifications as read"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Mark all unread notifications as read for user.

    Bulk operation to mark all unread notifications as read in a single request.

    Query Parameters:
    - user_id: User ID (required)

    Example:
        POST /api/v1/notifications/mark-all-read?user_id=1

    Returns:
        {
            "marked_count": 15
        }
    """
    service = NotificationService(session)

    marked_count = await service.mark_all_as_read(user_id)

    await session.commit()

    return {
        "marked_count": marked_count
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    user_id: int = Query(..., description="User ID (for ownership verification)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete notification.

    Permanently deletes the notification. Includes ownership check.

    Path Parameters:
    - notification_id: Notification ID to delete

    Query Parameters:
    - user_id: User ID (required for ownership verification)

    Example:
        DELETE /api/v1/notifications/123?user_id=1

    Returns:
        {
            "success": true,
            "notification_id": 123
        }

    Raises:
        403: If user doesn't own the notification
        404: If notification not found
    """
    service = NotificationService(session)

    try:
        success = await service.delete_notification(notification_id, user_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notification_id} not found"
            )

        await session.commit()

        return {
            "success": True,
            "notification_id": notification_id
        }

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_notifications(
    user_id: int = Query(..., description="User ID to cleanup notifications for"),
    days_old: int = Query(90, ge=1, le=365, description="Delete notifications older than this many days"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Delete read notifications older than specified days.

    Cleanup operation to prevent notification table from growing indefinitely.
    Only deletes read notifications.

    Query Parameters:
    - user_id: User ID (required)
    - days_old: Delete notifications older than this many days (default: 90, max: 365)

    Example:
        POST /api/v1/notifications/cleanup?user_id=1&days_old=90

    Returns:
        {
            "deleted_count": 42,
            "days_old": 90
        }
    """
    service = NotificationService(session)

    deleted_count = await service.cleanup_old_notifications(user_id, days_old)

    await session.commit()

    return {
        "deleted_count": deleted_count,
        "days_old": days_old
    }
