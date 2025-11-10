"""Tests for cursor-based pagination (PERF-003)."""

import base64
import json
from datetime import datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:
    import aiosqlite  # type: ignore  # noqa: F401
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False

from dealbrain_api.db import Base
from dealbrain_api.models.core import Listing
from dealbrain_api.services.listings import (
    encode_cursor,
    decode_cursor,
    get_paginated_listings,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestCursorEncoding:
    """Test cursor encoding/decoding utilities."""

    def test_encode_cursor_with_integer_value(self):
        """Test encoding cursor with integer sort value."""
        cursor = encode_cursor(123, 456)
        assert isinstance(cursor, str)
        # Verify it's valid base64
        decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        decoded_json = json.loads(decoded_bytes.decode("utf-8"))
        assert decoded_json["id"] == 123
        assert decoded_json["sort_value"] == "456"

    def test_encode_cursor_with_float_value(self):
        """Test encoding cursor with float sort value."""
        cursor = encode_cursor(100, 199.99)
        decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        decoded_json = json.loads(decoded_bytes.decode("utf-8"))
        assert decoded_json["id"] == 100
        assert decoded_json["sort_value"] == "199.99"

    def test_encode_cursor_with_datetime_value(self):
        """Test encoding cursor with datetime (ISO format string)."""
        dt = datetime(2024, 1, 15, 12, 30, 0)
        cursor = encode_cursor(42, dt.isoformat())
        decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        decoded_json = json.loads(decoded_bytes.decode("utf-8"))
        assert decoded_json["id"] == 42
        assert decoded_json["sort_value"] == dt.isoformat()

    def test_encode_cursor_with_none_value(self):
        """Test encoding cursor with None sort value."""
        cursor = encode_cursor(999, None)
        decoded_bytes = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        decoded_json = json.loads(decoded_bytes.decode("utf-8"))
        assert decoded_json["id"] == 999
        assert decoded_json["sort_value"] is None

    def test_decode_cursor_valid(self):
        """Test decoding a valid cursor."""
        original_id = 123
        original_value = "2024-01-01T00:00:00"
        cursor = encode_cursor(original_id, original_value)

        decoded_id, decoded_value = decode_cursor(cursor)
        assert decoded_id == original_id
        assert decoded_value == original_value

    def test_decode_cursor_invalid_base64(self):
        """Test decoding invalid base64 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor("not-valid-base64!!!")

    def test_decode_cursor_invalid_json(self):
        """Test decoding invalid JSON raises ValueError."""
        invalid_json = base64.urlsafe_b64encode(b"not json").decode("utf-8")
        with pytest.raises(ValueError, match="Invalid cursor format"):
            decode_cursor(invalid_json)

    def test_cursor_roundtrip(self):
        """Test encoding and decoding cursor preserves values."""
        test_cases = [
            (1, "100"),
            (999, "2024-10-31T12:00:00"),
            (42, None),
            (500, "199.99"),
        ]

        for listing_id, sort_value in test_cases:
            cursor = encode_cursor(listing_id, sort_value)
            decoded_id, decoded_value = decode_cursor(cursor)
            assert decoded_id == listing_id
            assert decoded_value == sort_value


@pytest.mark.anyio("asyncio")
class TestPaginatedListings:
    """Test paginated listings service function.

    Note: These tests require a test database setup.
    For full integration testing, run with pytest --integration flag.
    """

    @pytest.mark.skip(reason="Requires test database setup - see test_pagination_api.py for API-level tests")
    async def test_get_first_page_default_params(
        self, db_session, sample_listings: list[Listing]
    ):
        """Test getting first page with default parameters."""
        result = await get_paginated_listings(db_session)

        assert "items" in result
        assert "total" in result
        assert "limit" in result
        assert "next_cursor" in result
        assert "has_next" in result

        assert result["limit"] == 50
        assert len(result["items"]) <= 50
        assert result["total"] >= len(result["items"])

    async def test_get_first_page_with_custom_limit(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test getting first page with custom limit."""
        result = await get_paginated_listings(session, limit=10)

        assert len(result["items"]) <= 10
        assert result["limit"] == 10

    async def test_pagination_with_small_dataset(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test pagination when total items < limit."""
        # Assuming sample_listings has fewer items than default limit
        result = await get_paginated_listings(session, limit=100)

        assert result["has_next"] is False
        assert result["next_cursor"] is None

    async def test_pagination_has_next_page(
        self, session: AsyncSession, many_listings: list[Listing]
    ):
        """Test pagination correctly identifies next page availability."""
        result = await get_paginated_listings(session, limit=10)

        if result["total"] > 10:
            assert result["has_next"] is True
            assert result["next_cursor"] is not None
        else:
            assert result["has_next"] is False
            assert result["next_cursor"] is None

    async def test_pagination_cursor_navigation(
        self, session: AsyncSession, many_listings: list[Listing]
    ):
        """Test navigating through pages using cursor."""
        # Get first page
        page1 = await get_paginated_listings(session, limit=5)
        assert len(page1["items"]) > 0

        if not page1["has_next"]:
            pytest.skip("Not enough data for multi-page test")

        # Get second page using cursor
        page2 = await get_paginated_listings(session, limit=5, cursor=page1["next_cursor"])

        # Items should be different
        page1_ids = {listing.id for listing in page1["items"]}
        page2_ids = {listing.id for listing in page2["items"]}
        assert page1_ids.isdisjoint(page2_ids), "Pages should not contain duplicate items"

    async def test_pagination_sort_by_price_asc(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test sorting by price ascending."""
        result = await get_paginated_listings(
            session, limit=10, sort_by="price_usd", sort_order="asc"
        )

        # Verify items are sorted by price ascending
        prices = [listing.price_usd for listing in result["items"]]
        assert prices == sorted(prices), "Items should be sorted by price ascending"

    async def test_pagination_sort_by_price_desc(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test sorting by price descending."""
        result = await get_paginated_listings(
            session, limit=10, sort_by="price_usd", sort_order="desc"
        )

        # Verify items are sorted by price descending
        prices = [listing.price_usd for listing in result["items"]]
        assert prices == sorted(prices, reverse=True), "Items should be sorted by price descending"

    async def test_pagination_sort_by_updated_at_desc(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test default sort by updated_at descending."""
        result = await get_paginated_listings(
            session, limit=10, sort_by="updated_at", sort_order="desc"
        )

        # Verify items are sorted by updated_at descending
        timestamps = [listing.updated_at for listing in result["items"]]
        assert timestamps == sorted(timestamps, reverse=True)

    async def test_pagination_filter_by_form_factor(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test filtering by form factor."""
        # First, set form factor on some listings
        for i, listing in enumerate(sample_listings[:3]):
            listing.form_factor = "Mini PC" if i % 2 == 0 else "Desktop"
        await session.commit()

        result = await get_paginated_listings(session, form_factor="Mini PC")

        # All returned items should have the specified form factor
        for listing in result["items"]:
            assert listing.form_factor == "Mini PC"

    async def test_pagination_filter_by_manufacturer(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test filtering by manufacturer."""
        # Set manufacturer on some listings
        for i, listing in enumerate(sample_listings[:3]):
            listing.manufacturer = "Dell" if i % 2 == 0 else "HP"
        await session.commit()

        result = await get_paginated_listings(session, manufacturer="Dell")

        # All returned items should have the specified manufacturer
        for listing in result["items"]:
            assert listing.manufacturer == "Dell"

    async def test_pagination_filter_by_price_range(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test filtering by price range."""
        result = await get_paginated_listings(
            session, min_price=200.0, max_price=800.0
        )

        # All returned items should be within price range
        for listing in result["items"]:
            assert 200.0 <= listing.price_usd <= 800.0

    async def test_pagination_filter_min_price_only(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test filtering with min_price only."""
        result = await get_paginated_listings(session, min_price=500.0)

        for listing in result["items"]:
            assert listing.price_usd >= 500.0

    async def test_pagination_filter_max_price_only(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test filtering with max_price only."""
        result = await get_paginated_listings(session, max_price=500.0)

        for listing in result["items"]:
            assert listing.price_usd <= 500.0

    async def test_pagination_combined_filters(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test combining multiple filters."""
        # Set up test data
        for i, listing in enumerate(sample_listings[:5]):
            listing.manufacturer = "Dell"
            listing.form_factor = "Mini PC"
            listing.price_usd = 400.0 + (i * 50)
        await session.commit()

        result = await get_paginated_listings(
            session,
            manufacturer="Dell",
            form_factor="Mini PC",
            min_price=400.0,
            max_price=600.0,
        )

        # Verify all filters are applied
        for listing in result["items"]:
            assert listing.manufacturer == "Dell"
            assert listing.form_factor == "Mini PC"
            assert 400.0 <= listing.price_usd <= 600.0

    async def test_pagination_invalid_sort_column(self, session: AsyncSession):
        """Test validation of invalid sort column."""
        with pytest.raises(ValueError, match="Invalid sort column"):
            await get_paginated_listings(session, sort_by="invalid_column")

    async def test_pagination_invalid_sort_column_sql_injection(self, session: AsyncSession):
        """Test protection against SQL injection in sort column."""
        with pytest.raises(ValueError, match="Invalid sort column"):
            await get_paginated_listings(session, sort_by="id; DROP TABLE listing;")

    async def test_pagination_limit_validation_too_small(self, session: AsyncSession):
        """Test limit validation rejects values < 1."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 500"):
            await get_paginated_listings(session, limit=0)

    async def test_pagination_limit_validation_too_large(self, session: AsyncSession):
        """Test limit validation rejects values > 500."""
        with pytest.raises(ValueError, match="Limit must be between 1 and 500"):
            await get_paginated_listings(session, limit=501)

    async def test_pagination_invalid_cursor_format(self, session: AsyncSession):
        """Test invalid cursor format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cursor format"):
            await get_paginated_listings(session, cursor="invalid-cursor")

    async def test_pagination_stable_ordering(
        self, session: AsyncSession, many_listings: list[Listing]
    ):
        """Test that pagination maintains stable ordering across pages."""
        # Get all items in small pages
        all_ids = []
        cursor = None

        for _ in range(10):  # Arbitrary limit to prevent infinite loop
            result = await get_paginated_listings(session, limit=5, cursor=cursor)
            all_ids.extend([listing.id for listing in result["items"]])

            if not result["has_next"]:
                break
            cursor = result["next_cursor"]

        # Verify no duplicates (stable ordering)
        assert len(all_ids) == len(set(all_ids)), "Pagination should not return duplicates"

    async def test_pagination_total_count_cached(
        self, session: AsyncSession, sample_listings: list[Listing]
    ):
        """Test that total count is consistent across pages (cached)."""
        page1 = await get_paginated_listings(session, limit=5)
        page2 = await get_paginated_listings(session, limit=5, cursor=page1["next_cursor"])

        # Total should be the same (assuming no inserts between calls)
        assert page1["total"] == page2["total"]

    async def test_pagination_empty_result_set(self, session: AsyncSession):
        """Test pagination with no matching results."""
        result = await get_paginated_listings(
            session,
            manufacturer="NonExistentManufacturer",
        )

        assert len(result["items"]) == 0
        assert result["has_next"] is False
        assert result["next_cursor"] is None
        assert result["total"] == 0


# Fixtures


@pytest.fixture
async def sample_listings(session: AsyncSession) -> list[Listing]:
    """Create sample listings for testing."""
    listings = []
    now = datetime.utcnow()

    for i in range(15):
        listing = Listing(
            title=f"Test Listing {i+1}",
            price_usd=100.0 + (i * 50),
            adjusted_price_usd=90.0 + (i * 45),
            condition="used",
            updated_at=now - timedelta(hours=i),
            created_at=now - timedelta(days=i),
        )
        session.add(listing)
        listings.append(listing)

    await session.commit()

    # Refresh to get generated IDs
    for listing in listings:
        await session.refresh(listing)

    return listings


@pytest.fixture
async def many_listings(session: AsyncSession) -> list[Listing]:
    """Create many listings for pagination testing."""
    listings = []
    now = datetime.utcnow()

    for i in range(100):
        listing = Listing(
            title=f"Bulk Test Listing {i+1}",
            price_usd=100.0 + (i * 10),
            adjusted_price_usd=95.0 + (i * 9.5),
            condition="used",
            manufacturer="TestManufacturer" if i % 3 == 0 else "OtherManufacturer",
            form_factor="Mini PC" if i % 2 == 0 else "Desktop",
            updated_at=now - timedelta(minutes=i),
            created_at=now - timedelta(hours=i),
        )
        session.add(listing)
        listings.append(listing)

    await session.commit()

    # Refresh to get generated IDs
    for listing in listings:
        await session.refresh(listing)

    return listings
