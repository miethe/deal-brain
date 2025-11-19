"""Models for collections and sharing features.

This module contains models for:
- User: Basic user authentication foundation
- ListingShare: Public shareable deal pages (FR-A1)
- UserShare: User-to-user deal sharing (FR-A3)
- Collection: User-defined collections of deals (FR-B1)
- CollectionItem: Individual items within collections (FR-B2)
- Notification: In-app notifications for users (FR-A4)
"""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .listings import Listing


class User(Base, TimestampMixin):
    """Minimal user model for authentication foundation.

    This is a basic user model to support collections and sharing features.
    Full authentication (passwords, OAuth, sessions) will be added in later phases.
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(320), unique=True, nullable=True, index=True
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    collections: Mapped[list[Collection]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    created_shares: Mapped[list[ListingShare]] = relationship(
        back_populates="creator", lazy="selectin"
    )
    sent_shares: Mapped[list[UserShare]] = relationship(
        foreign_keys="UserShare.sender_id", back_populates="sender", lazy="selectin"
    )
    received_shares: Mapped[list[UserShare]] = relationship(
        foreign_keys="UserShare.recipient_id", back_populates="recipient", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class ListingShare(Base):
    """Public shareable deal page (FR-A1).

    Allows users to generate unique shareable links for listings that can be
    previewed by anyone without authentication. Includes view tracking and
    optional expiry.
    """

    __tablename__ = "listing_share"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listing.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    share_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    listing: Mapped[Listing] = relationship(back_populates="shares", lazy="joined")
    creator: Mapped[Optional[User]] = relationship(back_populates="created_shares", lazy="joined")

    @classmethod
    def generate_token(cls) -> str:
        """Generate secure 64-character share token.

        Uses secrets.token_urlsafe for cryptographically secure token generation.
        Tokens are URL-safe and suitable for use in shareable links.

        Returns:
            64-character URL-safe token
        """
        return secrets.token_urlsafe(48)[:64]

    def is_expired(self) -> bool:
        """Check if share has expired.

        Returns:
            True if share has expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    async def increment_view_count(self, session) -> None:
        """Increment view count for this share.

        Args:
            session: SQLAlchemy async session
        """
        self.view_count += 1
        session.add(self)
        await session.flush()

    def __repr__(self) -> str:
        status = "expired" if self.is_expired() else "active"
        return f"<ListingShare(id={self.id}, listing_id={self.listing_id}, token='{self.share_token[:8]}...', status={status})>"


class UserShare(Base):
    """User-to-user deal sharing (FR-A3).

    Allows users to share deals directly with other users, including an optional
    message. Tracks when the share was viewed and imported to a collection.
    """

    __tablename__ = "user_share"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listing.id", ondelete="CASCADE"), nullable=False
    )
    share_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shared_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    imported_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    sender: Mapped[User] = relationship(
        foreign_keys=[sender_id], back_populates="sent_shares", lazy="joined"
    )
    recipient: Mapped[User] = relationship(
        foreign_keys=[recipient_id], back_populates="received_shares", lazy="joined"
    )
    listing: Mapped[Listing] = relationship(back_populates="user_shares", lazy="joined")

    @classmethod
    def generate_token(cls) -> str:
        """Generate secure 64-character share token.

        Uses secrets.token_urlsafe for cryptographically secure token generation.

        Returns:
            64-character URL-safe token
        """
        return secrets.token_urlsafe(48)[:64]

    def is_expired(self) -> bool:
        """Check if share has expired.

        Returns:
            True if share has expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def is_viewed(self) -> bool:
        """Check if share has been viewed.

        Returns:
            True if share has been viewed, False otherwise
        """
        return self.viewed_at is not None

    def is_imported(self) -> bool:
        """Check if share has been imported to a collection.

        Returns:
            True if share has been imported, False otherwise
        """
        return self.imported_at is not None

    async def mark_viewed(self, session) -> None:
        """Mark share as viewed with current timestamp.

        Args:
            session: SQLAlchemy async session
        """
        if self.viewed_at is None:
            self.viewed_at = datetime.utcnow()
            session.add(self)
            await session.flush()

    async def mark_imported(self, session) -> None:
        """Mark share as imported with current timestamp.

        Args:
            session: SQLAlchemy async session
        """
        if self.imported_at is None:
            self.imported_at = datetime.utcnow()
            session.add(self)
            await session.flush()

    def __repr__(self) -> str:
        status_parts = []
        if self.is_expired():
            status_parts.append("expired")
        if self.is_viewed():
            status_parts.append("viewed")
        if self.is_imported():
            status_parts.append("imported")
        status = ",".join(status_parts) if status_parts else "pending"
        return f"<UserShare(id={self.id}, sender={self.sender_id}, recipient={self.recipient_id}, listing={self.listing_id}, status={status})>"


class Collection(Base, TimestampMixin):
    """User-defined collection of deals (FR-B1).

    Allows users to organize deals into named collections with descriptions
    and visibility controls. Collections can be private, unlisted (shareable
    via link), or public.
    """

    __tablename__ = "collection"
    __table_args__ = (
        # Composite index for user's collections filtered by visibility
        {"comment": "User collections with visibility-based filtering and discovery"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="private", nullable=False)

    # Relationships
    user: Mapped[User] = relationship(back_populates="collections", lazy="joined")
    items: Mapped[list[CollectionItem]] = relationship(
        back_populates="collection", cascade="all, delete-orphan", lazy="selectin"
    )
    share_tokens: Mapped[list["CollectionShareToken"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    @property
    def item_count(self) -> int:
        """Get count of items in collection.

        Returns:
            Number of items in collection
        """
        return len(self.items)

    def has_item(self, listing_id: int) -> bool:
        """Check if collection contains a specific listing.

        Args:
            listing_id: ID of listing to check

        Returns:
            True if collection contains listing, False otherwise
        """
        return any(item.listing_id == listing_id for item in self.items)

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name='{self.name}', user_id={self.user_id}, items={self.item_count})>"


class CollectionItem(Base, TimestampMixin):
    """Individual item within a collection (FR-B2).

    Represents a single listing within a collection, with support for:
    - Status tracking (undecided, shortlisted, rejected, bought)
    - User notes
    - Position-based ordering for drag-and-drop support
    """

    __tablename__ = "collection_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collection.id", ondelete="CASCADE"), nullable=False
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listing.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="undecided", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    collection: Mapped[Collection] = relationship(back_populates="items", lazy="joined")
    listing: Mapped[Listing] = relationship(back_populates="collection_items", lazy="joined")

    def __repr__(self) -> str:
        return f"<CollectionItem(id={self.id}, collection_id={self.collection_id}, listing_id={self.listing_id}, status='{self.status}')>"


class CollectionShareToken(Base, TimestampMixin):
    """Shareable token for collection access (Phase 2a).

    Allows collections to be shared via unique URLs with view tracking and
    optional expiry. Supports visibility modes:
    - unlisted: Shareable via token but not publicly discoverable
    - public: Both token-shareable and publicly discoverable

    The expires_at field provides soft-delete functionality - expired tokens
    can be filtered out without hard deletion.
    """
    __tablename__ = "collection_share_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collection.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
        index=True
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)

    # Relationships
    collection: Mapped[Collection] = relationship(back_populates="share_tokens", lazy="joined")

    @classmethod
    def generate_token(cls) -> str:
        """Generate secure 64-character share token.

        Uses secrets.token_urlsafe for cryptographically secure token generation.
        Tokens are URL-safe and suitable for use in shareable links.

        Returns:
            64-character URL-safe token
        """
        return secrets.token_urlsafe(48)[:64]

    def is_expired(self) -> bool:
        """Check if share token has expired.

        Returns:
            True if share has expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    async def increment_view_count(self, session) -> None:
        """Increment view count for this share token.

        Args:
            session: SQLAlchemy async session
        """
        self.view_count += 1
        session.add(self)
        await session.flush()

    def __repr__(self) -> str:
        status = "expired" if self.is_expired() else "active"
        return f"<CollectionShareToken(id={self.id}, collection_id={self.collection_id}, token='{self.token[:8]}...', views={self.view_count}, status={status})>"


class Notification(Base, TimestampMixin):
    """In-app notification for users (FR-A4).

    Provides real-time and persistent notifications for user actions such as:
    - Share received: When another user shares a deal with you
    - Share imported: When someone imports a deal you shared
    - Collection updates: When collection items are added/removed
    - System notifications: General system alerts

    Notifications are marked as read/unread and can be filtered by type.
    """
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)

    # Optional link to related share (for share notifications)
    share_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_share.id", ondelete="CASCADE"),
        nullable=True
    )

    # Relationships
    user: Mapped[User] = relationship(lazy="joined")
    share: Mapped[Optional[UserShare]] = relationship(lazy="joined")

    def is_read(self) -> bool:
        """Check if notification has been read.

        Returns:
            True if notification has been read, False otherwise
        """
        return self.read_at is not None

    async def mark_as_read(self, session) -> None:
        """Mark notification as read with current timestamp.

        Args:
            session: SQLAlchemy async session
        """
        if self.read_at is None:
            self.read_at = datetime.utcnow()
            session.add(self)
            await session.flush()

    def __repr__(self) -> str:
        status = "read" if self.is_read() else "unread"
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', status={status})>"
