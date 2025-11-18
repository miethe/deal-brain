# Phase 3.1 & 3.2 API Testing Guide

This guide provides instructions for testing the newly implemented Collections & Sharing Foundation REST API endpoints.

## Overview

**Phase 3.1: Public Shares Endpoints** (5 SP)
- GET /api/v1/deals/{listing_id}/{share_token} - View public shared deal

**Phase 3.2: User Shares Endpoints** (9 SP)
- POST /api/v1/user-shares - Create user-to-user share
- GET /api/v1/user-shares - List received shares (inbox)
- GET /api/v1/user-shares/{share_token} - Preview shared deal
- POST /api/v1/user-shares/{share_token}/import - Import shared deal to collection

## Prerequisites

1. **Database Setup**: Ensure Phase 1 migrations are applied
   ```bash
   make migrate
   ```

2. **Start Services**: Run the API server
   ```bash
   make api
   # OR with Docker Compose
   make up
   ```

3. **Test Data**: Create test users and listings
   ```bash
   # TODO: Add seed script for test data
   # For now, manually insert test users via SQL or Python REPL
   ```

## Important Notes

### Authentication Placeholder

**IMPORTANT**: Phase 3 includes a **placeholder auth implementation** for development and testing.

- File: `/home/user/deal-brain/apps/api/dealbrain_api/api/user_shares.py`
- Function: `get_current_user()`
- Current behavior: Returns hardcoded user_id=1

**In production**, this MUST be replaced with proper JWT authentication:
```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    # 1. Extract JWT from Authorization header
    # 2. Validate JWT signature and expiry
    # 3. Extract user_id from JWT claims
    # 4. Return CurrentUser with validated user_id
    pass
```

### Redis Caching (Phase 3.1.2)

The public shares endpoint includes **Redis caching infrastructure** but requires implementation:

- File: `/home/user/deal-brain/apps/api/dealbrain_api/api/shares.py`
- Function: `get_redis_client()`
- Current behavior: Returns None (caching disabled)

To enable caching:
```python
async def get_redis_client():
    from redis.asyncio import Redis
    settings = get_settings()
    return await Redis.from_url(settings.redis_url)
```

## Testing Endpoints

### 1. Test Public Share Endpoint (Phase 3.1)

**Endpoint**: `GET /api/v1/deals/{listing_id}/{share_token}`

**Test Case 1: Valid Share**
```bash
# First, create a share in the database (via Python REPL or SQL)
# Then test the endpoint:

curl -X GET "http://localhost:8000/api/v1/deals/1/abc123def456..." \
  -H "Accept: application/json"

# Expected Response (200):
{
  "share_token": "abc123def456...",
  "listing_id": 1,
  "view_count": 1,
  "is_expired": false
}
```

**Test Case 2: Invalid Token**
```bash
curl -X GET "http://localhost:8000/api/v1/deals/1/invalid_token" \
  -H "Accept: application/json"

# Expected Response (404):
{
  "detail": "Share not found"
}
```

**Test Case 3: Expired Share**
```bash
# Create an expired share (expires_at in the past)
# Then test:

curl -X GET "http://localhost:8000/api/v1/deals/1/expired_token" \
  -H "Accept: application/json"

# Expected Response (404):
{
  "detail": "Share has expired"
}
```

**Test Case 4: View Count Increment**
```bash
# Call the same valid share multiple times
curl -X GET "http://localhost:8000/api/v1/deals/1/abc123def456..."
curl -X GET "http://localhost:8000/api/v1/deals/1/abc123def456..."
curl -X GET "http://localhost:8000/api/v1/deals/1/abc123def456..."

# Verify view_count increments each time
```

### 2. Test Create User Share (Phase 3.2.1)

**Endpoint**: `POST /api/v1/user-shares`

**Test Case 1: Valid Share Creation**
```bash
curl -X POST "http://localhost:8000/api/v1/user-shares" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "recipient_id": 2,
    "listing_id": 1,
    "message": "Check out this amazing deal!"
  }'

# Expected Response (201):
{
  "id": 1,
  "sender_id": 1,
  "recipient_id": 2,
  "listing_id": 1,
  "share_token": "abc123def456...",
  "message": "Check out this amazing deal!",
  "shared_at": "2025-11-17T12:00:00Z",
  "expires_at": "2025-12-17T12:00:00Z",
  "viewed_at": null,
  "imported_at": null,
  "is_expired": false,
  "is_viewed": false,
  "is_imported": false
}
```

**Test Case 2: Invalid Recipient**
```bash
curl -X POST "http://localhost:8000/api/v1/user-shares" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": 9999,
    "listing_id": 1,
    "message": "Test"
  }'

# Expected Response (400):
{
  "detail": "Recipient user 9999 not found"
}
```

**Test Case 3: Rate Limiting**
```bash
# Create 11 shares rapidly (rate limit is 10/hour)
for i in {1..11}; do
  curl -X POST "http://localhost:8000/api/v1/user-shares" \
    -H "Content-Type: application/json" \
    -d '{
      "recipient_id": 2,
      "listing_id": 1,
      "message": "Test '$i'"
    }'
done

# Expected: First 10 succeed (201), 11th fails (409):
{
  "detail": "User 1 has exceeded share rate limit (10/hour)"
}
```

### 3. Test List Received Shares (Phase 3.2.2)

**Endpoint**: `GET /api/v1/user-shares`

**Test Case 1: List All Shares**
```bash
curl -X GET "http://localhost:8000/api/v1/user-shares?filter=all&limit=10" \
  -H "Accept: application/json"

# Expected Response (200):
[
  {
    "id": 1,
    "sender_id": 2,
    "recipient_id": 1,
    "listing_id": 123,
    "share_token": "abc123...",
    "message": "Check this out!",
    "shared_at": "2025-11-17T12:00:00Z",
    "expires_at": "2025-12-17T12:00:00Z",
    "viewed_at": null,
    "imported_at": null,
    "is_expired": false,
    "is_viewed": false,
    "is_imported": false
  }
]
```

**Test Case 2: Filter Unviewed Only**
```bash
curl -X GET "http://localhost:8000/api/v1/user-shares?filter=unviewed" \
  -H "Accept: application/json"

# Expected Response (200):
# Only shares with viewed_at=null
```

**Test Case 3: Pagination**
```bash
curl -X GET "http://localhost:8000/api/v1/user-shares?skip=10&limit=5" \
  -H "Accept: application/json"

# Expected Response (200):
# Returns shares 11-15
```

### 4. Test Preview User Share (Phase 3.2.3)

**Endpoint**: `GET /api/v1/user-shares/{share_token}`

**Test Case 1: Preview as Recipient**
```bash
# With authentication (placeholder returns user_id=1)
curl -X GET "http://localhost:8000/api/v1/user-shares/abc123def456..." \
  -H "Accept: application/json"

# Expected Response (200):
# viewed_at is set to current timestamp
{
  "id": 1,
  "sender_id": 2,
  "recipient_id": 1,
  "listing_id": 123,
  "share_token": "abc123...",
  "message": "Check this out!",
  "viewed_at": "2025-11-17T13:00:00Z",
  "is_viewed": true,
  ...
}
```

**Test Case 2: Preview as Anonymous**
```bash
# Without authentication
curl -X GET "http://localhost:8000/api/v1/user-shares/abc123def456..." \
  -H "Accept: application/json"

# Expected Response (200):
# viewed_at remains null
```

**Test Case 3: Invalid Token**
```bash
curl -X GET "http://localhost:8000/api/v1/user-shares/invalid_token" \
  -H "Accept: application/json"

# Expected Response (404):
{
  "detail": "Share not found"
}
```

### 5. Test Import Shared Deal (Phase 3.2.4)

**Endpoint**: `POST /api/v1/user-shares/{share_token}/import`

**Test Case 1: Import to Specific Collection**
```bash
curl -X POST "http://localhost:8000/api/v1/user-shares/abc123def456.../import" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "collection_id": 5
  }'

# Expected Response (201):
{
  "id": 1,
  "collection_id": 5,
  "listing_id": 123,
  "status": "undecided",
  "notes": "Shared: Check this out!",
  "position": null,
  "added_at": "2025-11-17T14:00:00Z",
  "updated_at": "2025-11-17T14:00:00Z"
}
```

**Test Case 2: Import to Default Collection**
```bash
curl -X POST "http://localhost:8000/api/v1/user-shares/abc123def456.../import" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{}'

# Expected Response (201):
# Creates "My Deals" collection if doesn't exist
```

**Test Case 3: Duplicate Import**
```bash
# Import the same share twice
curl -X POST "http://localhost:8000/api/v1/user-shares/abc123def456.../import" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": 5}'

curl -X POST "http://localhost:8000/api/v1/user-shares/abc123def456.../import" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": 5}'

# Expected: Second request fails (409):
{
  "detail": "Listing 123 already exists in collection 5"
}
```

**Test Case 4: Wrong Recipient**
```bash
# Try to import a share meant for user_id=2 while authenticated as user_id=1
# (This requires modifying the placeholder auth to return user_id=1)

curl -X POST "http://localhost:8000/api/v1/user-shares/wrong_recipient_token/import" \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected Response (403):
{
  "detail": "User 1 is not the recipient of this share"
}
```

## API Documentation

### Interactive Swagger UI

The FastAPI server automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Navigate to these URLs to:
- View all available endpoints
- See request/response schemas
- Test endpoints interactively
- View OpenAPI specification

### Example: Using Swagger UI

1. Go to http://localhost:8000/docs
2. Find "shares" or "user-shares" section
3. Click "Try it out" on any endpoint
4. Fill in parameters/request body
5. Click "Execute" to test

## Database Verification

After running tests, verify database state:

```python
# Start Python REPL with database access
poetry run python

from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.models.sharing import ListingShare, UserShare, CollectionItem

async def check_shares():
    async with session_scope() as session:
        # Check listing shares
        listing_shares = await session.execute(select(ListingShare))
        print(f"Listing shares: {listing_shares.scalars().all()}")

        # Check user shares
        user_shares = await session.execute(select(UserShare))
        print(f"User shares: {user_shares.scalars().all()}")

        # Check collection items
        items = await session.execute(select(CollectionItem))
        print(f"Collection items: {items.scalars().all()}")

import asyncio
asyncio.run(check_shares())
```

## Troubleshooting

### Error: "Module not found"
```bash
# Ensure dependencies are installed
poetry install
```

### Error: "Table does not exist"
```bash
# Run migrations
make migrate
```

### Error: "No module named 'redis'"
```bash
# Install Redis dependencies (optional for caching)
poetry add redis
```

### Error: "Authentication required"
- The placeholder auth currently returns user_id=1
- No actual auth token required in Phase 3
- Will be replaced in Phase 4

## Performance Testing

### Load Testing with Apache Bench

Test public share endpoint performance:
```bash
# Create 1000 requests with 10 concurrent connections
ab -n 1000 -c 10 "http://localhost:8000/api/v1/deals/1/abc123def456..."
```

Test user share creation rate limiting:
```bash
# Verify rate limiting works under load
ab -n 15 -c 1 -p user_share_payload.json -T application/json \
  "http://localhost:8000/api/v1/user-shares"
```

## Next Steps (Phase 3.3)

After Phase 3.1 and 3.2 are verified, implement:

1. **Collections Endpoints** (Phase 3.3)
   - POST /v1/collections - Create collection
   - GET /v1/collections - List user's collections
   - GET /v1/collections/{id} - Get collection details
   - PUT /v1/collections/{id} - Update collection
   - DELETE /v1/collections/{id} - Delete collection
   - POST /v1/collections/{id}/items - Add item to collection
   - DELETE /v1/collections/{id}/items/{item_id} - Remove item

2. **Integration Tests** (Phase 3.5)
   - Write pytest tests for all endpoints
   - Test error cases and edge conditions
   - Validate rate limiting
   - Test concurrent requests

3. **Frontend UI** (Phase 4)
   - Public share page with OG tags
   - Share creation modal
   - User inbox UI
   - Collection management UI

## References

- **Service Layer**: `/home/user/deal-brain/apps/api/dealbrain_api/services/sharing_service.py`
- **Integration Service**: `/home/user/deal-brain/apps/api/dealbrain_api/services/integration_service.py`
- **Schemas**: `/home/user/deal-brain/packages/core/dealbrain_core/schemas/sharing.py`
- **Models**: `/home/user/deal-brain/apps/api/dealbrain_api/models/sharing.py`
