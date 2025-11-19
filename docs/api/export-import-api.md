---
title: "Export/Import API Reference"
description: "Complete REST API documentation for Deal Brain's export and import functionality, including single listings and full collections with duplicate detection and merge strategies."
audience: [developers, ai-agents]
tags: [api, export, import, listings, collections, rest, endpoints, json, schema]
created: 2025-11-19
updated: 2025-11-19
category: "api-documentation"
status: published
related:
  - /docs/schemas/export-format-reference.md
  - /docs/api/deal-builder-api-specification.md
  - /docs/guides/export-import-user-guide.md
---

# Export/Import API Reference

## Overview

The Export/Import API enables users to export listings and collections as portable JSON files and import them into other Deal Brain instances. All exports use the v1.0.0 schema which is locked for stability and backward compatibility.

### Key Features

- **Single Listing Export**: Export any listing as portable JSON with all data
- **Collection Export**: Export entire collections with all items and metadata
- **Schema Validation**: All imports validated against v1.0.0 schema
- **Duplicate Detection**: Fuzzy matching detects potential duplicates before import
- **Preview System**: Review imports before confirming with 30-minute TTL
- **Merge Strategies**: Choose how to handle duplicates (create new, update, merge items)
- **Custom Fields**: Full support for custom field data preservation
- **Performance Metrics**: Complete preservation of CPU Mark scores and calculated metrics

---

## Base URL & Authentication

**Base URL**: `/api/v1`

**Authentication**: Bearer token (JWT) - required for user-scoped operations

### Headers

All requests require:
```http
Content-Type: application/json
Accept: application/json
```

Authenticated endpoints require:
```http
Authorization: Bearer {token}
```

**Note**: Currently using placeholder auth (hardcoded user_id=1). Production will use JWT validation.

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "request_id": "unique-request-identifier"
}
```

### HTTP Status Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 200 | OK | Successful read or preview creation |
| 201 | Created | Successful import confirmation (listing/collection created) |
| 304 | Not Modified | Cache hit (ETags) |
| 400 | Bad Request | Invalid JSON format, missing required fields, invalid merge strategy |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | User lacks access to resource (not owner) |
| 404 | Not Found | Listing/collection not found, or preview expired |
| 422 | Unprocessable Entity | Schema validation failed (invalid according to v1.0.0) |
| 500 | Internal Server Error | Unexpected server error |

---

## Listing Export Endpoints

### GET /listings/{id}/export

Export a single listing as portable JSON file (v1.0.0 schema).

**Authentication**: Optional (public listings can be exported without auth)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"json"` | Export format (only `"json"` supported) |

**Responses**:

#### 200 - Success

```
Content-Type: application/json
Content-Disposition: attachment; filename="deal-brain-listing-{id}-{date}.json"
```

Returns the complete listing export in v1.0.0 format.

**Example Response:**
```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-19T12:34:56.789Z",
    "exported_by": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "type": "deal"
  },
  "data": {
    "listing": {
      "id": 42,
      "title": "Intel Core i7 Gaming PC",
      "price_usd": 799.99,
      "condition": "like_new",
      "status": "active",
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-18T14:20:00Z"
    },
    "valuation": { /* ... */ },
    "performance": { /* ... */ },
    "metadata": { /* ... */ }
  }
}
```

#### 403 - Forbidden

User does not have access to this listing (not owner and not public).

```json
{
  "detail": "User does not have access to this listing"
}
```

#### 404 - Not Found

Listing does not exist.

```json
{
  "detail": "Listing 42 not found"
}
```

#### 500 - Internal Server Error

Unexpected server error during export.

```json
{
  "detail": "Export failed: database connection error"
}
```

**Examples**:

```bash
# Export listing 42 as JSON
curl -H "Authorization: Bearer token" \
  https://api.dealbrain.io/api/v1/listings/42/export?format=json \
  -o listing-42.json

# Export with default parameters
curl https://api.dealbrain.io/api/v1/listings/42/export \
  -o listing-42.json
```

---

## Listing Import Endpoints

### POST /listings/import

Import a listing from JSON with validation and duplicate detection.

**Authentication**: Required

**Request Format**:

Either file upload or raw JSON data (not both).

#### Option 1: File Upload

```
Content-Type: multipart/form-data
```

**Form Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | file | Yes* | JSON file (UTF-8 encoded) |

*Required if `data` parameter not provided

#### Option 2: Raw JSON Data

```
Content-Type: application/x-www-form-urlencoded
```

**Form Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `data` | string | Yes* | Raw JSON string (escaped) |

*Required if `file` parameter not provided

**Responses**:

#### 200 - Success (Preview Created)

```json
{
  "preview_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "deal",
  "parsed_data": {
    "listing": {
      "id": 42,
      "title": "Gaming PC",
      "price_usd": 799.99,
      "condition": "like_new",
      "status": "active"
    }
  },
  "duplicates": [
    {
      "entity_id": 41,
      "entity_type": "listing",
      "match_score": 0.95,
      "match_reason": "Similar title (95%) and price (92%)",
      "entity_data": {
        "id": 41,
        "title": "Gaming PC - Intel i7",
        "price_usd": 799.99,
        "seller": "TechDeals"
      }
    }
  ],
  "expires_at": "2025-11-19T13:04:56.789Z"
}
```

**Preview Expiration**: Previews expire after 30 minutes. User must confirm import within this window.

#### 400 - Bad Request

Invalid JSON format or missing required parameters.

```json
{
  "detail": "Invalid JSON format: Expecting value: line 1 column 1 (char 0)"
}
```

```json
{
  "detail": "Either 'file' or 'data' parameter required"
}
```

```json
{
  "detail": "Empty file uploaded"
}
```

#### 422 - Unprocessable Entity

Schema validation failed - JSON doesn't match v1.0.0 schema.

```json
{
  "detail": "Invalid export schema: 1 validation error for PortableDealExport\ndeal_brain_export\n  value is not a valid dictionary (type=type_error.dict)\n"
}
```

#### 500 - Internal Server Error

```json
{
  "detail": "Import failed: database error during duplicate detection"
}
```

**Examples**:

```bash
# Import from file upload
curl -X POST \
  -H "Authorization: Bearer token" \
  -F "file=@listing.json" \
  https://api.dealbrain.io/api/v1/listings/import

# Import from raw JSON
curl -X POST \
  -H "Authorization: Bearer token" \
  -d 'data={"deal_brain_export":{"version":"1.0.0","type":"deal","exported_at":"2025-11-19T12:00:00Z"},"data":{"listing":{"id":1,"title":"PC","price_usd":100,"condition":"good","status":"active","created_at":"2025-11-19T12:00:00Z","updated_at":"2025-11-19T12:00:00Z"}}}' \
  https://api.dealbrain.io/api/v1/listings/import
```

---

### POST /listings/import/confirm

Confirm and execute a listing import from a preview.

**Authentication**: Required

**Request Body**:

```json
{
  "preview_id": "550e8400-e29b-41d4-a716-446655440000",
  "merge_strategy": "create_new",
  "target_listing_id": null
}
```

**Request Schema**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `preview_id` | string | Yes | Preview ID from `/listings/import` response |
| `merge_strategy` | string | Yes | Strategy for handling duplicates |
| `target_listing_id` | integer | No | Required if strategy is `"update_existing"` |

**Merge Strategies**:

| Strategy | Description | When to Use | Requirements |
|----------|-------------|------------|--------------|
| `create_new` | Always create new listing | Default, no duplicates or want separate copy | None |
| `update_existing` | Update existing listing with import data | Replace old data with new | `target_listing_id` required |
| `skip` | Don't import (error) | User changed mind | None |

**Responses**:

#### 201 - Created (Import Successful)

```json
{
  "id": 123,
  "title": "Gaming PC",
  "price_usd": 799.99,
  "status": "active",
  "created_at": "2025-11-19T12:00:00Z",
  "updated_at": "2025-11-19T12:00:00Z"
}
```

New listing was created with import data.

#### 400 - Bad Request

Invalid merge strategy, missing required parameter, or preview expired.

```json
{
  "detail": "target_listing_id required for update_existing strategy"
}
```

```json
{
  "detail": "Preview not found or expired"
}
```

```json
{
  "detail": "Import skipped by user"
}
```

#### 500 - Internal Server Error

```json
{
  "detail": "Import confirmation failed: database transaction error"
}
```

**Examples**:

```bash
# Confirm import with create_new strategy
curl -X POST \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "preview_id": "550e8400-e29b-41d4-a716-446655440000",
    "merge_strategy": "create_new"
  }' \
  https://api.dealbrain.io/api/v1/listings/import/confirm

# Confirm with update_existing strategy
curl -X POST \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "preview_id": "550e8400-e29b-41d4-a716-446655440000",
    "merge_strategy": "update_existing",
    "target_listing_id": 41
  }' \
  https://api.dealbrain.io/api/v1/listings/import/confirm
```

---

## Collection Export Endpoints

### GET /collections/{id}/export

Export a collection with all items as portable JSON file (v1.0.0 schema).

**Authentication**: Required (user must own collection)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"json"` | Export format (only `"json"` supported) |

**Responses**:

#### 200 - Success

```
Content-Type: application/json
Content-Disposition: attachment; filename="deal-brain-collection-{id}-{date}.json"
```

Returns the complete collection export in v1.0.0 format.

**Example Response:**
```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-19T12:34:56.789Z",
    "exported_by": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "type": "collection"
  },
  "data": {
    "collection": {
      "id": 5,
      "name": "Best Gaming Deals - Q4 2025",
      "description": "Curated collection of excellent gaming PC deals",
      "visibility": "public",
      "created_at": "2025-11-01T10:00:00Z",
      "updated_at": "2025-11-19T12:00:00Z"
    },
    "items": [
      {
        "listing": {
          "listing": { /* ... */ },
          "valuation": { /* ... */ },
          "performance": { /* ... */ }
        },
        "status": "active",
        "notes": "Excellent price for specs",
        "position": 1,
        "added_at": "2025-11-15T10:30:00Z"
      }
    ]
  }
}
```

#### 403 - Forbidden

User doesn't own this collection.

```json
{
  "detail": "User does not have access to this collection"
}
```

#### 404 - Not Found

Collection doesn't exist.

```json
{
  "detail": "Collection 5 not found"
}
```

#### 500 - Internal Server Error

```json
{
  "detail": "Export failed: error exporting items"
}
```

**Examples**:

```bash
# Export collection 5
curl -H "Authorization: Bearer token" \
  https://api.dealbrain.io/api/v1/collections/5/export \
  -o collection-5.json
```

---

## Collection Import Endpoints

### POST /collections/import

Import a collection from JSON with validation and duplicate detection.

**Authentication**: Required

**Request Format**:

Either file upload or raw JSON data (not both).

#### Option 1: File Upload

```
Content-Type: multipart/form-data
```

**Form Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | file | Yes* | JSON file (UTF-8 encoded) |

#### Option 2: Raw JSON Data

```
Content-Type: application/x-www-form-urlencoded
```

**Form Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `data` | string | Yes* | Raw JSON string (escaped) |

**Responses**:

#### 200 - Success (Preview Created)

```json
{
  "preview_id": "550e8400-e29b-41d4-a716-446655440001",
  "type": "collection",
  "parsed_data": {
    "collection": {
      "id": 5,
      "name": "Gaming Deals",
      "description": "Great gaming PC deals",
      "visibility": "private",
      "item_count": 3
    }
  },
  "duplicates": [
    {
      "entity_id": 4,
      "entity_type": "collection",
      "match_score": 0.85,
      "match_reason": "Similar name (85%)",
      "entity_data": {
        "id": 4,
        "name": "Gaming PC Deals",
        "description": "Best gaming deals",
        "item_count": 5
      }
    }
  ],
  "expires_at": "2025-11-19T13:04:56.789Z"
}
```

#### 400 - Bad Request

Invalid JSON format or missing parameters.

```json
{
  "detail": "Invalid JSON format: Expecting value: line 1 column 1"
}
```

#### 422 - Unprocessable Entity

Schema validation failed.

```json
{
  "detail": "Invalid export schema: collection name required"
}
```

#### 500 - Internal Server Error

```json
{
  "detail": "Import failed: database error"
}
```

**Examples**:

```bash
# Import from file
curl -X POST \
  -H "Authorization: Bearer token" \
  -F "file=@collection.json" \
  https://api.dealbrain.io/api/v1/collections/import
```

---

### POST /collections/import/confirm

Confirm and execute a collection import from a preview.

**Authentication**: Required

**Request Body**:

```json
{
  "preview_id": "550e8400-e29b-41d4-a716-446655440001",
  "merge_strategy": "create_new",
  "target_collection_id": null
}
```

**Request Schema**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `preview_id` | string | Yes | Preview ID from `/collections/import` response |
| `merge_strategy` | string | Yes | Strategy for handling duplicates |
| `target_collection_id` | integer | No | Required if strategy is `"merge_items"` |

**Merge Strategies**:

| Strategy | Description | When to Use | Requirements |
|----------|-------------|------------|--------------|
| `create_new` | Create new collection with all items | Default, or want separate copy | None |
| `merge_items` | Add items to existing collection | Combine with existing collection | `target_collection_id` required |
| `skip` | Don't import (error) | User changed mind | None |

**Responses**:

#### 201 - Created (Import Successful)

```json
{
  "id": 6,
  "name": "Gaming Deals",
  "description": "Great gaming PC deals",
  "visibility": "private",
  "item_count": 3,
  "created_at": "2025-11-19T12:00:00Z",
  "updated_at": "2025-11-19T12:00:00Z"
}
```

#### 400 - Bad Request

Invalid merge strategy or missing required parameter.

```json
{
  "detail": "target_collection_id required for merge_items strategy"
}
```

#### 404 - Not Found

Preview expired or doesn't exist.

```json
{
  "detail": "Preview not found or expired"
}
```

#### 500 - Internal Server Error

```json
{
  "detail": "Import confirmation failed: transaction error"
}
```

**Examples**:

```bash
# Confirm import with create_new
curl -X POST \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "preview_id": "550e8400-e29b-41d4-a716-446655440001",
    "merge_strategy": "create_new"
  }' \
  https://api.dealbrain.io/api/v1/collections/import/confirm

# Confirm with merge_items
curl -X POST \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "preview_id": "550e8400-e29b-41d4-a716-446655440001",
    "merge_strategy": "merge_items",
    "target_collection_id": 5
  }' \
  https://api.dealbrain.io/api/v1/collections/import/confirm
```

---

## Duplicate Detection

### How Duplicate Detection Works

The import preview includes duplicate detection to help users avoid creating duplicates.

#### For Listings

Matches are found using three methods:

1. **Exact Title + Seller Match** (Score: 1.0)
   - Title and seller must match exactly
   - Highest confidence match

2. **URL Match** (Score: 1.0)
   - Listing URL matches exactly
   - Indicates same marketplace listing

3. **Fuzzy Title + Price Similarity** (Score: 0.7-1.0)
   - Title similarity (Jaccard token-based)
   - Price similarity (percentage difference)
   - Combined score: 70% title + 30% price
   - Only returned if combined > 0.7

**Example Duplicate Match:**
```json
{
  "entity_id": 41,
  "entity_type": "listing",
  "match_score": 0.95,
  "match_reason": "Similar title (95%) and price (92%)",
  "entity_data": {
    "id": 41,
    "title": "Intel Core i7 Gaming PC",
    "price_usd": 789.99,
    "seller": "TechDeals Co."
  }
}
```

#### For Collections

Matches are found by name:

1. **Exact Name Match** (Score: 1.0)
   - Collection name matches exactly (user-scoped)

2. **Fuzzy Name Similarity** (Score: 0.7-1.0)
   - Token-based name similarity
   - Only if > 0.7
   - User-scoped (doesn't match other users' collections)

**Example Duplicate Match:**
```json
{
  "entity_id": 4,
  "entity_type": "collection",
  "match_score": 0.85,
  "match_reason": "Similar name (85%)",
  "entity_data": {
    "id": 4,
    "name": "Gaming PC Deals",
    "item_count": 5
  }
}
```

### Using Duplicate Information

1. User reviews preview with duplicates
2. If duplicate found:
   - Choose `merge_strategy: "create_new"` to create separate copy anyway
   - Choose `merge_strategy: "update_existing"` to replace existing data
   - Choose `merge_strategy: "skip"` to cancel import
3. If no duplicates or satisfied with action, proceed with confirmation

---

## Schema Validation

### Validation on Import

All imports are validated against the v1.0.0 JSON Schema. Validation includes:

- **Structure**: Required fields present, correct object/array types
- **Types**: Fields have correct data types (string, number, datetime, etc.)
- **Enums**: Enum fields use valid values
- **Constraints**: String lengths, number ranges
- **Datetime Format**: ISO 8601 timestamps are valid
- **UUID Format**: UUIDs are valid v4 format

### Schema Version Validation

- Only v1.0.0 is currently accepted
- Version must match exactly (no minor version variations)
- Error message indicates if version is missing or incompatible

**Error Example:**
```json
{
  "detail": "Invalid export schema: Incompatible schema version: 0.9.0. Only v1.0.0 is currently supported. Migration from older versions may be required."
}
```

### What's NOT Validated

- **Duplicate content**: System detects duplicates but doesn't prevent import
- **URL liveness**: URLs are not checked to be valid or reachable
- **CPU Mark scores**: Not validated against known databases
- **Custom field structure**: Arbitrary custom fields are accepted

---

## Rate Limiting

Export and import operations are currently unlimited. If rate limiting is implemented:

- **Export**: 100 requests per minute per user
- **Import preview**: 100 requests per minute per user
- **Import confirm**: No limit (already have preview)

Rate limit headers will be added to responses when implemented:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1637354456
```

---

## Complete Workflow Examples

### Single Listing Export/Import Workflow

```bash
# 1. Export listing 42
curl -H "Authorization: Bearer token" \
  https://api.dealbrain.io/api/v1/listings/42/export \
  -o gaming-pc.json

# 2. Transfer file to another system...

# 3. Import on another system (preview)
curl -X POST \
  -H "Authorization: Bearer token" \
  -F "file=@gaming-pc.json" \
  https://other-api.dealbrain.io/api/v1/listings/import \
  -o preview.json

# 4. Review preview, then confirm
PREVIEW_ID=$(jq -r '.preview_id' preview.json)

curl -X POST \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d "{\"preview_id\":\"$PREVIEW_ID\",\"merge_strategy\":\"create_new\"}" \
  https://other-api.dealbrain.io/api/v1/listings/import/confirm
```

### Collection Export/Import Workflow

```bash
# 1. Export collection 5
curl -H "Authorization: Bearer token" \
  https://api.dealbrain.io/api/v1/collections/5/export \
  -o gaming-deals.json

# 2. Import on another system
curl -X POST \
  -H "Authorization: Bearer token" \
  -F "file=@gaming-deals.json" \
  https://other-api.dealbrain.io/api/v1/collections/import \
  -o preview.json

# 3. Confirm import
PREVIEW_ID=$(jq -r '.preview_id' preview.json)

curl -X POST \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d "{\"preview_id\":\"$PREVIEW_ID\",\"merge_strategy\":\"create_new\"}" \
  https://other-api.dealbrain.io/api/v1/collections/import/confirm
```

---

## Integration Examples

### JavaScript/Node.js

```javascript
// Export listing
async function exportListing(listingId, token) {
  const response = await fetch(`/api/v1/listings/${listingId}/export`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// Import with preview
async function importListing(jsonData, token) {
  const formData = new FormData();
  formData.append('data', JSON.stringify(jsonData));

  const response = await fetch('/api/v1/listings/import', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  return response.json();
}

// Confirm import
async function confirmImport(previewId, mergeStrategy, token) {
  const response = await fetch('/api/v1/listings/import/confirm', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      preview_id: previewId,
      merge_strategy: mergeStrategy
    })
  });
  return response.json();
}
```

### Python

```python
import requests
import json

# Export listing
def export_listing(listing_id, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'/api/v1/listings/{listing_id}/export',
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Import with preview
def import_listing(json_data, token):
    headers = {'Authorization': f'Bearer {token}'}
    files = {'data': ('listing.json', json.dumps(json_data), 'application/json')}

    response = requests.post(
        '/api/v1/listings/import',
        headers=headers,
        files=files
    )
    response.raise_for_status()
    return response.json()

# Confirm import
def confirm_import(preview_id, merge_strategy, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'preview_id': preview_id,
        'merge_strategy': merge_strategy
    }

    response = requests.post(
        '/api/v1/listings/import/confirm',
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()
```

---

## Related Documentation

- **Schema Reference**: See `/docs/schemas/export-format-reference.md` for field details
- **JSON Schema File**: See `/docs/schemas/deal-brain-export-schema-v1.0.0.json` for validation schema
- **User Guide**: See `/docs/guides/export-import-user-guide.md` for user-facing instructions
- **Collections API**: See `/docs/api/collections-sharing-api.md` for collection endpoints
- **Main API Spec**: See `/docs/api/deal-builder-api-specification.md` for other endpoints
