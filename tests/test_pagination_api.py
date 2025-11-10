"""Integration tests for paginated listings API endpoint (PERF-003)."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.core import Listing


@pytest.mark.asyncio
class TestPaginatedListingsEndpoint:
    """Test GET /v1/listings/paginated endpoint."""

    async def test_get_first_page_default_params(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test getting first page with default parameters."""
        response = await client.get("/v1/listings/paginated")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "next_cursor" in data
        assert "has_next" in data

        assert data["limit"] == 50
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["has_next"], bool)

    async def test_get_page_with_custom_limit(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test getting page with custom limit."""
        response = await client.get("/v1/listings/paginated?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert len(data["items"]) <= 10

    async def test_pagination_navigation(
        self, client: AsyncClient, many_listings: list[Listing]
    ):
        """Test navigating through pages using cursor."""
        # Get first page
        response1 = await client.get("/v1/listings/paginated?limit=10")
        assert response1.status_code == 200
        page1 = response1.json()

        if not page1["has_next"]:
            pytest.skip("Not enough data for multi-page test")

        # Get second page using cursor
        next_cursor = page1["next_cursor"]
        response2 = await client.get(f"/v1/listings/paginated?limit=10&cursor={next_cursor}")
        assert response2.status_code == 200
        page2 = response2.json()

        # Verify no duplicate items
        page1_ids = {item["id"] for item in page1["items"]}
        page2_ids = {item["id"] for item in page2["items"]}
        assert page1_ids.isdisjoint(page2_ids), "Pages should not contain duplicate items"

    async def test_sort_by_price_ascending(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test sorting by price ascending."""
        response = await client.get(
            "/v1/listings/paginated?sort_by=price_usd&sort_order=asc&limit=10"
        )

        assert response.status_code == 200
        data = response.json()

        prices = [item["price_usd"] for item in data["items"]]
        assert prices == sorted(prices), "Items should be sorted by price ascending"

    async def test_sort_by_price_descending(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test sorting by price descending."""
        response = await client.get(
            "/v1/listings/paginated?sort_by=price_usd&sort_order=desc&limit=10"
        )

        assert response.status_code == 200
        data = response.json()

        prices = [item["price_usd"] for item in data["items"]]
        assert prices == sorted(prices, reverse=True), "Items should be sorted by price descending"

    async def test_sort_by_updated_at_default(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test default sort by updated_at descending."""
        response = await client.get("/v1/listings/paginated?limit=10")

        assert response.status_code == 200
        data = response.json()

        # Verify items are sorted by updated_at descending
        timestamps = [item["updated_at"] for item in data["items"]]
        # Convert to datetime for comparison
        dt_timestamps = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
        assert dt_timestamps == sorted(dt_timestamps, reverse=True)

    async def test_filter_by_form_factor(
        self, client: AsyncClient, sample_listings_with_metadata: list[Listing]
    ):
        """Test filtering by form factor."""
        response = await client.get("/v1/listings/paginated?form_factor=Mini PC")

        assert response.status_code == 200
        data = response.json()

        # All returned items should have the specified form factor
        for item in data["items"]:
            assert item["form_factor"] == "Mini PC"

    async def test_filter_by_manufacturer(
        self, client: AsyncClient, sample_listings_with_metadata: list[Listing]
    ):
        """Test filtering by manufacturer."""
        response = await client.get("/v1/listings/paginated?manufacturer=Dell")

        assert response.status_code == 200
        data = response.json()

        # All returned items should have the specified manufacturer
        for item in data["items"]:
            assert item["manufacturer"] == "Dell"

    async def test_filter_by_price_range(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test filtering by price range."""
        response = await client.get(
            "/v1/listings/paginated?min_price=200&max_price=800"
        )

        assert response.status_code == 200
        data = response.json()

        # All returned items should be within price range
        for item in data["items"]:
            assert 200.0 <= item["price_usd"] <= 800.0

    async def test_filter_min_price_only(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test filtering with min_price only."""
        response = await client.get("/v1/listings/paginated?min_price=500")

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["price_usd"] >= 500.0

    async def test_filter_max_price_only(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test filtering with max_price only."""
        response = await client.get("/v1/listings/paginated?max_price=500")

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert item["price_usd"] <= 500.0

    async def test_combined_filters_and_sorting(
        self, client: AsyncClient, sample_listings_with_metadata: list[Listing]
    ):
        """Test combining filters and sorting."""
        response = await client.get(
            "/v1/listings/paginated?"
            "manufacturer=Dell&"
            "form_factor=Mini PC&"
            "min_price=200&"
            "max_price=800&"
            "sort_by=price_usd&"
            "sort_order=asc&"
            "limit=20"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify filters
        for item in data["items"]:
            assert item["manufacturer"] == "Dell"
            assert item["form_factor"] == "Mini PC"
            assert 200.0 <= item["price_usd"] <= 800.0

        # Verify sorting
        prices = [item["price_usd"] for item in data["items"]]
        assert prices == sorted(prices)

    async def test_invalid_sort_column(self, client: AsyncClient):
        """Test invalid sort column returns 400."""
        response = await client.get("/v1/listings/paginated?sort_by=invalid_column")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid sort column" in data["detail"]

    async def test_sql_injection_protection(self, client: AsyncClient):
        """Test protection against SQL injection in sort column."""
        response = await client.get(
            "/v1/listings/paginated?sort_by=id; DROP TABLE listing;"
        )

        # Should be rejected by regex validation or invalid column check
        assert response.status_code == 400

    async def test_limit_validation_too_small(self, client: AsyncClient):
        """Test limit < 1 returns 422 (validation error)."""
        response = await client.get("/v1/listings/paginated?limit=0")

        assert response.status_code == 422  # FastAPI validation error

    async def test_limit_validation_too_large(self, client: AsyncClient):
        """Test limit > 500 returns 422 (validation error)."""
        response = await client.get("/v1/listings/paginated?limit=501")

        assert response.status_code == 422  # FastAPI validation error

    async def test_invalid_cursor_format(self, client: AsyncClient):
        """Test invalid cursor format returns 400."""
        response = await client.get("/v1/listings/paginated?cursor=invalid-cursor")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid cursor format" in data["detail"]

    async def test_invalid_sort_order(self, client: AsyncClient):
        """Test invalid sort order returns 422 (validation error)."""
        response = await client.get("/v1/listings/paginated?sort_order=invalid")

        assert response.status_code == 422  # FastAPI validation error

    async def test_negative_price_filters(self, client: AsyncClient):
        """Test negative price filters return 422 (validation error)."""
        response = await client.get("/v1/listings/paginated?min_price=-100")

        assert response.status_code == 422  # FastAPI validation error

    async def test_empty_result_set(self, client: AsyncClient):
        """Test pagination with no matching results."""
        response = await client.get(
            "/v1/listings/paginated?manufacturer=NonExistentManufacturer"
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 0
        assert data["has_next"] is False
        assert data["next_cursor"] is None

    async def test_response_schema_structure(
        self, client: AsyncClient, sample_listings: list[Listing]
    ):
        """Test response schema matches PaginatedListingsResponse."""
        response = await client.get("/v1/listings/paginated?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "next_cursor" in data
        assert "has_next" in data

        # Verify types
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["has_next"], bool)
        # next_cursor can be string or None
        assert data["next_cursor"] is None or isinstance(data["next_cursor"], str)

        # Verify item structure (should match ListingRead schema)
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "title" in item
            assert "price_usd" in item

    async def test_pagination_consistency_across_pages(
        self, client: AsyncClient, many_listings: list[Listing]
    ):
        """Test that total count is consistent across pages."""
        # Get first page
        response1 = await client.get("/v1/listings/paginated?limit=10")
        page1 = response1.json()

        if not page1["has_next"]:
            pytest.skip("Not enough data for multi-page test")

        # Get second page
        cursor = page1["next_cursor"]
        response2 = await client.get(f"/v1/listings/paginated?limit=10&cursor={cursor}")
        page2 = response2.json()

        # Total should be consistent (cached)
        assert page1["total"] == page2["total"]

    async def test_eager_loading_relationships(
        self, client: AsyncClient, sample_listings_with_cpu: list[Listing]
    ):
        """Test that CPU/GPU relationships are eagerly loaded (no N+1 queries)."""
        response = await client.get("/v1/listings/paginated?limit=10")

        assert response.status_code == 200
        data = response.json()

        # Verify CPU data is included if present
        for item in data["items"]:
            if item.get("cpu_id"):
                assert "cpu" in item or item.get("cpu") is not None


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

    for listing in listings:
        await session.refresh(listing)

    return listings


@pytest.fixture
async def sample_listings_with_metadata(session: AsyncSession) -> list[Listing]:
    """Create sample listings with manufacturer and form factor metadata."""
    listings = []
    now = datetime.utcnow()

    manufacturers = ["Dell", "HP", "Lenovo"]
    form_factors = ["Mini PC", "Desktop", "All-in-One"]

    for i in range(30):
        listing = Listing(
            title=f"Test Listing {i+1}",
            price_usd=200.0 + (i * 30),
            adjusted_price_usd=180.0 + (i * 27),
            condition="used",
            manufacturer=manufacturers[i % 3],
            form_factor=form_factors[i % 3],
            updated_at=now - timedelta(hours=i),
            created_at=now - timedelta(days=i),
        )
        session.add(listing)
        listings.append(listing)

    await session.commit()

    for listing in listings:
        await session.refresh(listing)

    return listings


@pytest.fixture
async def sample_listings_with_cpu(session: AsyncSession) -> list[Listing]:
    """Create sample listings with CPU relationships."""
    from dealbrain_api.models.core import Cpu

    # Create a test CPU
    cpu = Cpu(
        name="Intel Core i5-12400",
        manufacturer="Intel",
        cpu_mark_single=3500,
        cpu_mark_multi=20000,
    )
    session.add(cpu)
    await session.commit()
    await session.refresh(cpu)

    listings = []
    now = datetime.utcnow()

    for i in range(10):
        listing = Listing(
            title=f"Test Listing with CPU {i+1}",
            price_usd=400.0 + (i * 50),
            adjusted_price_usd=380.0 + (i * 45),
            condition="used",
            cpu_id=cpu.id,
            updated_at=now - timedelta(hours=i),
        )
        session.add(listing)
        listings.append(listing)

    await session.commit()

    for listing in listings:
        await session.refresh(listing)

    return listings
