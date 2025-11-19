---
title: "Collections & Sharing Developer Guide"
description: "Comprehensive developer guide covering architecture, implementation patterns, testing strategies, and code organization for Deal Brain's Collections and Sharing features."
audience: [developers, ai-agents]
tags: [developer-guide, collections, sharing, architecture, implementation, testing, database]
created: 2025-11-18
updated: 2025-11-18
category: "developer-documentation"
status: published
related:
  - /docs/api/collections-sharing-api.md
  - /docs/guides/collections-sharing-user-guide.md
---

# Collections & Sharing Developer Guide

## Overview

This guide covers the implementation of Collections & Sharing features in Deal Brain, including architecture, patterns, services, repositories, and testing strategies.

### Quick Facts

- **Features Implemented:**
  - Collections (CRUD + item management)
  - User-to-user sharing (with rate limiting)
  - Public shareable links (with caching)
  - Notifications system
  - Export functionality (CSV/JSON)

- **Tech Stack:**
  - Backend: FastAPI (Python) + SQLAlchemy ORM + PostgreSQL
  - Frontend: Next.js + React Query
  - Caching: Redis
  - Testing: pytest + async test fixtures

- **Code Locations:**
  - Models: `apps/api/dealbrain_api/models/sharing.py`
  - Schemas: `packages/core/dealbrain_core/schemas/sharing.py`
  - APIs: `apps/api/dealbrain_api/api/{collections,user_shares,shares,notifications}.py`
  - Services: `apps/api/dealbrain_api/services/{collections_service,sharing_service,notification_service}.py`
  - Repositories: `apps/api/dealbrain_api/repositories/{collection_repository}.py`

---

## Architecture

### Layered Architecture

Deal Brain follows a classic layered architecture:

```
┌─────────────────────────────────┐
│    API Layer (FastAPI)          │  ← Request handling, validation
│  {collections, shares, etc}     │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Service Layer                 │  ← Business logic orchestration
│ {CollectionsService,            │
│  SharingService,                │
│  NotificationService}           │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Repository Layer              │  ← Data access abstraction
│ {CollectionRepository,          │
│  SharingRepository, etc}        │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Database Layer                │  ← PostgreSQL + SQLAlchemy ORM
│ {User, Collection, Listing,     │
│  CollectionItem, Notification}  │
└─────────────────────────────────┘
```

### Data Model

```
User (1) ──────→ (N) Collection
         ──────→ (N) UserShare (sender)
         ──────→ (N) UserShare (recipient)
         ──────→ (N) ListingShare
         ──────→ (N) Notification

Collection (1) ─→ (N) CollectionItem
                        │
                        └──→ (1) Listing

UserShare ──→ Listing
          ──→ User (sender)
          ──→ User (recipient)

Notification ──→ UserShare (optional)
             ──→ User
```

---

## Database Schema

### User Table

```sql
CREATE TABLE "user" (
    id INTEGER PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE,
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_user_email ON "user"(email);
```

### Collection Table

```sql
CREATE TABLE collection (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL FOREIGN KEY REFERENCES "user"(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    visibility VARCHAR(20) DEFAULT 'private',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_collection_user_id ON collection(user_id);
```

### CollectionItem Table

```sql
CREATE TABLE collection_item (
    id INTEGER PRIMARY KEY,
    collection_id INTEGER NOT NULL FOREIGN KEY REFERENCES collection(id) ON DELETE CASCADE,
    listing_id INTEGER NOT NULL FOREIGN KEY REFERENCES listing(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'undecided',
    notes TEXT,
    position INTEGER,
    added_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_collection_item_collection_id ON collection_item(collection_id);
CREATE INDEX idx_collection_item_listing_id ON collection_item(listing_id);
CREATE UNIQUE INDEX idx_collection_item_unique ON collection_item(collection_id, listing_id);
```

### ListingShare Table

```sql
CREATE TABLE listing_share (
    id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL FOREIGN KEY REFERENCES listing(id) ON DELETE CASCADE,
    created_by INTEGER FOREIGN KEY REFERENCES "user"(id) ON DELETE SET NULL,
    share_token VARCHAR(64) UNIQUE NOT NULL,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_listing_share_token ON listing_share(share_token);
CREATE INDEX idx_listing_share_listing_id ON listing_share(listing_id);
```

### UserShare Table

```sql
CREATE TABLE user_share (
    id INTEGER PRIMARY KEY,
    sender_id INTEGER NOT NULL FOREIGN KEY REFERENCES "user"(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL FOREIGN KEY REFERENCES "user"(id) ON DELETE CASCADE,
    listing_id INTEGER NOT NULL FOREIGN KEY REFERENCES listing(id) ON DELETE CASCADE,
    share_token VARCHAR(64) UNIQUE NOT NULL,
    message TEXT,
    shared_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    viewed_at TIMESTAMP,
    imported_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_share_token ON user_share(share_token);
CREATE INDEX idx_user_share_sender_id ON user_share(sender_id);
CREATE INDEX idx_user_share_recipient_id ON user_share(recipient_id);
```

### Notification Table

```sql
CREATE TABLE notification (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL FOREIGN KEY REFERENCES "user"(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    share_id INTEGER FOREIGN KEY REFERENCES user_share(id) ON DELETE CASCADE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notification_user_id ON notification(user_id);
CREATE INDEX idx_notification_user_read ON notification(user_id, read_at);
CREATE INDEX idx_notification_type ON notification(type);
```

---

## Models

### User Model

```python
class User(Base, TimestampMixin):
    """Minimal user model for authentication foundation."""
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships - eager loaded with selectin
    collections: Mapped[list[Collection]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    created_shares: Mapped[list[ListingShare]] = relationship(
        back_populates="creator",
        lazy="selectin"
    )
    sent_shares: Mapped[list[UserShare]] = relationship(
        foreign_keys="UserShare.sender_id",
        back_populates="sender",
        lazy="selectin"
    )
    received_shares: Mapped[list[UserShare]] = relationship(
        foreign_keys="UserShare.recipient_id",
        back_populates="recipient",
        lazy="selectin"
    )
```

### Collection Model

```python
class Collection(Base, TimestampMixin):
    """User-defined collection of deals."""
    __tablename__ = "collection"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="private")

    # Relationships
    user: Mapped[User] = relationship(back_populates="collections", lazy="joined")
    items: Mapped[list[CollectionItem]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    @property
    def item_count(self) -> int:
        """Get count of items in collection."""
        return len(self.items)
```

### CollectionItem Model

```python
class CollectionItem(Base, TimestampMixin):
    """Individual item within a collection."""
    __tablename__ = "collection_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collection.id", ondelete="CASCADE"),
        nullable=False
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listing.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="undecided")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())

    collection: Mapped[Collection] = relationship(back_populates="items", lazy="joined")
    listing: Mapped[Listing] = relationship(back_populates="collection_items", lazy="joined")
```

---

## Services

### CollectionsService

Located in `apps/api/dealbrain_api/services/collections_service.py`

**Purpose**: Orchestrate collection operations including CRUD, item management, and validation.

**Key Methods**:

```python
class CollectionsService:
    """Service for collection operations."""

    async def create_collection(
        self,
        user_id: int,
        name: str,
        description: str | None = None,
        visibility: str = "private"
    ) -> Collection:
        """Create a new collection."""

    async def list_user_collections(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> list[Collection]:
        """List user's collections with pagination."""

    async def get_collection(
        self,
        collection_id: int,
        user_id: int,
        load_items: bool = False
    ) -> Collection | None:
        """Get collection with ownership check."""

    async def update_collection(
        self,
        collection_id: int,
        user_id: int,
        name: str | None = None,
        description: str | None = None,
        visibility: str | None = None
    ) -> Collection | None:
        """Update collection metadata."""

    async def delete_collection(
        self,
        collection_id: int,
        user_id: int
    ) -> bool:
        """Delete collection and cascade items."""

    async def add_item_to_collection(
        self,
        collection_id: int,
        listing_id: int,
        user_id: int,
        status: str = "undecided",
        notes: str | None = None,
        position: int | None = None
    ) -> CollectionItem:
        """Add item with deduplication check."""

    async def update_collection_item(
        self,
        item_id: int,
        user_id: int,
        status: str | None = None,
        notes: str | None = None,
        position: int | None = None
    ) -> CollectionItem | None:
        """Update item with ownership validation."""

    async def remove_item_from_collection(
        self,
        item_id: int,
        user_id: int
    ) -> bool:
        """Remove item from collection."""
```

### SharingService

Located in `apps/api/dealbrain_api/services/sharing_service.py`

**Purpose**: Handle share token generation, validation, and view tracking.

**Key Methods**:

```python
class SharingService:
    """Service for sharing operations."""

    async def generate_listing_share_token(
        self,
        listing_id: int,
        created_by_id: int | None = None,
        ttl_days: int = 180
    ) -> ListingShare:
        """Generate public share token for listing."""

    async def validate_listing_share_token(
        self,
        share_token: str
    ) -> tuple[ListingShare | None, bool]:
        """Validate share token and check expiry."""

    async def increment_share_view(self, share_token: str) -> None:
        """Increment view count for share."""

    async def create_user_share(
        self,
        sender_id: int,
        recipient_id: int,
        listing_id: int,
        message: str | None = None,
        ttl_days: int = 30
    ) -> UserShare:
        """Create user-to-user share with rate limiting."""

    async def check_share_rate_limit(
        self,
        user_id: int,
        window_hours: int = 1,
        limit: int = 10
    ) -> tuple[int, int]:
        """Check rate limit (returns: used, remaining)."""

    async def mark_share_viewed(
        self,
        share_token: str
    ) -> None:
        """Mark share as viewed by recipient."""

    async def mark_share_imported(
        self,
        share_token: str
    ) -> None:
        """Mark share as imported to collection."""
```

### NotificationService

Located in `apps/api/dealbrain_api/services/notification_service.py`

**Purpose**: Manage notification creation, retrieval, and status updates.

**Key Methods**:

```python
class NotificationService:
    """Service for notification operations."""

    async def create_notification(
        self,
        user_id: int,
        type: str,
        title: str,
        message: str,
        share_id: int | None = None
    ) -> Notification:
        """Create notification for user."""

    async def get_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        notification_type: str | None = None
    ) -> list[Notification]:
        """Get user's notifications with filtering."""

    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications."""

    async def mark_as_read(self, notification_id: int) -> Notification | None:
        """Mark single notification as read."""

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read (returns count)."""

    async def notify_share_received(
        self,
        recipient_id: int,
        sender_id: int,
        listing_id: int,
        message: str | None = None
    ) -> Notification:
        """Create 'share received' notification."""

    async def notify_share_imported(
        self,
        sender_id: int,
        importer_id: int,
        listing_id: int
    ) -> Notification:
        """Create 'share imported' notification."""
```

---

## API Endpoints

### Collections API

**File**: `apps/api/dealbrain_api/api/collections.py`

Provides full CRUD operations for collections and items:

```python
@router.post("", response_model=CollectionRead, status_code=201)
async def create_collection(
    payload: CollectionCreate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency)
) -> CollectionRead:
    """Create new collection."""

@router.get("", response_model=list[CollectionRead])
async def list_collections(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
) -> list[CollectionRead]:
    """List user's collections."""

@router.post("/{collection_id}/items", response_model=CollectionItemRead, status_code=201)
async def add_collection_item(
    collection_id: int,
    payload: CollectionItemCreate,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency)
) -> CollectionItemRead:
    """Add item to collection."""

@router.get("/{collection_id}/export")
async def export_collection(
    collection_id: int,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    format: str = Query("json", regex="^(csv|json)$")
) -> Response:
    """Export collection as CSV or JSON."""
```

### User Shares API

**File**: `apps/api/dealbrain_api/api/user_shares.py`

Handles user-to-user sharing with rate limiting:

```python
@router.post("", response_model=UserShareRead, status_code=201)
async def create_user_share(
    payload: CreateUserShareRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency)
) -> UserShareRead:
    """Create user-to-user share (rate limited: 10/hour)."""

@router.get("", response_model=list[UserShareRead])
async def list_user_shares(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False)
) -> list[UserShareRead]:
    """List received shares (inbox)."""

@router.post("/{share_token}/import", response_model=CollectionItemRead, status_code=201)
async def import_shared_deal(
    share_token: str,
    payload: ImportShareRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency)
) -> CollectionItemRead:
    """Import shared deal to collection."""
```

### Public Shares API

**File**: `apps/api/dealbrain_api/api/shares.py`

Public share links with view counting and caching:

```python
@router.get("/{listing_id}/{share_token}", response_model=PublicListingShareRead)
async def get_public_shared_deal(
    listing_id: int,
    share_token: str,
    session: AsyncSession = Depends(session_dependency),
    caching_service: CachingService = Depends(get_caching_service)
) -> PublicListingShareRead:
    """View public share (no auth, cached 24h)."""
```

---

## Repositories

### CollectionRepository

Located in `apps/api/dealbrain_api/repositories/collection_repository.py`

**Purpose**: Abstract data access for collections and items.

**Key Methods**:

```python
class CollectionRepository:
    """Repository for collection data access."""

    async def create(self, user_id: int, name: str, **kwargs) -> Collection:
        """Create collection."""

    async def get_by_id(self, collection_id: int, load_items: bool = False) -> Collection | None:
        """Get collection by ID."""

    async def get_by_user(self, user_id: int, limit: int, offset: int) -> list[Collection]:
        """Get user's collections with pagination."""

    async def update(self, collection: Collection) -> Collection:
        """Update collection."""

    async def delete(self, collection_id: int) -> bool:
        """Delete collection (cascade items)."""

    async def add_item(self, collection_id: int, listing_id: int, **kwargs) -> CollectionItem:
        """Add item to collection with deduplication."""

    async def get_item(self, item_id: int) -> CollectionItem | None:
        """Get item by ID."""

    async def has_item(self, collection_id: int, listing_id: int) -> bool:
        """Check if collection contains listing."""

    async def update_item(self, item: CollectionItem) -> CollectionItem:
        """Update collection item."""

    async def delete_item(self, item_id: int) -> bool:
        """Delete item from collection."""
```

---

## Testing

### Test Structure

Tests are organized by layer:

```
tests/
├── services/
│   ├── test_collections_service.py
│   ├── test_sharing_service.py
│   └── test_notification_service.py
├── repositories/
│   └── test_collection_repository.py
├── api/
│   ├── test_collections_api.py
│   ├── test_user_shares_api.py
│   ├── test_shares_api.py
│   └── test_notifications_api.py
└── integration/
    └── test_sharing_workflow.py
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/services/test_collections_service.py -v

# Run specific test
poetry run pytest tests/services/test_collections_service.py::test_create_collection -v

# Run with coverage
poetry run pytest tests/ --cov=dealbrain_api --cov-report=html
```

### Example Test

```python
@pytest.mark.asyncio
async def test_create_collection(
    session: AsyncSession,
    test_user: User
):
    """Test collection creation."""
    service = CollectionsService(session)

    # Create collection
    collection = await service.create_collection(
        user_id=test_user.id,
        name="Gaming PCs",
        description="Best gaming deals",
        visibility="private"
    )

    # Assertions
    assert collection.id is not None
    assert collection.name == "Gaming PCs"
    assert collection.user_id == test_user.id
    assert collection.visibility == "private"
    assert collection.item_count == 0


@pytest.mark.asyncio
async def test_add_item_prevents_duplicates(
    session: AsyncSession,
    test_user: User,
    test_collection: Collection,
    test_listing: Listing
):
    """Test deduplication on add item."""
    service = CollectionsService(session)

    # Add item first time
    item1 = await service.add_item_to_collection(
        collection_id=test_collection.id,
        listing_id=test_listing.id,
        user_id=test_user.id
    )

    # Try adding same item again
    with pytest.raises(ValueError, match="already exists"):
        await service.add_item_to_collection(
            collection_id=test_collection.id,
            listing_id=test_listing.id,
            user_id=test_user.id
        )
```

---

## Performance Optimization

### Database Optimization

**N+1 Query Prevention:**
- Collections loaded with eager loading (selectin)
- Items relationship uses lazy="selectin"
- User relationships use lazy="joined"

**Query Optimization:**
```python
# ✅ Good: Eager loading
collection = await session.get(Collection, collection_id, options=[
    selectinload(Collection.items),
    selectinload(Collection.user)
])

# ❌ Bad: Lazy loading causes N+1
for collection in collections:
    for item in collection.items:  # N queries!
        print(item.listing.title)
```

### Caching Strategy

**Redis Caching for Public Shares:**
```python
# Cache key pattern: share:listing:{listing_id}:{token}
SHARE_CACHE_TTL_SECONDS = 86400  # 24 hours

# Check cache first
cached = await caching_service.get(cache_key, PublicListingShareRead)
if cached:
    return cached

# If miss, query database and cache
share = await sharing_service.validate_listing_share_token(token)
await caching_service.set(cache_key, share, SHARE_CACHE_TTL_SECONDS)
```

### Rate Limiting

**Sliding Window Rate Limit:**
```python
# Check shares in last hour
used_count = await redis.incr(f"user:{user_id}:shares:{hour}")
remaining = LIMIT - used_count

if used_count > LIMIT:
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded"
    )
```

---

## Common Patterns

### Authorization Pattern

All endpoints check ownership before allowing modifications:

```python
async def verify_ownership(
    user_id: int,
    resource_id: int,
    service: CollectionsService
) -> None:
    """Verify user owns resource."""
    collection = await service.get_collection(resource_id, user_id)
    if not collection:
        raise PermissionError("Not collection owner")
```

### Async/Await Pattern

All database operations are async:

```python
async def add_item(self, collection_id: int, listing_id: int):
    """Add item to collection."""
    async with self.session.begin():
        # Transactional operations
        collection = await self.session.get(Collection, collection_id)
        item = CollectionItem(
            collection_id=collection_id,
            listing_id=listing_id
        )
        self.session.add(item)
        await self.session.flush()
    return item
```

### Error Handling Pattern

Consistent error handling with custom exceptions:

```python
try:
    collection = await service.get_collection(id, user_id)
    if not collection:
        raise HTTPException(404, "Collection not found")
except PermissionError as e:
    raise HTTPException(403, str(e))
except ValueError as e:
    raise HTTPException(400, str(e))
```

---

## Development Workflow

### Adding a New Feature

1. **Add database table** (migration)
   ```bash
   poetry run alembic revision --autogenerate -m "Add new feature"
   ```

2. **Create SQLAlchemy model** in `models/sharing.py`
   ```python
   class NewFeature(Base, TimestampMixin):
       # Define columns and relationships
   ```

3. **Create Pydantic schemas** in `packages/core/schemas/sharing.py`
   ```python
   class NewFeatureCreate(BaseModel):
       # Request schema
   ```

4. **Create repository** (if needed) in `repositories/`
   ```python
   class NewFeatureRepository:
       # Data access methods
   ```

5. **Extend service** in `services/collections_service.py`
   ```python
   async def new_feature_method(self, ...):
       # Business logic
   ```

6. **Add API endpoint** in `api/collections.py`
   ```python
   @router.post("/new-feature")
   async def new_feature_endpoint(...):
       # Request handling
   ```

7. **Write tests** in `tests/`
   ```bash
   pytest tests/services/test_collections_service.py -v
   ```

### Local Development Setup

```bash
# Install dependencies
make setup

# Start Docker stack
make up

# Apply migrations
make migrate

# Seed test data
make seed

# Run dev servers
make api
make web

# Run tests
make test
```

---

## Debugging

### Enable Logging

```python
import logging

logger = logging.getLogger(__name__)

# In your code
logger.info(f"Creating collection: {name}")
logger.warning(f"Duplicate item detected: {listing_id}")
logger.error(f"Database error: {e}")
```

### View API Traces

Use OpenTelemetry traces in Jaeger:
```
http://localhost:16686
```

### Database Inspection

```bash
# Connect to Postgres
psql -h localhost -U deal_brain -d deal_brain

# View collections
SELECT * FROM collection;
SELECT * FROM collection_item;

# Check user shares
SELECT * FROM user_share WHERE recipient_id = 1;
```

### Test Database State

```python
# In tests, inspect final state
await session.refresh(collection)
assert len(collection.items) == 2

# Query directly
result = await session.execute(
    select(CollectionItem).where(
        CollectionItem.collection_id == collection.id
    )
)
items = result.scalars().all()
```

---

## Deployment Considerations

### Database Migrations

Always run migrations before deploying:
```bash
poetry run alembic upgrade head
```

### Environment Variables

Required for production:
```bash
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379
JWT_SECRET=your_secret_key
API_BASE_URL=https://api.dealbrain.com
```

### Monitoring

Track in production:
- API endpoint latencies (Prometheus)
- Database connection pool usage
- Redis cache hit rate
- Notification delivery failures
- Share token validation errors

---

## Contributing

When contributing to Collections & Sharing:

1. Follow existing code patterns
2. Add tests for all changes
3. Run `make format` before committing
4. Add docstrings to new functions
5. Update relevant documentation
6. Test with multiple scenarios

---

## Support

For questions or issues:
1. Check existing tests for patterns
2. Review service implementations
3. Check API endpoint examples
4. Ask in team discussions

Happy coding!
