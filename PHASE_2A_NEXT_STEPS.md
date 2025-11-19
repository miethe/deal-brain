# Phase 2a Implementation - Next Steps

## Summary

Phase 2a database schema changes have been successfully implemented! All required database migrations, models, and tests are in place.

## What Was Implemented ✅

### 1. Database Migration (0030)
- **File:** `/home/user/deal-brain/apps/api/alembic/versions/0030_add_collection_sharing_enhancements.py`
- **Revision:** 0030
- **Parent:** 5dc4b78ba7c1

**Changes:**
- Added 3 discovery indexes to `collection` table
- Created `collection_share_token` table
- Added 4 indexes for efficient token lookups
- Configured CASCADE delete foreign key

### 2. SQLAlchemy Models
- **File:** `/home/user/deal-brain/apps/api/dealbrain_api/models/sharing.py`

**New Model:** `CollectionShareToken`
- Token generation with `generate_token()` class method
- Expiry checking with `is_expired()` instance method
- View tracking with `increment_view_count()` async method

**Updated Model:** `Collection`
- Added `share_tokens` relationship (bidirectional)
- Cascade delete configured

### 3. Model Exports
- **File:** `/home/user/deal-brain/apps/api/dealbrain_api/models/core.py`
- Added `CollectionShareToken` to imports and `__all__` list

### 4. Testing
- **File:** `/home/user/deal-brain/tests/test_collection_sharing_migration.py`
- Model structure tests
- Migration content validation
- Token generation tests

### 5. Verification
- **File:** `/home/user/deal-brain/scripts/verify_phase_2a_schema.py`
- Automated verification script
- ✅ Migration file structure validated (7 indexes confirmed)

## Testing the Migration

### Step 1: Apply the Migration

```bash
# Start the database service
make up

# Apply the migration
make migrate

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 5dc4b78ba7c1 -> 0030, Add collection sharing enhancements for Phase 2a
```

### Step 2: Verify in Database

```bash
# Connect to PostgreSQL
docker exec -it deal-brain-db-1 psql -U dealbrain -d dealbrain

# Check table structure
\d collection_share_token

# Expected columns:
# - id (integer, primary key)
# - collection_id (integer, not null, foreign key)
# - token (text, unique, not null)
# - view_count (integer, default 0)
# - expires_at (timestamp, nullable)
# - created_at (timestamp, not null)
# - updated_at (timestamp, not null)

# Check indexes
\di collection*

# Expected indexes:
# - idx_collection_user_visibility
# - idx_collection_visibility_created
# - idx_collection_visibility_updated
# - ix_collection_share_token_id
# - ix_collection_share_token_token (UNIQUE)
# - idx_collection_share_token_collection
# - idx_collection_share_token_expires

# Check foreign key
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.table_name = 'collection_share_token'
    AND tc.constraint_type = 'FOREIGN KEY';

# Expected: delete_rule = 'CASCADE'
```

### Step 3: Test Rollback

```bash
# Downgrade migration
poetry run alembic downgrade -1

# Expected output:
# INFO  [alembic.runtime.migration] Running downgrade 0030 -> 5dc4b78ba7c1, Remove collection sharing enhancements

# Verify table removed
docker exec -it deal-brain-db-1 psql -U dealbrain -d dealbrain -c "\d collection_share_token"

# Expected: "Did not find any relation named "collection_share_token"."

# Re-apply migration
make migrate
```

### Step 4: Run Unit Tests

```bash
# Run model tests (requires Poetry environment with dependencies)
poetry run pytest tests/test_collection_sharing_migration.py -v

# Expected tests:
# - test_collection_share_token_structure
# - test_collection_share_token_relationships
# - test_generate_token_method
# - test_is_expired_method_*
# - test_repr_method
# - test_collection_has_share_tokens_relationship
# - test_migration_file_exists
# - test_migration_content
```

### Step 5: Verify Model Functionality

```bash
# Run verification script (in Poetry environment)
poetry run python scripts/verify_phase_2a_schema.py

# Expected: All checks pass
```

## Schema Changes Summary

### New Table: `collection_share_token`

```
┌─────────────────────────────────┐
│ collection_share_token          │
├─────────────────────────────────┤
│ id                  INTEGER PK  │
│ collection_id       INTEGER FK  │ → collection.id (CASCADE)
│ token               TEXT UNIQUE │
│ view_count          INTEGER     │ (DEFAULT 0)
│ expires_at          TIMESTAMP   │ (NULLABLE)
│ created_at          TIMESTAMP   │
│ updated_at          TIMESTAMP   │
└─────────────────────────────────┘

Indexes:
- ix_collection_share_token_id (PK)
- ix_collection_share_token_token (UNIQUE)
- idx_collection_share_token_collection
- idx_collection_share_token_expires
```

### Updated Table: `collection`

```
New Indexes:
- idx_collection_user_visibility (user_id, visibility)
- idx_collection_visibility_created (visibility, created_at)
- idx_collection_visibility_updated (visibility, updated_at)
```

## Query Examples

### Generate Share Token

```python
from dealbrain_api.models.sharing import CollectionShareToken

# Generate token
token = CollectionShareToken.generate_token()
# Example: "7xK3mP9qR2vL8nF4wD6jH1cZ5sA0tY7uE3gB9pQ2rM6vN8jL4kF1xC5wT0zS7yU9"

# Create share token
share_token = CollectionShareToken(
    collection_id=1,
    token=token,
    view_count=0,
    expires_at=None  # Never expires
)
```

### Find Share Token by URL

```python
from sqlalchemy import select

# Find token (most common query - uses UNIQUE index)
stmt = select(CollectionShareToken).where(
    CollectionShareToken.token == token
)
share = await session.scalar(stmt)

if share and not share.is_expired():
    await share.increment_view_count(session)
    # Use share.collection to access collection
```

### Discover Recent Public Collections

```python
# Uses idx_collection_visibility_created
stmt = (
    select(Collection)
    .where(Collection.visibility == 'public')
    .order_by(Collection.created_at.desc())
    .limit(20)
)
collections = await session.scalars(stmt)
```

### Find User's Public Collections

```python
# Uses idx_collection_user_visibility
stmt = (
    select(Collection)
    .where(
        Collection.user_id == user_id,
        Collection.visibility == 'public'
    )
    .order_by(Collection.created_at.desc())
)
collections = await session.scalars(stmt)
```

## Performance Expectations

### Token Lookup Performance
- **Index:** UNIQUE index on `token` column
- **Expected:** O(1) lookup time
- **Query Plan:** Index Only Scan on ix_collection_share_token_token

### Discovery Query Performance
- **Index:** Composite index on (visibility, created_at)
- **Expected:** O(log n) lookup time
- **Query Plan:** Index Scan on idx_collection_visibility_created

### Cascade Delete Performance
- **Foreign Key:** CASCADE on collection_id
- **Expected:** O(n) where n = number of share tokens per collection
- **Automatic:** Database handles deletion, no application logic needed

## Security Considerations

### Token Security
- **Entropy:** 64 characters = ~384 bits of entropy
- **Algorithm:** `secrets.token_urlsafe()` (cryptographically secure)
- **Collision Risk:** Negligible with UNIQUE constraint
- **Brute Force:** Computationally infeasible

### Access Control Checklist
- [ ] Verify `collection.visibility` before allowing access
- [ ] Check `share_token.expires_at` before granting access
- [ ] Increment `view_count` only on successful access
- [ ] Validate token exists and is not expired
- [ ] Enforce rate limiting on token lookups (prevent enumeration)

## Next Phase: 2b (Service Layer)

With the database schema in place, Phase 2b will implement:

1. **CollectionShareService**
   - `create_share_token(collection_id, expires_at=None)`
   - `get_by_token(token)`
   - `increment_view_count(token)`
   - `revoke_token(token_id)`
   - `list_collection_tokens(collection_id)`

2. **API Endpoints**
   - `POST /api/collections/{id}/share` - Create share token
   - `GET /api/collections/shared/{token}` - Access shared collection
   - `DELETE /api/collections/share/{token_id}` - Revoke share token
   - `GET /api/collections/{id}/shares` - List collection's share tokens

3. **Access Validation**
   - Middleware for token validation
   - Visibility checks
   - Expiry enforcement

4. **Analytics**
   - View count tracking
   - Popular collections ranking
   - Share metrics dashboard

## Troubleshooting

### Migration Failed

```bash
# Check current migration status
poetry run alembic current

# Check migration history
poetry run alembic history

# If stuck, try manual downgrade
poetry run alembic downgrade base
poetry run alembic upgrade head

# Check database connection
poetry run python -c "from dealbrain_api.db import engine; print(engine.url)"
```

### Table Already Exists

If you see "relation already exists" error:

```bash
# Option 1: Drop the table manually
docker exec -it deal-brain-db-1 psql -U dealbrain -d dealbrain -c "DROP TABLE IF EXISTS collection_share_token CASCADE;"

# Option 2: Mark migration as applied (if table is correct)
poetry run alembic stamp 0030

# Then run migrations
make migrate
```

### Index Already Exists

If you see "relation already exists" for an index:

```bash
# Drop indexes manually
docker exec -it deal-brain-db-1 psql -U dealbrain -d dealbrain -c "
DROP INDEX IF EXISTS idx_collection_user_visibility;
DROP INDEX IF EXISTS idx_collection_visibility_created;
DROP INDEX IF EXISTS idx_collection_visibility_updated;
"

# Then retry migration
poetry run alembic downgrade -1
make migrate
```

## Files Reference

### Implementation Files
```
/home/user/deal-brain/
├── apps/api/
│   ├── alembic/versions/
│   │   └── 0030_add_collection_sharing_enhancements.py
│   └── dealbrain_api/models/
│       ├── sharing.py (updated)
│       └── core.py (updated)
├── tests/
│   └── test_collection_sharing_migration.py
├── scripts/
│   └── verify_phase_2a_schema.py
└── documentation/
    ├── PHASE_2A_IMPLEMENTATION_SUMMARY.md
    └── PHASE_2A_NEXT_STEPS.md (this file)
```

## Success Criteria Checklist ✅

Phase 2a is complete when:

- [x] Migration file created with revision 0030
- [x] `collection_share_token` table schema defined
- [x] 7 indexes defined (3 on collection, 4 on collection_share_token)
- [x] Foreign key with CASCADE delete configured
- [x] CollectionShareToken model created
- [x] Collection model updated with share_tokens relationship
- [x] Models exported from core module
- [x] Unit tests written
- [x] Verification script created
- [ ] Migration applied successfully (`make migrate`)
- [ ] Database schema verified (`\d collection_share_token`)
- [ ] Rollback tested (`alembic downgrade -1`)
- [ ] Unit tests passing (`pytest tests/test_collection_sharing_migration.py`)

## Questions?

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Review the implementation summary: `PHASE_2A_IMPLEMENTATION_SUMMARY.md`
3. Run the verification script: `poetry run python scripts/verify_phase_2a_schema.py`
4. Check migration status: `poetry run alembic current`
5. Examine database directly: `docker exec -it deal-brain-db-1 psql -U dealbrain`

---

**Phase 2a Status:** ✅ Implementation Complete, Ready for Testing
**Next Phase:** 2b - Service Layer & API Endpoints
