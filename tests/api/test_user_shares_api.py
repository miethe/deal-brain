"""Integration tests for user-to-user shares API endpoints (Phase 3.2).

This module tests the user shares endpoints:
- POST /api/v1/user-shares - Create user-to-user share
- GET /api/v1/user-shares - List received shares (inbox)
- GET /api/v1/user-shares/{token} - Preview shared deal
- POST /api/v1/user-shares/{token}/import - Import to collection

Covers:
- Share creation with/without message
- Rate limiting (10 shares/hour)
- Recipient/listing validation
- Inbox filtering and pagination
- Preview with/without authentication
- Import to collection (default and specified)
- Deduplication checks
- Authorization (only recipient can import)
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from dealbrain_api.db import Base
from dealbrain_api.models.sharing import Collection, CollectionItem, User, UserShare
from dealbrain_api.models.listings import Listing
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Try to import aiosqlite
AIOSQLITE_AVAILABLE = False
try:
    import aiosqlite  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:
    # aiosqlite is not installed; tests will be skipped if unavailable
    pass


# ==================== Fixtures ====================


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory database session for tests."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping user shares API tests")

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
    """Create FastAPI test app with user_shares router."""
    from dealbrain_api.api.user_shares import router, get_current_user, CurrentUser
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
async def sender_user(db_session):
    """Create a sender user."""
    user = User(
        username="sender",
        email="sender@example.com",
        display_name="Sender User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def recipient_user(db_session):
    """Create a recipient user."""
    user = User(
        username="recipient",
        email="recipient@example.com",
        display_name="Recipient User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db_session):
    """Create another user for authorization tests."""
    user = User(
        username="other",
        email="other@example.com",
        display_name="Other User"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_listing(db_session):
    """Create a test listing."""
    listing = Listing(
        title="Gaming PC Deal",
        price_usd=799.99,
        quality="complete"
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


@pytest_asyncio.fixture
async def another_listing(db_session):
    """Create another test listing."""
    listing = Listing(
        title="Office PC Deal",
        price_usd=499.99,
        quality="complete"
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


@pytest_asyncio.fixture
async def default_collection(db_session, recipient_user):
    """Create a default collection for recipient."""
    collection = Collection(
        user_id=recipient_user.id,
        name="My Deals",
        description="Default collection",
        visibility="private"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection


@pytest_asyncio.fixture
async def custom_collection(db_session, recipient_user):
    """Create a custom collection for recipient."""
    collection = Collection(
        user_id=recipient_user.id,
        name="Gaming Deals",
        description="Gaming PC deals",
        visibility="private"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection


@pytest_asyncio.fixture
async def active_user_share(db_session, sender_user, recipient_user, test_listing):
    """Create an active user share."""
    share = UserShare(
        sender_id=sender_user.id,
        recipient_id=recipient_user.id,
        listing_id=test_listing.id,
        share_token=UserShare.generate_token(),
        message="Check out this deal!",
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


@pytest_asyncio.fixture
async def viewed_share(db_session, sender_user, recipient_user, test_listing):
    """Create a viewed user share."""
    share = UserShare(
        sender_id=sender_user.id,
        recipient_id=recipient_user.id,
        listing_id=test_listing.id,
        share_token=UserShare.generate_token(),
        message="Another deal",
        expires_at=datetime.utcnow() + timedelta(days=30),
        viewed_at=datetime.utcnow()
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


@pytest_asyncio.fixture
async def expired_share(db_session, sender_user, recipient_user, test_listing):
    """Create an expired user share."""
    share = UserShare(
        sender_id=sender_user.id,
        recipient_id=recipient_user.id,
        listing_id=test_listing.id,
        share_token=UserShare.generate_token(),
        message="Expired deal",
        expires_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(share)
    await db_session.commit()
    await db_session.refresh(share)
    return share


def mock_current_user(user_id: int, username: str):
    """Helper to mock get_current_user dependency."""
    from dealbrain_api.api.user_shares import CurrentUser

    async def _get_current_user():
        return CurrentUser(user_id=user_id, username=username)

    return _get_current_user


# ==================== POST /user-shares Tests ====================


def test_create_user_share_success(app, client, sender_user, recipient_user, test_listing):
    """Test POST /user-shares - Valid request creates share."""
    from dealbrain_api.api.user_shares import get_current_user

    # Override auth to use sender
    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": test_listing.id,
        "message": "Check this out!"
    }

    response = client.post("/v1/user-shares", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["sender_id"] == sender_user.id
    assert data["recipient_id"] == recipient_user.id
    assert data["listing_id"] == test_listing.id
    assert data["message"] == "Check this out!"
    assert data["share_token"] is not None
    assert len(data["share_token"]) == 64
    assert data["is_expired"] is False
    assert data["is_viewed"] is False
    assert data["is_imported"] is False


def test_create_user_share_without_message(app, client, sender_user, recipient_user, test_listing):
    """Test POST /user-shares - Message is optional."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": test_listing.id
    }

    response = client.post("/v1/user-shares", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] is None


def test_create_user_share_recipient_not_found(app, client, sender_user, test_listing):
    """Test POST /user-shares - Invalid recipient_id returns 400."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": 99999,  # Nonexistent user
        "listing_id": test_listing.id,
        "message": "Test"
    }

    response = client.post("/v1/user-shares", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()


def test_create_user_share_listing_not_found(app, client, sender_user, recipient_user):
    """Test POST /user-shares - Invalid listing_id returns 400."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": 99999,  # Nonexistent listing
        "message": "Test"
    }

    response = client.post("/v1/user-shares", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()


def test_create_user_share_rate_limit(app, client, sender_user, recipient_user, test_listing):
    """Test POST /user-shares - Rate limit enforced (10 shares/hour)."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": test_listing.id,
        "message": "Test"
    }

    # Create 10 shares (should succeed)
    for i in range(10):
        response = client.post("/v1/user-shares", json=payload)
        assert response.status_code == 201

    # 11th share should fail (rate limit)
    response = client.post("/v1/user-shares", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert "rate limit" in data["detail"].lower() or "exceeded" in data["detail"].lower()


def test_create_user_share_generates_unique_token(app, client, sender_user, recipient_user, test_listing):
    """Test POST /user-shares - Each share gets unique token."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": test_listing.id
    }

    # Create 5 shares
    tokens = []
    for _ in range(5):
        response = client.post("/v1/user-shares", json=payload)
        assert response.status_code == 201
        tokens.append(response.json()["share_token"])

    # All tokens should be unique
    assert len(tokens) == len(set(tokens))


def test_create_user_share_response_schema(app, client, sender_user, recipient_user, test_listing):
    """Test POST /user-shares - Response matches UserShareRead schema."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": test_listing.id,
        "message": "Test"
    }

    response = client.post("/v1/user-shares", json=payload)

    assert response.status_code == 201
    data = response.json()

    # Verify all required fields
    required_fields = [
        "id", "sender_id", "recipient_id", "listing_id", "share_token",
        "message", "shared_at", "expires_at", "viewed_at", "imported_at",
        "is_expired", "is_viewed", "is_imported"
    ]
    for field in required_fields:
        assert field in data


# ==================== GET /user-shares Tests ====================


def test_list_user_shares_empty(app, client, recipient_user):
    """Test GET /user-shares - Empty inbox."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    response = client.get("/v1/user-shares")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_user_shares_pagination(app, client, sender_user, recipient_user, test_listing, db_session):
    """Test GET /user-shares - Pagination works correctly."""
    from dealbrain_api.api.user_shares import get_current_user

    # Create 15 shares
    for i in range(15):
        share = UserShare(
            sender_id=sender_user.id,
            recipient_id=recipient_user.id,
            listing_id=test_listing.id,
            share_token=f"token_{i:02d}_" + UserShare.generate_token()[:50],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(share)
    await db_session.commit()

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Get first page (limit 10)
    response = client.get("/v1/user-shares?limit=10&skip=0")
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1) == 10

    # Get second page
    response = client.get("/v1/user-shares?limit=10&skip=10")
    assert response.status_code == 200
    page2 = response.json()
    assert len(page2) == 5

    # Verify no overlap
    page1_ids = {share["id"] for share in page1}
    page2_ids = {share["id"] for share in page2}
    assert len(page1_ids & page2_ids) == 0


def test_list_user_shares_filter_unviewed(app, client, recipient_user, active_user_share, viewed_share):
    """Test GET /user-shares - Filter=unviewed shows only unviewed."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    response = client.get("/v1/user-shares?filter=unviewed")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == active_user_share.id
    assert data[0]["is_viewed"] is False


def test_list_user_shares_filter_all(app, client, recipient_user, active_user_share, viewed_share):
    """Test GET /user-shares - Filter=all shows all shares."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    response = client.get("/v1/user-shares?filter=all")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least active and viewed


def test_list_user_shares_excludes_expired(app, client, recipient_user, active_user_share, expired_share):
    """Test GET /user-shares - Expired shares excluded by default."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    response = client.get("/v1/user-shares?filter=unviewed")

    assert response.status_code == 200
    data = response.json()
    # Should only include active_user_share, not expired_share
    share_ids = [share["id"] for share in data]
    assert active_user_share.id in share_ids
    assert expired_share.id not in share_ids


@pytest.mark.asyncio
async def test_list_user_shares_ordered_by_date(app, client, sender_user, recipient_user, test_listing, db_session):
    """Test GET /user-shares - Shares ordered by shared_at DESC (newest first)."""
    from dealbrain_api.api.user_shares import get_current_user

    # Create shares with different timestamps
    share1 = UserShare(
        sender_id=sender_user.id,
        recipient_id=recipient_user.id,
        listing_id=test_listing.id,
        share_token=UserShare.generate_token(),
        shared_at=datetime.utcnow() - timedelta(hours=2),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    share2 = UserShare(
        sender_id=sender_user.id,
        recipient_id=recipient_user.id,
        listing_id=test_listing.id,
        share_token=UserShare.generate_token(),
        shared_at=datetime.utcnow() - timedelta(hours=1),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    share3 = UserShare(
        sender_id=sender_user.id,
        recipient_id=recipient_user.id,
        listing_id=test_listing.id,
        share_token=UserShare.generate_token(),
        shared_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add_all([share1, share2, share3])
    await db_session.commit()

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    response = client.get("/v1/user-shares?filter=all")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

    # First share should be the newest (share3)
    assert data[0]["id"] == share3.id


# ==================== GET /user-shares/{token} Tests ====================


def test_preview_user_share_success(app, client, active_user_share):
    """Test GET /user-shares/{token} - Valid token returns share."""
    response = client.get(f"/v1/user-shares/{active_user_share.share_token}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == active_user_share.id
    assert data["share_token"] == active_user_share.share_token
    assert data["listing_id"] == active_user_share.listing_id


def test_preview_user_share_not_found(client):
    """Test GET /user-shares/{token} - Invalid token returns 404."""
    response = client.get("/v1/user-shares/invalid_token_12345")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_preview_user_share_expired(client, expired_share):
    """Test GET /user-shares/{token} - Expired share returns 404."""
    response = client.get(f"/v1/user-shares/{expired_share.share_token}")

    assert response.status_code == 404
    data = response.json()
    assert "expired" in data["detail"].lower()


def test_preview_user_share_marks_viewed(app, client, active_user_share, recipient_user):
    """Test GET /user-shares/{token} - Marks as viewed when recipient views."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Initial state: not viewed
    assert active_user_share.viewed_at is None

    response = client.get(f"/v1/user-shares/{active_user_share.share_token}")

    assert response.status_code == 200
    data = response.json()
    # viewed_at should now be set (becomes is_viewed=True)
    assert data["is_viewed"] is True


def test_preview_user_share_unauthenticated(client, active_user_share):
    """Test GET /user-shares/{token} - Works without authentication."""
    # No authentication override
    response = client.get(f"/v1/user-shares/{active_user_share.share_token}")

    # Should succeed even without auth
    assert response.status_code == 200
    data = response.json()
    assert data["share_token"] == active_user_share.share_token


def test_preview_user_share_wrong_user_no_mark(app, client, active_user_share, other_user):
    """Test GET /user-shares/{token} - Wrong user doesn't mark as viewed."""
    from dealbrain_api.api.user_shares import get_current_user

    # Authenticate as other_user (not recipient)
    app.dependency_overrides[get_current_user] = mock_current_user(other_user.id, other_user.username)

    response = client.get(f"/v1/user-shares/{active_user_share.share_token}")

    assert response.status_code == 200
    data = response.json()
    # Should NOT be marked as viewed (only recipient can mark)
    assert data["is_viewed"] is False


# ==================== POST /user-shares/{token}/import Tests ====================


def test_import_user_share_success(app, client, active_user_share, recipient_user, custom_collection):
    """Test POST /user-shares/{token}/import - Imports to specified collection."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    payload = {"collection_id": custom_collection.id}

    response = client.post(f"/v1/user-shares/{active_user_share.share_token}/import", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["collection_id"] == custom_collection.id
    assert data["listing_id"] == active_user_share.listing_id
    assert data["status"] == "undecided"
    # Notes should include the share message
    assert "Check out this deal!" in data["notes"]


def test_import_user_share_default_collection(app, client, active_user_share, recipient_user, default_collection):
    """Test POST /user-shares/{token}/import - Uses default collection if not specified."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Don't specify collection_id
    payload = {}

    response = client.post(f"/v1/user-shares/{active_user_share.share_token}/import", json=payload)

    assert response.status_code == 201
    data = response.json()
    # Should use default collection
    assert data["collection_id"] == default_collection.id
    assert data["listing_id"] == active_user_share.listing_id


@pytest.mark.asyncio
async def test_import_user_share_duplicate(app, client, active_user_share, recipient_user, custom_collection, db_session):
    """Test POST /user-shares/{token}/import - Returns 409 if already in collection."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Add listing to collection first
    item = CollectionItem(
        collection_id=custom_collection.id,
        listing_id=active_user_share.listing_id,
        status="undecided"
    )
    db_session.add(item)
    await db_session.commit()

    payload = {"collection_id": custom_collection.id}

    response = client.post(f"/v1/user-shares/{active_user_share.share_token}/import", json=payload)

    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"].lower()


def test_import_user_share_wrong_recipient(app, client, active_user_share, other_user, custom_collection):
    """Test POST /user-shares/{token}/import - Returns 403 if not recipient."""
    from dealbrain_api.api.user_shares import get_current_user

    # Authenticate as other_user (not recipient)
    app.dependency_overrides[get_current_user] = mock_current_user(other_user.id, other_user.username)

    payload = {"collection_id": custom_collection.id}

    response = client.post(f"/v1/user-shares/{active_user_share.share_token}/import", json=payload)

    assert response.status_code == 403
    data = response.json()
    assert "permission" in data["detail"].lower() or "not the recipient" in data["detail"].lower()


def test_import_user_share_marks_imported(app, client, active_user_share, recipient_user, custom_collection, db_session):
    """Test POST /user-shares/{token}/import - Marks share as imported."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Initial state: not imported
    assert active_user_share.imported_at is None

    payload = {"collection_id": custom_collection.id}

    response = client.post(f"/v1/user-shares/{active_user_share.share_token}/import", json=payload)

    assert response.status_code == 201

    # Refresh share from database
    db_session.refresh(active_user_share)
    assert active_user_share.imported_at is not None
    assert active_user_share.is_imported() is True


def test_import_user_share_invalid_token(app, client, recipient_user):
    """Test POST /user-shares/{token}/import - Invalid token returns 400."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    payload = {}

    response = client.post("/v1/user-shares/invalid_token_12345/import", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert "not found" in data["detail"].lower() or "invalid" in data["detail"].lower()


def test_import_user_share_expired_token(app, client, expired_share, recipient_user):
    """Test POST /user-shares/{token}/import - Expired token returns 400."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    payload = {}

    response = client.post(f"/v1/user-shares/{expired_share.share_token}/import", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert "expired" in data["detail"].lower() or "not found" in data["detail"].lower()


# ==================== Edge Cases ====================


def test_create_user_share_message_length_validation(app, client, sender_user, recipient_user, test_listing):
    """Test POST /user-shares - Message length enforced (max 500 chars)."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(sender_user.id, sender_user.username)

    payload = {
        "recipient_id": recipient_user.id,
        "listing_id": test_listing.id,
        "message": "x" * 501  # Over 500 chars
    }

    response = client.post("/v1/user-shares", json=payload)

    # Should fail validation
    assert response.status_code == 422


def test_list_user_shares_limit_validation(app, client, recipient_user):
    """Test GET /user-shares - Limit must be 1-100."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Limit too high
    response = client.get("/v1/user-shares?limit=101")
    assert response.status_code == 422

    # Limit too low
    response = client.get("/v1/user-shares?limit=0")
    assert response.status_code == 422

    # Valid limit
    response = client.get("/v1/user-shares?limit=50")
    assert response.status_code == 200


def test_list_user_shares_filter_validation(app, client, recipient_user):
    """Test GET /user-shares - Filter must be 'unviewed' or 'all'."""
    from dealbrain_api.api.user_shares import get_current_user

    app.dependency_overrides[get_current_user] = mock_current_user(recipient_user.id, recipient_user.username)

    # Invalid filter
    response = client.get("/v1/user-shares?filter=invalid")
    assert response.status_code == 422

    # Valid filters
    response = client.get("/v1/user-shares?filter=unviewed")
    assert response.status_code == 200

    response = client.get("/v1/user-shares?filter=all")
    assert response.status_code == 200
