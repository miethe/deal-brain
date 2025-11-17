"""Tests for sharing and collections Pydantic schemas."""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from dealbrain_core.enums import CollectionVisibility, CollectionItemStatus
from dealbrain_core.schemas import (
    ListingShareBase,
    ListingShareCreate,
    ListingShareRead,
    PublicListingShareRead,
    UserShareBase,
    UserShareCreate,
    UserShareRead,
    CollectionBase,
    CollectionCreate,
    CollectionUpdate,
    CollectionRead,
    CollectionItemBase,
    CollectionItemCreate,
    CollectionItemUpdate,
    CollectionItemRead,
)


# ==================== ListingShare Schema Tests ====================


class TestListingShareBase:
    """Test suite for ListingShareBase schema."""

    def test_accepts_valid_data(self):
        """Schema should accept valid listing_id."""
        data = {"listing_id": 1}
        schema = ListingShareBase(**data)
        assert schema.listing_id == 1
        assert schema.expires_at is None

    def test_accepts_expires_at(self):
        """Schema should accept optional expires_at."""
        expires = datetime.now() + timedelta(days=180)
        data = {"listing_id": 1, "expires_at": expires}
        schema = ListingShareBase(**data)
        assert schema.listing_id == 1
        assert schema.expires_at == expires

    def test_rejects_missing_listing_id(self):
        """Schema should reject missing listing_id."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            ListingShareBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("listing_id",) for error in errors)


class TestListingShareCreate:
    """Test suite for ListingShareCreate schema."""

    def test_inherits_from_base(self):
        """Create schema should inherit from Base."""
        data = {"listing_id": 1}
        schema = ListingShareCreate(**data)
        assert schema.listing_id == 1
        assert schema.expires_at is None


class TestListingShareRead:
    """Test suite for ListingShareRead schema."""

    def test_accepts_full_response_data(self):
        """Read schema should accept full response data."""
        data = {
            "id": 1,
            "listing_id": 1,
            "share_token": "abc123",
            "view_count": 5,
            "created_at": datetime.now(),
            "created_by": 1,
            "is_expired": False,
        }
        schema = ListingShareRead(**data)
        assert schema.id == 1
        assert schema.share_token == "abc123"
        assert schema.view_count == 5
        assert schema.is_expired is False

    def test_created_by_optional(self):
        """created_by field should be optional."""
        data = {
            "id": 1,
            "listing_id": 1,
            "share_token": "abc123",
            "view_count": 0,
            "created_at": datetime.now(),
            "is_expired": False,
        }
        schema = ListingShareRead(**data)
        assert schema.created_by is None


class TestPublicListingShareRead:
    """Test suite for PublicListingShareRead schema."""

    def test_accepts_minimal_public_data(self):
        """Public schema should accept minimal data (no auth required)."""
        data = {
            "share_token": "abc123",
            "listing_id": 1,
            "view_count": 10,
            "is_expired": False,
        }
        schema = PublicListingShareRead(**data)
        assert schema.share_token == "abc123"
        assert schema.listing_id == 1
        assert schema.view_count == 10


# ==================== UserShare Schema Tests ====================


class TestUserShareBase:
    """Test suite for UserShareBase schema."""

    def test_accepts_valid_data(self):
        """Schema should accept valid recipient_id and listing_id."""
        data = {"recipient_id": 2, "listing_id": 1}
        schema = UserShareBase(**data)
        assert schema.recipient_id == 2
        assert schema.listing_id == 1
        assert schema.message is None

    def test_accepts_message(self):
        """Schema should accept optional message."""
        data = {"recipient_id": 2, "listing_id": 1, "message": "Check this out!"}
        schema = UserShareBase(**data)
        assert schema.message == "Check this out!"

    def test_rejects_message_too_long(self):
        """Schema should reject message longer than 500 chars."""
        long_message = "x" * 501
        data = {"recipient_id": 2, "listing_id": 1, "message": long_message}
        with pytest.raises(ValidationError) as exc_info:
            UserShareBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("message",) for error in errors)

    def test_accepts_message_at_max_length(self):
        """Schema should accept message exactly at 500 chars."""
        max_message = "x" * 500
        data = {"recipient_id": 2, "listing_id": 1, "message": max_message}
        schema = UserShareBase(**data)
        assert len(schema.message) == 500


class TestUserShareCreate:
    """Test suite for UserShareCreate schema."""

    def test_inherits_from_base(self):
        """Create schema should inherit from Base."""
        data = {"recipient_id": 2, "listing_id": 1, "message": "Test"}
        schema = UserShareCreate(**data)
        assert schema.recipient_id == 2
        assert schema.message == "Test"


class TestUserShareRead:
    """Test suite for UserShareRead schema."""

    def test_accepts_full_response_data(self):
        """Read schema should accept full response data."""
        now = datetime.now()
        data = {
            "id": 1,
            "sender_id": 1,
            "recipient_id": 2,
            "listing_id": 1,
            "message": "Check this out!",
            "share_token": "abc123",
            "shared_at": now,
            "expires_at": now + timedelta(days=30),
            "viewed_at": now + timedelta(hours=1),
            "imported_at": now + timedelta(hours=2),
            "is_expired": False,
            "is_viewed": True,
            "is_imported": True,
        }
        schema = UserShareRead(**data)
        assert schema.id == 1
        assert schema.sender_id == 1
        assert schema.recipient_id == 2
        assert schema.share_token == "abc123"
        assert schema.is_viewed is True
        assert schema.is_imported is True

    def test_tracking_fields_optional(self):
        """Tracking fields should be optional."""
        now = datetime.now()
        data = {
            "id": 1,
            "sender_id": 1,
            "recipient_id": 2,
            "listing_id": 1,
            "share_token": "abc123",
            "shared_at": now,
            "expires_at": now + timedelta(days=30),
            "is_expired": False,
            "is_viewed": False,
            "is_imported": False,
        }
        schema = UserShareRead(**data)
        assert schema.viewed_at is None
        assert schema.imported_at is None


# ==================== Collection Schema Tests ====================


class TestCollectionBase:
    """Test suite for CollectionBase schema."""

    def test_accepts_valid_data(self):
        """Schema should accept valid name."""
        data = {"name": "My Collection"}
        schema = CollectionBase(**data)
        assert schema.name == "My Collection"
        assert schema.description is None
        assert schema.visibility == CollectionVisibility.PRIVATE

    def test_accepts_full_data(self):
        """Schema should accept all fields."""
        data = {
            "name": "Test Collection",
            "description": "Test description",
            "visibility": CollectionVisibility.PUBLIC,
        }
        schema = CollectionBase(**data)
        assert schema.name == "Test Collection"
        assert schema.description == "Test description"
        assert schema.visibility == CollectionVisibility.PUBLIC

    def test_rejects_empty_name(self):
        """Schema should reject empty name."""
        data = {"name": ""}
        with pytest.raises(ValidationError) as exc_info:
            CollectionBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_rejects_name_too_long(self):
        """Schema should reject name longer than 100 chars."""
        long_name = "x" * 101
        data = {"name": long_name}
        with pytest.raises(ValidationError) as exc_info:
            CollectionBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_accepts_name_at_max_length(self):
        """Schema should accept name exactly at 100 chars."""
        max_name = "x" * 100
        data = {"name": max_name}
        schema = CollectionBase(**data)
        assert len(schema.name) == 100

    def test_rejects_description_too_long(self):
        """Schema should reject description longer than 1000 chars."""
        long_desc = "x" * 1001
        data = {"name": "Test", "description": long_desc}
        with pytest.raises(ValidationError) as exc_info:
            CollectionBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_accepts_description_at_max_length(self):
        """Schema should accept description exactly at 1000 chars."""
        max_desc = "x" * 1000
        data = {"name": "Test", "description": max_desc}
        schema = CollectionBase(**data)
        assert len(schema.description) == 1000

    def test_accepts_visibility_enum(self):
        """Schema should accept CollectionVisibility enum values."""
        for visibility in CollectionVisibility:
            data = {"name": "Test", "visibility": visibility}
            schema = CollectionBase(**data)
            assert schema.visibility == visibility

    def test_accepts_visibility_string(self):
        """Schema should accept visibility as string."""
        data = {"name": "Test", "visibility": "unlisted"}
        schema = CollectionBase(**data)
        assert schema.visibility == CollectionVisibility.UNLISTED

    def test_rejects_invalid_visibility(self):
        """Schema should reject invalid visibility value."""
        data = {"name": "Test", "visibility": "invalid"}
        with pytest.raises(ValidationError) as exc_info:
            CollectionBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("visibility",) for error in errors)


class TestCollectionCreate:
    """Test suite for CollectionCreate schema."""

    def test_inherits_from_base(self):
        """Create schema should inherit from Base."""
        data = {"name": "Test Collection"}
        schema = CollectionCreate(**data)
        assert schema.name == "Test Collection"
        assert schema.visibility == CollectionVisibility.PRIVATE


class TestCollectionUpdate:
    """Test suite for CollectionUpdate schema."""

    def test_all_fields_optional(self):
        """Update schema should have all fields optional."""
        data = {}
        schema = CollectionUpdate(**data)
        assert schema.name is None
        assert schema.description is None
        assert schema.visibility is None

    def test_accepts_partial_update(self):
        """Update schema should accept partial updates."""
        data = {"name": "Updated Name"}
        schema = CollectionUpdate(**data)
        assert schema.name == "Updated Name"
        assert schema.description is None

    def test_validates_name_length_when_provided(self):
        """Update schema should validate name length when provided."""
        long_name = "x" * 101
        data = {"name": long_name}
        with pytest.raises(ValidationError) as exc_info:
            CollectionUpdate(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_rejects_empty_name(self):
        """Update schema should reject empty name."""
        data = {"name": ""}
        with pytest.raises(ValidationError) as exc_info:
            CollectionUpdate(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)


class TestCollectionRead:
    """Test suite for CollectionRead schema."""

    def test_accepts_full_response_data(self):
        """Read schema should accept full response data."""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "My Collection",
            "description": "Test description",
            "visibility": CollectionVisibility.PRIVATE,
            "user_id": 1,
            "created_at": now,
            "updated_at": now,
            "item_count": 5,
        }
        schema = CollectionRead(**data)
        assert schema.id == 1
        assert schema.name == "My Collection"
        assert schema.user_id == 1
        assert schema.item_count == 5

    def test_items_optional(self):
        """items field should be optional."""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "My Collection",
            "visibility": CollectionVisibility.PRIVATE,
            "user_id": 1,
            "created_at": now,
            "updated_at": now,
            "item_count": 0,
        }
        schema = CollectionRead(**data)
        assert schema.items is None

    def test_accepts_items_list(self):
        """items field should accept list of CollectionItemRead."""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "My Collection",
            "visibility": CollectionVisibility.PRIVATE,
            "user_id": 1,
            "created_at": now,
            "updated_at": now,
            "item_count": 1,
            "items": [
                {
                    "id": 1,
                    "collection_id": 1,
                    "listing_id": 1,
                    "status": CollectionItemStatus.UNDECIDED,
                    "added_at": now,
                    "updated_at": now,
                }
            ],
        }
        schema = CollectionRead(**data)
        assert len(schema.items) == 1
        assert schema.items[0].listing_id == 1


# ==================== CollectionItem Schema Tests ====================


class TestCollectionItemBase:
    """Test suite for CollectionItemBase schema."""

    def test_accepts_valid_data(self):
        """Schema should accept valid listing_id."""
        data = {"listing_id": 1}
        schema = CollectionItemBase(**data)
        assert schema.listing_id == 1
        assert schema.status == CollectionItemStatus.UNDECIDED
        assert schema.notes is None
        assert schema.position is None

    def test_accepts_full_data(self):
        """Schema should accept all fields."""
        data = {
            "listing_id": 1,
            "status": CollectionItemStatus.SHORTLISTED,
            "notes": "Great deal!",
            "position": 0,
        }
        schema = CollectionItemBase(**data)
        assert schema.listing_id == 1
        assert schema.status == CollectionItemStatus.SHORTLISTED
        assert schema.notes == "Great deal!"
        assert schema.position == 0

    def test_accepts_status_enum(self):
        """Schema should accept CollectionItemStatus enum values."""
        for status in CollectionItemStatus:
            data = {"listing_id": 1, "status": status}
            schema = CollectionItemBase(**data)
            assert schema.status == status

    def test_accepts_status_string(self):
        """Schema should accept status as string."""
        data = {"listing_id": 1, "status": "shortlisted"}
        schema = CollectionItemBase(**data)
        assert schema.status == CollectionItemStatus.SHORTLISTED

    def test_rejects_invalid_status(self):
        """Schema should reject invalid status value."""
        data = {"listing_id": 1, "status": "invalid"}
        with pytest.raises(ValidationError) as exc_info:
            CollectionItemBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status",) for error in errors)

    def test_rejects_notes_too_long(self):
        """Schema should reject notes longer than 500 chars."""
        long_notes = "x" * 501
        data = {"listing_id": 1, "notes": long_notes}
        with pytest.raises(ValidationError) as exc_info:
            CollectionItemBase(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("notes",) for error in errors)

    def test_accepts_notes_at_max_length(self):
        """Schema should accept notes exactly at 500 chars."""
        max_notes = "x" * 500
        data = {"listing_id": 1, "notes": max_notes}
        schema = CollectionItemBase(**data)
        assert len(schema.notes) == 500


class TestCollectionItemCreate:
    """Test suite for CollectionItemCreate schema."""

    def test_inherits_from_base(self):
        """Create schema should inherit from Base."""
        data = {"listing_id": 1, "status": CollectionItemStatus.SHORTLISTED}
        schema = CollectionItemCreate(**data)
        assert schema.listing_id == 1
        assert schema.status == CollectionItemStatus.SHORTLISTED


class TestCollectionItemUpdate:
    """Test suite for CollectionItemUpdate schema."""

    def test_all_fields_optional(self):
        """Update schema should have all fields optional."""
        data = {}
        schema = CollectionItemUpdate(**data)
        assert schema.status is None
        assert schema.notes is None
        assert schema.position is None

    def test_accepts_partial_update(self):
        """Update schema should accept partial updates."""
        data = {"status": CollectionItemStatus.BOUGHT}
        schema = CollectionItemUpdate(**data)
        assert schema.status == CollectionItemStatus.BOUGHT
        assert schema.notes is None

    def test_validates_notes_length_when_provided(self):
        """Update schema should validate notes length when provided."""
        long_notes = "x" * 501
        data = {"notes": long_notes}
        with pytest.raises(ValidationError) as exc_info:
            CollectionItemUpdate(**data)
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("notes",) for error in errors)


class TestCollectionItemRead:
    """Test suite for CollectionItemRead schema."""

    def test_accepts_full_response_data(self):
        """Read schema should accept full response data."""
        now = datetime.now()
        data = {
            "id": 1,
            "collection_id": 1,
            "listing_id": 1,
            "status": CollectionItemStatus.SHORTLISTED,
            "notes": "Great deal!",
            "position": 0,
            "added_at": now,
            "updated_at": now,
        }
        schema = CollectionItemRead(**data)
        assert schema.id == 1
        assert schema.collection_id == 1
        assert schema.listing_id == 1
        assert schema.status == CollectionItemStatus.SHORTLISTED
        assert schema.notes == "Great deal!"
        assert schema.position == 0


# ==================== Integration Tests ====================


class TestSchemaIntegration:
    """Test integration between schemas (e.g., CollectionRead with items)."""

    def test_collection_with_multiple_items(self):
        """CollectionRead should support multiple items."""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "My Collection",
            "visibility": CollectionVisibility.PRIVATE,
            "user_id": 1,
            "created_at": now,
            "updated_at": now,
            "item_count": 3,
            "items": [
                {
                    "id": 1,
                    "collection_id": 1,
                    "listing_id": 1,
                    "status": CollectionItemStatus.SHORTLISTED,
                    "added_at": now,
                    "updated_at": now,
                },
                {
                    "id": 2,
                    "collection_id": 1,
                    "listing_id": 2,
                    "status": CollectionItemStatus.UNDECIDED,
                    "notes": "Need to check specs",
                    "position": 1,
                    "added_at": now,
                    "updated_at": now,
                },
                {
                    "id": 3,
                    "collection_id": 1,
                    "listing_id": 3,
                    "status": CollectionItemStatus.REJECTED,
                    "notes": "Too expensive",
                    "position": 2,
                    "added_at": now,
                    "updated_at": now,
                },
            ],
        }
        schema = CollectionRead(**data)
        assert schema.item_count == 3
        assert len(schema.items) == 3
        assert schema.items[0].status == CollectionItemStatus.SHORTLISTED
        assert schema.items[1].notes == "Need to check specs"
        assert schema.items[2].status == CollectionItemStatus.REJECTED

    def test_schema_serialization(self):
        """Schemas should serialize to dict correctly."""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "Test Collection",
            "visibility": CollectionVisibility.PUBLIC,
            "user_id": 1,
            "created_at": now,
            "updated_at": now,
            "item_count": 0,
        }
        schema = CollectionRead(**data)
        serialized = schema.model_dump()
        assert serialized["name"] == "Test Collection"
        assert serialized["visibility"] == "public"  # Enum serialized as string
        assert serialized["item_count"] == 0
