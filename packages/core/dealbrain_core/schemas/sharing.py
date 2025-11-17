"""Schemas for sharing and collections entities."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ..enums import CollectionVisibility, CollectionItemStatus
from .base import DealBrainModel


# ==================== Listing Share Schemas ====================


class ListingShareBase(DealBrainModel):
    """Base schema for listing shares."""

    listing_id: int
    expires_at: datetime | None = None


class ListingShareCreate(ListingShareBase):
    """Schema for creating a listing share."""

    pass


class ListingShareRead(ListingShareBase):
    """Schema for listing share responses."""

    id: int
    share_token: str
    view_count: int
    created_at: datetime
    created_by: int | None = None
    is_expired: bool = False


class PublicListingShareRead(DealBrainModel):
    """Schema for public listing share pages (no auth required)."""

    share_token: str
    listing_id: int
    view_count: int
    is_expired: bool = False


# ==================== User Share Schemas ====================


class UserShareBase(DealBrainModel):
    """Base schema for user shares."""

    recipient_id: int
    listing_id: int
    message: str | None = Field(None, max_length=500)


class UserShareCreate(UserShareBase):
    """Schema for creating a user share."""

    pass


class UserShareRead(UserShareBase):
    """Schema for user share responses."""

    id: int
    sender_id: int
    share_token: str
    shared_at: datetime
    expires_at: datetime
    viewed_at: datetime | None = None
    imported_at: datetime | None = None
    is_expired: bool = False
    is_viewed: bool = False
    is_imported: bool = False


# ==================== Collection Schemas ====================


class CollectionBase(DealBrainModel):
    """Base schema for collections."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    visibility: CollectionVisibility = CollectionVisibility.PRIVATE


class CollectionCreate(CollectionBase):
    """Schema for creating a collection."""

    pass


class CollectionUpdate(DealBrainModel):
    """Schema for updating a collection."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    visibility: CollectionVisibility | None = None


class CollectionRead(CollectionBase):
    """Schema for collection responses."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    items: list[CollectionItemRead] | None = None


# ==================== Collection Item Schemas ====================


class CollectionItemBase(DealBrainModel):
    """Base schema for collection items."""

    listing_id: int
    status: CollectionItemStatus = CollectionItemStatus.UNDECIDED
    notes: str | None = Field(None, max_length=500)
    position: int | None = None


class CollectionItemCreate(CollectionItemBase):
    """Schema for adding item to collection."""

    pass


class CollectionItemUpdate(DealBrainModel):
    """Schema for updating a collection item."""

    status: CollectionItemStatus | None = None
    notes: str | None = Field(None, max_length=500)
    position: int | None = None


class CollectionItemRead(CollectionItemBase):
    """Schema for collection item responses."""

    id: int
    collection_id: int
    added_at: datetime
    updated_at: datetime


# Forward reference resolution for CollectionRead.items
CollectionRead.model_rebuild()


__all__ = [
    # Listing Share
    "ListingShareBase",
    "ListingShareCreate",
    "ListingShareRead",
    "PublicListingShareRead",
    # User Share
    "UserShareBase",
    "UserShareCreate",
    "UserShareRead",
    # Collection
    "CollectionBase",
    "CollectionCreate",
    "CollectionUpdate",
    "CollectionRead",
    # Collection Item
    "CollectionItemBase",
    "CollectionItemCreate",
    "CollectionItemUpdate",
    "CollectionItemRead",
]
