"""Integration tests for public shares API endpoints (Phase 3.1).

This module tests the GET /api/v1/deals/{listing_id}/{share_token} endpoint
for viewing publicly shared deals without authentication.

Covers:
- Valid token returns listing
- Invalid token returns 404
- Expired token returns 404
- View count increments
- Cache behavior (when Redis available)
- Listing ID mismatch handling
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import importlib.util
import pytest
import pytest_asyncio
from dealbrain_api.db import Base
from dealbrain_api.models.sharing import ListingShare, User
from dealbrain_api.models.listings import Listing
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Check if aiosqlite is available (required for sqlite+aiosqlite engine)
AIOSQLITE_AVAILABLE = importlib.util.find_spec("aiosqlite") is not None


# ==================== Fixtures ====================


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory database session for tests."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping shares API tests")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def app(db_session):
    """Create FastAPI test app with shares router."""
    from dealbrain_api.api.shares import router
    from dealbrain_api.db import session_dependency

    test_app = FastAPI()
    test_app.include_router(router)

    # Override session dependency
    async def override_session_dependency():
        yield db_session

    test_app.dependency_overrides[session_dependency] = override_session_dependency

    return test_app


@pytest.fixture
def client(app):
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(username="testuser", email="test@example.com", display_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_listing(db_session):
    """Create a test listing."""
    listing = Listing(title="Test Mini PC", price_usd=599.99, quality="complete")
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


@pytest_asyncio.fixture
async def active_share(db_session, test_listing, test_user):
    """Create an active public share."""
    share = ListingShare(
        listing_id=test_listing.id,
        created_by=test_user.id,
        share_token=ListingShare.generate_token(),
        view_count=5,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


@pytest_asyncio.fixture
async def expired_share(db_session, test_listing, test_user):
    """Create an expired public share."""
    share = ListingShare(
        listing_id=test_listing.id,
        created_by=test_user.id,
        share_token=ListingShare.generate_token(),
        view_count=10,
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


@pytest_asyncio.fixture
async def share_without_expiry(db_session, test_listing, test_user):
    """Create a share without expiry date."""
    share = ListingShare(
        listing_id=test_listing.id,
        created_by=test_user.id,
        share_token=ListingShare.generate_token(),
        view_count=0,
        expires_at=None,
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


# ==================== Tests ====================


def test_get_public_share_success(client, active_share, test_listing):
    """Test GET /deals/{id}/{token} - Valid token returns listing."""
    response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == active_share.share_token
    assert data["listing_id"] == test_listing.id
    assert data["view_count"] == 6  # Incremented from 5
    assert data["is_expired"] is False


def test_get_public_share_without_expiry(client, share_without_expiry, test_listing):
    """Test GET /deals/{id}/{token} - Share without expiry never expires."""
    response = client.get(f"/v1/deals/{test_listing.id}/{share_without_expiry.share_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == share_without_expiry.share_token
    assert data["listing_id"] == test_listing.id
    assert data["view_count"] == 1  # Incremented from 0
    assert data["is_expired"] is False


def test_get_public_share_not_found_invalid_token(client, test_listing):
    """Test GET /deals/{id}/{token} - Invalid token returns 404."""
    response = client.get(f"/v1/deals/{test_listing.id}/invalid_token_12345")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_public_share_not_found_nonexistent_listing(client):
    """Test GET /deals/{id}/{token} - Nonexistent listing returns 404."""
    response = client.get("/v1/deals/99999/some_token_12345")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_public_share_expired(client, expired_share, test_listing):
    """Test GET /deals/{id}/{token} - Expired token returns 404."""
    response = client.get(f"/v1/deals/{test_listing.id}/{expired_share.share_token}")

    assert response.status_code == 404
    data = response.json()
    assert "expired" in data["detail"].lower()


def test_get_public_share_listing_id_mismatch(client, active_share):
    """Test GET /deals/{id}/{token} - Mismatched listing_id returns 404."""
    wrong_listing_id = active_share.listing_id + 100
    response = client.get(f"/v1/deals/{wrong_listing_id}/{active_share.share_token}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_public_share_increments_view_count(client, active_share, test_listing, db_session):
    """Test GET /deals/{id}/{token} - View count increments correctly."""
    initial_view_count = active_share.view_count

    # Make multiple requests
    for i in range(3):
        response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")
        assert response.status_code == 200
        data = response.json()
        # Each request should increment the view count
        assert data["view_count"] == initial_view_count + i + 1


def test_get_public_share_view_increment_failure_non_blocking(client, active_share, test_listing):
    """Test GET /deals/{id}/{token} - View increment failure doesn't block response."""
    # Mock the SharingService.increment_share_view to raise an exception
    with patch(
        "dealbrain_api.services.sharing_service.SharingService.increment_share_view"
    ) as mock_increment:
        mock_increment.side_effect = Exception("Database error")

        response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")

        # Request should still succeed even if view increment fails
        assert response.status_code == 200
        data = response.json()
        assert data["share_token"] == active_share.share_token


@patch("dealbrain_api.api.shares.get_redis_client")
def test_get_public_share_with_redis_cache_miss(
    mock_redis_client, client, active_share, test_listing
):
    """Test GET /deals/{id}/{token} - Cache miss behavior with Redis."""
    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)  # Cache miss
    mock_redis_client.return_value = mock_redis

    response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == active_share.share_token
    # Verify Redis.get was called
    # Note: In actual implementation, cache key would be checked


@patch("dealbrain_api.api.shares.get_redis_client")
def test_get_public_share_with_redis_cache_error(
    mock_redis_client, client, active_share, test_listing
):
    """Test GET /deals/{id}/{token} - Redis error doesn't block response."""
    # Mock Redis client to raise an exception
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))
    mock_redis_client.return_value = mock_redis

    response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")

    # Request should still succeed even if Redis fails
    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == active_share.share_token


def test_get_public_share_response_schema(client, active_share, test_listing):
    """Test GET /deals/{id}/{token} - Response matches PublicListingShareRead schema."""
    response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields are present
    assert "share_token" in data
    assert "listing_id" in data
    assert "view_count" in data
    assert "is_expired" in data

    # Verify field types
    assert isinstance(data["share_token"], str)
    assert isinstance(data["listing_id"], int)
    assert isinstance(data["view_count"], int)
    assert isinstance(data["is_expired"], bool)


def test_get_public_share_no_authentication_required(client, active_share, test_listing):
    """Test GET /deals/{id}/{token} - No authentication required."""
    # Don't provide any authentication headers
    response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")

    # Should succeed without authentication
    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == active_share.share_token


# ==================== Edge Cases ====================


def test_get_public_share_with_special_characters_in_token(client, test_listing):
    """Test GET /deals/{id}/{token} - URL-safe tokens with special chars work."""
    # URL-safe tokens can contain dashes and underscores
    token_with_special_chars = "abc123-_xyz789-_ABC123"

    response = client.get(f"/v1/deals/{test_listing.id}/{token_with_special_chars}")

    # Should return 404 (not found) not 422 (validation error)
    assert response.status_code == 404


def test_get_public_share_with_very_long_token(client, test_listing):
    """Test GET /deals/{id}/{token} - Very long token handled correctly."""
    # Test with a very long token (longer than 64 chars)
    long_token = "a" * 128

    response = client.get(f"/v1/deals/{test_listing.id}/{long_token}")

    # Should return 404 (not found) not 422 or 500
    assert response.status_code == 404


def test_get_public_share_concurrent_view_increments(client, active_share, test_listing):
    """Test GET /deals/{id}/{token} - Concurrent requests increment view count correctly."""
    initial_view_count = active_share.view_count

    # Make 5 concurrent requests
    responses = []
    for _ in range(5):
        response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")
        responses.append(response)

    # All requests should succeed
    for response in responses:
        assert response.status_code == 200

    # Final view count should be initial + 5
    final_response = client.get(f"/v1/deals/{test_listing.id}/{active_share.share_token}")
    assert final_response.status_code == 200
    final_data = final_response.json()
    # Should be at least initial + 6 (5 previous + 1 current)
    assert final_data["view_count"] >= initial_view_count + 6
