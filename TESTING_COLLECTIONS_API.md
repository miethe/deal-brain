# Testing Collections API (Phase 3.3 & 3.4)

This document provides testing instructions for the Collections and Collection Items REST API endpoints.

## Prerequisites

1. Start the API server:
   ```bash
   make up      # Start full Docker Compose stack
   # OR
   make api     # Run API dev server locally
   ```

2. Ensure database migrations are applied:
   ```bash
   make migrate
   ```

3. The API will be available at:
   - Docker: `http://localhost:8020`
   - Local dev: `http://localhost:8000`

## API Endpoints

### Collections Endpoints (Phase 3.3)

#### 1. POST /api/v1/collections (Create Collection)

Create a new collection:

```bash
curl -X POST http://localhost:8020/api/v1/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming PCs",
    "description": "Best gaming deals under $1000",
    "visibility": "private"
  }'
```

Expected Response (201):
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Gaming PCs",
  "description": "Best gaming deals under $1000",
  "visibility": "private",
  "created_at": "2025-11-17T12:00:00Z",
  "updated_at": "2025-11-17T12:00:00Z",
  "item_count": 0,
  "items": null
}
```

#### 2. GET /api/v1/collections (List User's Collections)

List all collections:

```bash
curl http://localhost:8020/api/v1/collections?limit=10
```

Expected Response (200):
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "Gaming PCs",
    "description": "Best gaming deals under $1000",
    "visibility": "private",
    "created_at": "2025-11-17T12:00:00Z",
    "updated_at": "2025-11-17T12:00:00Z",
    "item_count": 0,
    "items": null
  }
]
```

#### 3. GET /api/v1/collections/{id} (Get Collection Details)

Get collection with items:

```bash
curl http://localhost:8020/api/v1/collections/1
```

Expected Response (200):
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Gaming PCs",
  "description": "Best gaming deals under $1000",
  "visibility": "private",
  "created_at": "2025-11-17T12:00:00Z",
  "updated_at": "2025-11-17T12:00:00Z",
  "item_count": 2,
  "items": [
    {
      "id": 1,
      "collection_id": 1,
      "listing_id": 123,
      "status": "shortlisted",
      "notes": "Great deal",
      "position": null,
      "added_at": "2025-11-17T12:30:00Z",
      "updated_at": "2025-11-17T12:30:00Z"
    }
  ]
}
```

#### 4. PATCH /api/v1/collections/{id} (Update Collection)

Update collection metadata:

```bash
curl -X PATCH http://localhost:8020/api/v1/collections/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Best Gaming PCs",
    "visibility": "public"
  }'
```

Expected Response (200):
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Best Gaming PCs",
  "description": "Best gaming deals under $1000",
  "visibility": "public",
  "created_at": "2025-11-17T12:00:00Z",
  "updated_at": "2025-11-17T13:00:00Z",
  "item_count": 2,
  "items": null
}
```

#### 5. DELETE /api/v1/collections/{id} (Delete Collection)

Delete collection (cascade deletes items):

```bash
curl -X DELETE http://localhost:8020/api/v1/collections/1
```

Expected Response (204): No content

### Collection Items Endpoints (Phase 3.4)

#### 1. POST /api/v1/collections/{id}/items (Add Item)

Add listing to collection:

```bash
curl -X POST http://localhost:8020/api/v1/collections/1/items \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": 123,
    "status": "shortlisted",
    "notes": "Great CPU/GPU combo for the price"
  }'
```

Expected Response (201):
```json
{
  "id": 1,
  "collection_id": 1,
  "listing_id": 123,
  "status": "shortlisted",
  "notes": "Great CPU/GPU combo for the price",
  "position": null,
  "added_at": "2025-11-17T12:30:00Z",
  "updated_at": "2025-11-17T12:30:00Z"
}
```

Test deduplication (should return 409):

```bash
# Add same listing again
curl -X POST http://localhost:8020/api/v1/collections/1/items \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": 123,
    "status": "shortlisted"
  }'
```

Expected Response (409):
```json
{
  "detail": "Listing 123 already exists in collection 1"
}
```

#### 2. PATCH /api/v1/collections/{id}/items/{item_id} (Update Item)

Update item status:

```bash
curl -X PATCH http://localhost:8020/api/v1/collections/1/items/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "bought",
    "notes": "Purchased on 2025-11-17, arrived in perfect condition"
  }'
```

Expected Response (200):
```json
{
  "id": 1,
  "collection_id": 1,
  "listing_id": 123,
  "status": "bought",
  "notes": "Purchased on 2025-11-17, arrived in perfect condition",
  "position": null,
  "added_at": "2025-11-17T12:30:00Z",
  "updated_at": "2025-11-17T14:00:00Z"
}
```

#### 3. DELETE /api/v1/collections/{id}/items/{item_id} (Remove Item)

Remove item from collection:

```bash
curl -X DELETE http://localhost:8020/api/v1/collections/1/items/1
```

Expected Response (204): No content

#### 4. GET /api/v1/collections/{id}/export (Export Collection)

Export as CSV:

```bash
curl http://localhost:8020/api/v1/collections/1/export?format=csv \
  -o collection_1.csv
```

Expected Response (200):
```csv
name,price,cpu,gpu,cpu_mark_ratio,score,status,notes
"Gaming PC",599.99,"Intel i5-12400","GTX 1650",85.50,4.20,"shortlisted","Great deal"
```

Export as JSON:

```bash
curl http://localhost:8020/api/v1/collections/1/export?format=json \
  -o collection_1.json
```

Expected Response (200):
```json
{
  "collection": {
    "id": 1,
    "name": "Gaming PCs",
    "description": "Best gaming deals under $1000",
    "visibility": "private",
    "created_at": "2025-11-17T12:00:00Z",
    "updated_at": "2025-11-17T12:00:00Z",
    "item_count": 1
  },
  "items": [
    {
      "id": 1,
      "listing_id": 123,
      "status": "shortlisted",
      "notes": "Great deal",
      "position": null,
      "added_at": "2025-11-17T12:30:00Z",
      "updated_at": "2025-11-17T12:30:00Z",
      "listing": {
        "name": "Gaming PC",
        "price": 599.99,
        "cpu": "Intel i5-12400",
        "gpu": "GTX 1650",
        "cpu_mark_ratio": 85.50,
        "score": 4.20
      }
    }
  ]
}
```

## Test Scenarios

### Scenario 1: Create and Manage a Collection

1. Create a collection: `POST /collections`
2. List collections: `GET /collections` (should see new collection)
3. Get collection details: `GET /collections/{id}` (should show 0 items)
4. Update collection: `PATCH /collections/{id}` (change visibility)
5. Verify update: `GET /collections/{id}` (should show updated_at changed)

### Scenario 2: Add and Manage Items

1. Create a collection: `POST /collections`
2. Add item: `POST /collections/{id}/items` (listing_id must exist)
3. Get collection: `GET /collections/{id}` (should show 1 item)
4. Update item: `PATCH /collections/{id}/items/{item_id}` (change status to "bought")
5. Remove item: `DELETE /collections/{id}/items/{item_id}`
6. Get collection: `GET /collections/{id}` (should show 0 items)

### Scenario 3: Export Collection

1. Create a collection: `POST /collections`
2. Add multiple items: `POST /collections/{id}/items` (repeat with different listing_id)
3. Export as CSV: `GET /collections/{id}/export?format=csv`
4. Export as JSON: `GET /collections/{id}/export?format=json`
5. Verify both files contain all items

### Scenario 4: Error Handling

1. Get non-existent collection: `GET /collections/999` (should return 404)
2. Update non-existent collection: `PATCH /collections/999` (should return 404)
3. Delete non-existent collection: `DELETE /collections/999` (should return 404)
4. Add duplicate item: `POST /collections/{id}/items` with same listing_id twice (should return 409)
5. Add item with invalid listing_id: `POST /collections/{id}/items` with listing_id=999999 (should return 400)

## Interactive API Documentation

Visit the auto-generated API docs:

- Swagger UI: `http://localhost:8020/docs`
- ReDoc: `http://localhost:8020/redoc`

Navigate to the "collections" tag to see all endpoints with:
- Request/response schemas
- Interactive testing interface
- Example payloads
- Error response documentation

## Common Issues

### Issue: 404 Not Found for all endpoints

**Cause**: Router not registered in API __init__.py

**Solution**: Verify `collections` is imported and registered:
```python
from . import collections
router.include_router(collections.router)
```

### Issue: 409 Conflict when adding items

**Cause**: Listing already exists in collection (deduplication check)

**Solution**: This is expected behavior. Remove the existing item first or use a different listing_id.

### Issue: 400 Bad Request when adding items

**Cause**: Listing doesn't exist in the database

**Solution**: Create a listing first or use an existing listing_id. Check available listings:
```bash
curl http://localhost:8020/api/v1/listings?limit=10
```

### Issue: CSV export shows empty listing data

**Cause**: Items don't have loaded listing relationships

**Solution**: This might indicate the service layer isn't eager loading listings. Check `CollectionsService.get_collection_items()` loads listings with `load_listings=True`.

## Next Steps: Phase 3.5 (Integration Tests)

After verifying all endpoints work manually, Phase 3.5 will add:

1. **Unit tests** for service layer methods
2. **Integration tests** for API endpoints
3. **Test fixtures** for collections and items
4. **Test coverage** for error scenarios
5. **Performance tests** for export endpoints with large collections

Test file location: `/home/user/deal-brain/tests/api/test_collections_api.py`
