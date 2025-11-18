---
title: "Collections & Sharing API Reference"
description: "Complete REST API documentation for Deal Brain's Collections and Sharing features including user-to-user sharing, public share links, collections management, and notifications."
audience: [developers, ai-agents]
tags: [api, collections, sharing, rest, endpoints, integration, authentication]
created: 2025-11-18
updated: 2025-11-18
category: "api-documentation"
status: published
related:
  - /docs/guides/collections-sharing-user-guide.md
  - /docs/development/collections-sharing-developer-guide.md
  - /docs/api/deal-builder-api-specification.md
---

# Collections & Sharing API Reference

## Overview

The Collections & Sharing API enables users to organize deals into personal collections, share listings with other users or via public links, and receive notifications about shared deals. This specification documents all REST API endpoints.

### Key Features

- **Collections**: Organize listings into custom, named collections with private/public visibility
- **User-to-User Sharing**: Share deals directly with other users with optional messages
- **Public Share Links**: Generate secure, token-based shareable links for any listing
- **Notifications**: Real-time notifications for received shares and imported deals
- **Export**: Export collections as CSV or JSON for offline comparison
- **Rate Limiting**: Built-in rate limiting on share operations

### Architecture

```
Frontend (Next.js) ↔ API Layer (FastAPI)
                     ↓
                Service Layer (CollectionsService, SharingService)
                     ↓
                Repository Layer
                     ↓
                Database (PostgreSQL)
```

---

## Base URL & Versioning

**Base URL**: `/api/v1`

**API Version**: 1.0

**Protocol**: HTTPS (required in production)

**Authentication**: Bearer token (JWT)

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

---

## Collections Endpoints

### POST /collections

Create a new collection.

**Authentication**: Required

**Request**:
```json
{
  "name": "Gaming PCs",
  "description": "Best gaming deals for 2025",
  "visibility": "private"
}
```

**Request Schema**:
```typescript
interface CollectionCreate {
  name: string;           // Required, 1-100 chars
  description?: string;   // Optional, max 1000 chars
  visibility?: "private" | "unlisted" | "public";  // Default: "private"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Gaming PCs",
  "description": "Best gaming deals for 2025",
  "visibility": "private",
  "created_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T12:00:00Z",
  "item_count": 0,
  "items": null
}
```

**Response Schema**:
```typescript
interface CollectionRead {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  visibility: "private" | "unlisted" | "public";
  created_at: string;
  updated_at: string;
  item_count: number;
  items?: CollectionItemRead[] | null;
}
```

**Error Responses**:
- `400 Bad Request` - Invalid request body (validation error)
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming PCs",
    "description": "Best gaming deals",
    "visibility": "private"
  }'
```

---

### GET /collections

List user's collections.

**Authentication**: Required

**Query Parameters**:
- `skip` (integer, optional): Number of collections to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number to return, 1-100 (default: 20)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "Gaming PCs",
    "description": "Best gaming deals",
    "visibility": "private",
    "created_at": "2025-11-18T12:00:00Z",
    "updated_at": "2025-11-18T12:00:00Z",
    "item_count": 5,
    "items": null
  },
  {
    "id": 2,
    "user_id": 1,
    "name": "Office Builds",
    "description": "Work PC candidates",
    "visibility": "private",
    "created_at": "2025-11-17T10:30:00Z",
    "updated_at": "2025-11-17T10:30:00Z",
    "item_count": 3,
    "items": null
  }
]
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/collections?limit=10&skip=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /collections/{collection_id}

Get collection details with items.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID

**Response** (200 OK):
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Gaming PCs",
  "description": "Best gaming deals",
  "visibility": "private",
  "created_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T12:00:00Z",
  "item_count": 2,
  "items": [
    {
      "id": 1,
      "collection_id": 1,
      "listing_id": 123,
      "status": "shortlisted",
      "notes": "Great CPU, good price",
      "position": null,
      "added_at": "2025-11-18T12:00:00Z",
      "updated_at": "2025-11-18T12:00:00Z"
    },
    {
      "id": 2,
      "collection_id": 1,
      "listing_id": 124,
      "status": "undecided",
      "notes": null,
      "position": null,
      "added_at": "2025-11-18T11:30:00Z",
      "updated_at": "2025-11-18T11:30:00Z"
    }
  ]
}
```

**Item Status Values**:
- `undecided` - Still evaluating
- `shortlisted` - Top candidate
- `rejected` - Ruled out
- `bought` - Purchased

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `404 Not Found` - Collection not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/collections/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### PATCH /collections/{collection_id}

Update collection metadata.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID

**Request** (all fields optional):
```json
{
  "name": "Best Gaming PCs 2025",
  "description": "Top gaming deals",
  "visibility": "public"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Best Gaming PCs 2025",
  "description": "Top gaming deals",
  "visibility": "public",
  "created_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T13:00:00Z",
  "item_count": 2,
  "items": null
}
```

**Error Responses**:
- `400 Bad Request` - Invalid request (validation error)
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `404 Not Found` - Collection not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X PATCH http://localhost:8000/api/v1/collections/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Best Gaming PCs",
    "visibility": "public"
  }'
```

---

### DELETE /collections/{collection_id}

Delete collection and all its items.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID

**Response** (204 No Content):
```
(empty body)
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `404 Not Found` - Collection not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/collections/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Collection Items Endpoints

### POST /collections/{collection_id}/items

Add item to collection.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID

**Request**:
```json
{
  "listing_id": 123,
  "status": "shortlisted",
  "notes": "Great value for gaming",
  "position": null
}
```

**Request Schema**:
```typescript
interface CollectionItemCreate {
  listing_id: number;      // Required
  status?: "undecided" | "shortlisted" | "rejected" | "bought"; // Default: "undecided"
  notes?: string;          // Optional, max 500 chars
  position?: number | null; // Optional, for ordering
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "collection_id": 1,
  "listing_id": 123,
  "status": "shortlisted",
  "notes": "Great value for gaming",
  "position": null,
  "added_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` - Listing not found
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `409 Conflict` - Listing already exists in collection
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/collections/1/items \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": 123,
    "status": "shortlisted",
    "notes": "Great deal on this GPU"
  }'
```

---

### PATCH /collections/{collection_id}/items/{item_id}

Update collection item.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID
- `item_id` (integer): Collection item ID

**Request** (all fields optional):
```json
{
  "status": "bought",
  "notes": "Purchased on 2025-11-18",
  "position": 1
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "collection_id": 1,
  "listing_id": 123,
  "status": "bought",
  "notes": "Purchased on 2025-11-18",
  "position": 1,
  "added_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T14:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid request (validation error)
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `404 Not Found` - Item not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X PATCH http://localhost:8000/api/v1/collections/1/items/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "bought",
    "notes": "Purchased successfully"
  }'
```

---

### DELETE /collections/{collection_id}/items/{item_id}

Remove item from collection.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID
- `item_id` (integer): Collection item ID

**Response** (204 No Content):
```
(empty body)
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `404 Not Found` - Item not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/collections/1/items/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /collections/{collection_id}/export

Export collection as CSV or JSON.

**Authentication**: Required

**Path Parameters**:
- `collection_id` (integer): Collection ID

**Query Parameters**:
- `format` (string, required): Export format - `csv` or `json`

**Response** (200 OK - File Download):

For CSV:
```
Content-Type: text/csv
Content-Disposition: attachment; filename="collection_1.csv"

title,price_usd,cpu,gpu,dollar_per_cpu_mark,score,status,notes
"Gaming PC Build",1299.99,"i5-12400","RTX 3060",8.5,4.2,"shortlisted","Great value"
"Office Workstation",799.99,"Ryzen 5 5600X","No GPU",12.3,3.8,"rejected","Too expensive"
```

For JSON:
```json
{
  "collection": {
    "id": 1,
    "name": "Gaming PCs",
    "description": "Best gaming deals",
    "visibility": "private",
    "created_at": "2025-11-18T12:00:00Z",
    "updated_at": "2025-11-18T12:00:00Z",
    "item_count": 2
  },
  "items": [
    {
      "id": 1,
      "listing_id": 123,
      "status": "shortlisted",
      "notes": "Great deal",
      "position": null,
      "added_at": "2025-11-18T12:00:00Z",
      "updated_at": "2025-11-18T12:00:00Z",
      "listing": {
        "id": 123,
        "title": "Gaming PC",
        "price_usd": 1299.99,
        "cpu": "i5-12400",
        "gpu": "RTX 3060",
        "dollar_per_cpu_mark": 8.5,
        "score_composite": 4.2
      }
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Not collection owner
- `404 Not Found` - Collection not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
# Export as CSV
curl -X GET "http://localhost:8000/api/v1/collections/1/export?format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o collection_1.csv

# Export as JSON
curl -X GET "http://localhost:8000/api/v1/collections/1/export?format=json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o collection_1.json
```

---

## User-to-User Sharing Endpoints

### POST /user-shares

Create a user-to-user share.

**Authentication**: Required

**Rate Limiting**: 10 shares per hour per user

**Request**:
```json
{
  "recipient_id": 2,
  "listing_id": 123,
  "message": "Check out this amazing deal!"
}
```

**Request Schema**:
```typescript
interface CreateUserShareRequest {
  recipient_id: number;      // User ID of recipient
  listing_id: number;        // Listing ID to share
  message?: string;          // Optional, max 500 chars
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "sender_id": 1,
  "recipient_id": 2,
  "listing_id": 123,
  "share_token": "abc123def456xyz789...",
  "message": "Check out this amazing deal!",
  "shared_at": "2025-11-18T12:00:00Z",
  "expires_at": "2025-12-18T12:00:00Z",
  "viewed_at": null,
  "imported_at": null,
  "is_expired": false,
  "is_viewed": false,
  "is_imported": false
}
```

**Share Expiry**:
- User-to-user shares expire after 30 days
- Shares can be viewed and imported after expiry (data persists)

**Response Schema**:
```typescript
interface UserShareRead {
  id: number;
  sender_id: number;
  recipient_id: number;
  listing_id: number;
  share_token: string;
  message?: string;
  shared_at: string;
  expires_at: string;
  viewed_at?: string | null;
  imported_at?: string | null;
  is_expired: boolean;
  is_viewed: boolean;
  is_imported: boolean;
}
```

**Error Responses**:
- `400 Bad Request` - User or listing not found
- `401 Unauthorized` - Authentication required
- `409 Conflict` - Rate limit exceeded (10/hour)
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/user-shares \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": 2,
    "listing_id": 123,
    "message": "Check this out!"
  }'
```

---

### GET /user-shares

List received shares (inbox).

**Authentication**: Required

**Query Parameters**:
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Max results, 1-100 (default: 50)
- `unread_only` (boolean, optional): Only unviewed shares (default: false)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "sender_id": 1,
    "recipient_id": 2,
    "listing_id": 123,
    "share_token": "abc123...",
    "message": "Check out this deal!",
    "shared_at": "2025-11-18T12:00:00Z",
    "expires_at": "2025-12-18T12:00:00Z",
    "viewed_at": "2025-11-18T14:30:00Z",
    "imported_at": null,
    "is_expired": false,
    "is_viewed": true,
    "is_imported": false
  }
]
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/user-shares?limit=20&unread_only=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /user-shares/{share_token}

Preview a shared deal (view share details).

**Authentication**: Not required (but can be authenticated)

**Path Parameters**:
- `share_token` (string): Share token

**Response** (200 OK):
```json
{
  "id": 1,
  "sender_id": 1,
  "recipient_id": 2,
  "listing_id": 123,
  "share_token": "abc123...",
  "message": "Check out this deal!",
  "shared_at": "2025-11-18T12:00:00Z",
  "expires_at": "2025-12-18T12:00:00Z",
  "viewed_at": "2025-11-18T14:30:00Z",
  "imported_at": null,
  "is_expired": false,
  "is_viewed": true,
  "is_imported": false
}
```

**Error Responses**:
- `404 Not Found` - Share not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/user-shares/abc123def456xyz..." \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /user-shares/{share_token}/import

Import a shared deal to collection.

**Authentication**: Required

**Path Parameters**:
- `share_token` (string): Share token

**Request** (optional):
```json
{
  "collection_id": 1
}
```

**Request Schema**:
```typescript
interface ImportShareRequest {
  collection_id?: number; // Uses default collection if not provided
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "collection_id": 1,
  "listing_id": 123,
  "status": "undecided",
  "notes": null,
  "position": null,
  "added_at": "2025-11-18T14:45:00Z",
  "updated_at": "2025-11-18T14:45:00Z"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Share or collection not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/user-shares/abc123.../import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": 1
  }'
```

---

## Public Share Links Endpoints

### GET /deals/{listing_id}/{share_token}

View public shared deal (no authentication required).

**Authentication**: Not required

**Path Parameters**:
- `listing_id` (integer): Listing ID
- `share_token` (string): Share token

**Response** (200 OK):
```json
{
  "share_token": "abc123def456...",
  "listing_id": 123,
  "view_count": 42,
  "is_expired": false
}
```

**Notes**:
- View count is incremented automatically
- Responses cached in Redis for 24 hours (for social media previews)
- Supports OpenGraph metadata for social sharing

**Error Responses**:
- `404 Not Found` - Share not found or expired
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/deals/123/abc123def456..."

# Response includes listing data for display
```

---

## Notifications Endpoints

### GET /api/v1/notifications

List user notifications with filtering.

**Authentication**: Required

**Query Parameters**:
- `user_id` (integer, required): User ID
- `unread_only` (boolean, optional): Only unread notifications (default: false)
- `notification_type` (string, optional): Filter by type (share_received, share_imported, etc.)
- `limit` (integer, optional): Max results, 1-100 (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "notifications": [
    {
      "id": 1,
      "user_id": 1,
      "type": "share_received",
      "title": "New share from John",
      "message": "John shared a listing: Gaming PC Build",
      "read_at": null,
      "share_id": 1,
      "created_at": "2025-11-18T12:00:00Z",
      "updated_at": "2025-11-18T12:00:00Z"
    }
  ],
  "total": 10,
  "unread_count": 3,
  "limit": 50,
  "offset": 0
}
```

**Notification Types**:
- `share_received` - User shared a deal with you
- `share_imported` - Someone imported a deal you shared
- `collection_update` - Items added/removed from collection
- `system` - General system notifications

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications?user_id=1&unread_only=true&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /api/v1/notifications/{notification_id}/read

Mark notification as read.

**Authentication**: Required

**Path Parameters**:
- `notification_id` (integer): Notification ID

**Response** (200 OK):
```json
{
  "id": 1,
  "user_id": 1,
  "type": "share_received",
  "title": "New share from John",
  "message": "John shared a listing: Gaming PC Build",
  "read_at": "2025-11-18T12:30:00Z",
  "share_id": 1,
  "created_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T12:30:00Z"
}
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Notification not found
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/1/read" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### POST /api/v1/notifications/read-all

Mark all notifications as read.

**Authentication**: Required

**Request** (optional):
```json
{
  "user_id": 1
}
```

**Response** (200 OK):
```json
{
  "marked_count": 5
}
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/read-all" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /api/v1/notifications/unread-count

Get count of unread notifications.

**Authentication**: Required

**Query Parameters**:
- `user_id` (integer, required): User ID

**Response** (200 OK):
```json
{
  "unread_count": 3
}
```

**Error Responses**:
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Unexpected server error

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/notifications/unread-count?user_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "optional_field_name",
      "constraint": "optional_constraint_description"
    }
  },
  "request_id": "req_abc123xyz"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| VALIDATION_ERROR | 400 | Invalid request data |
| NOT_FOUND | 404 | Resource not found |
| PERMISSION_DENIED | 403 | Insufficient permissions |
| DUPLICATE_RESOURCE | 409 | Resource already exists |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| AUTHENTICATION_REQUIRED | 401 | Missing or invalid auth token |
| INTERNAL_SERVER_ERROR | 500 | Unexpected server error |

---

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer {token}
```

The token should be a valid JWT issued by the authentication system.

### Authentication Example

```bash
# With valid token
curl -X GET http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Returns 200 OK with collections

# Without token
curl -X GET http://localhost:8000/api/v1/collections

# Returns 401 Unauthorized
```

---

## Rate Limiting

Certain endpoints are rate limited to prevent abuse:

### Share Rate Limits

- User-to-user shares: **10 per hour per user**
- Public shares: No limit
- Receiver per hour: No limit

Rate limit headers included in responses:
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1637251200
```

When rate limited, API returns:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Max 10 shares per hour.",
    "details": {
      "reset_at": "2025-11-18T13:00:00Z"
    }
  }
}
```

---

## Performance Notes

- **Collections list**: Eager loading with item counts (no N+1 queries)
- **Collection details**: Single query with joined items
- **Public shares**: Cached in Redis for 24 hours
- **Export operations**: Streaming response for large collections
- **Notifications**: Indexed queries on user_id and type

### Pagination Best Practices

For large result sets, use pagination:

```bash
# Get first 20 results
curl -X GET "http://localhost:8000/api/v1/collections?limit=20&skip=0"

# Get next 20 results
curl -X GET "http://localhost:8000/api/v1/collections?limit=20&skip=20"

# Get next 20 results
curl -X GET "http://localhost:8000/api/v1/collections?limit=20&skip=40"
```

---

## Integration Examples

### JavaScript/TypeScript

```typescript
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';
const token = 'your_jwt_token';

// Create collection
const response = await axios.post(
  `${API_URL}/collections`,
  {
    name: 'Gaming PCs',
    visibility: 'private'
  },
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

// Share with user
await axios.post(
  `${API_URL}/user-shares`,
  {
    recipient_id: 2,
    listing_id: 123,
    message: 'Check this out!'
  },
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);
```

### Python

```python
import requests

API_URL = 'http://localhost:8000/api/v1'
token = 'your_jwt_token'

# Create collection
response = requests.post(
    f'{API_URL}/collections',
    json={
        'name': 'Gaming PCs',
        'visibility': 'private'
    },
    headers={'Authorization': f'Bearer {token}'}
)

# List collections
response = requests.get(
    f'{API_URL}/collections',
    headers={'Authorization': f'Bearer {token}'}
)
```

---

## Testing

The API includes comprehensive OpenAPI documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Use these to explore endpoints interactively and test requests.

---

## Support & Questions

For issues or questions:
1. Check the OpenAPI documentation at `/docs`
2. Review integration examples above
3. Contact the development team
