---
title: "Deal Builder API Contract Specifications"
description: "Complete API documentation for Deal Builder endpoints including request/response schemas, examples, and integration patterns. Serves as the contract between frontend and backend teams."
audience: [developers, ai-agents]
tags: [api, documentation, deal-builder, openapi, rest, specification, contract]
created: 2025-11-12
updated: 2025-11-12
category: "api-documentation"
status: draft
related:
  - /home/user/deal-brain/docs/project_plans/PRDs/features/deal-builder-v1.md
  - /home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1.md
  - /home/user/deal-brain/packages/core/dealbrain_core/valuation.py
  - /home/user/deal-brain/apps/api/dealbrain_api/services/listings.py
---

# Deal Builder API Contract Specifications

## Overview

The Deal Builder API enables users to create custom PC builds by selecting components, calculate real-time valuations using the existing Deal Brain valuation system, save builds for persistence, and share builds via URLs. This specification serves as the contract between frontend and backend development teams.

### Key Features

- **Real-time Valuation**: Calculate pricing and metrics instantly as components are selected
- **Snapshot Persistence**: Store pricing/metrics/breakdown at save time for historical accuracy
- **Shareable URLs**: Generate cryptographically secure tokens for sharing read-only build views
- **Deal Quality Indicators**: Color-coded pricing display with configurable thresholds
- **Performance Metrics**: Dollar-per-CPU-Mark (single/multi-thread) calculations
- **Soft Deletes**: Audit trail support with `deleted_at` timestamps

### Architecture

```
Frontend (Next.js)
    ↓ (React Query)
API Layer (FastAPI)
    ↓ (HTTP)
Service Layer (BuilderService)
    ↓ (Business Logic)
Repository Layer (BuilderRepository)
    ↓ (Async SQLAlchemy)
Database (PostgreSQL)
    ↓ (Queries)
Existing Valuation System (packages/core)
```

---

## Base URL & Versioning

**Base URL**: `/v1/builder`

**API Version**: 1.0

**Protocol**: HTTPS (required in production)

**Authentication**: Bearer token (JWT from existing Clerk/auth system)

### Headers

All requests must include:

```http
Content-Type: application/json
Accept: application/json
```

Authenticated endpoints require:

```http
Authorization: Bearer {token}
```

---

## Common Response Formats

### Success Response (200 OK)

All successful endpoint responses follow this structure:

```json
{
  "data": {
    // Endpoint-specific response body
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:00Z",
    "request_id": "req_abc123xyz"
  }
}
```

For list endpoints with pagination:

```json
{
  "data": [
    // Array of items
  ],
  "meta": {
    "timestamp": "2025-11-12T10:30:00Z",
    "request_id": "req_abc123xyz",
    "pagination": {
      "limit": 10,
      "offset": 0,
      "total": 42,
      "has_more": true
    }
  }
}
```

### Error Response (4xx, 5xx)

All error responses follow the Deal Brain ErrorResponse pattern:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid CPU ID provided",
    "details": {
      "field": "cpu_id",
      "constraint": "must_exist_in_catalog",
      "provided_value": 99999
    }
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:00Z",
    "request_id": "req_abc123xyz"
  }
}
```

---

## Data Models

### BuildComponentCreate (Request)

Represents a component selection in a build configuration.

```python
class BuildComponentCreate(BaseModel):
    """Request schema for adding a component to a build."""

    component_type: ComponentType
    """Type of component: CPU, GPU, RAM, PRIMARY_STORAGE, SECONDARY_STORAGE, etc."""

    cpu_id: int | None = None
    """CPU database ID. Required if component_type is CPU."""

    gpu_id: int | None = None
    """GPU database ID. Optional for GPU component type."""

    ram_gb: int | None = None
    """RAM size in GB. Optional for RAM component type."""

    primary_storage_gb: int | None = None
    """Primary storage size in GB."""

    primary_storage_type: str | None = None
    """Storage type: SSD, HDD, NVMe, etc."""

    secondary_storage_gb: int | None = None
    """Secondary storage size in GB. Optional."""

    secondary_storage_type: str | None = None
    """Secondary storage type."""

    quantity: int = Field(default=1, ge=1, le=4)
    """Quantity of component (default 1, max 4)."""

    metadata_json: dict[str, Any] | None = None
    """Arbitrary metadata for component (e.g., notes, condition flags)."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### BuildPreviewRequest (Request)

Request schema for calculating build valuation without saving.

```python
class BuildPreviewRequest(BaseModel):
    """Calculate valuation for a hypothetical build without persisting."""

    cpu_id: int | None = None
    """CPU database ID (required for metrics calculation)."""

    gpu_id: int | None = None
    """GPU database ID (optional)."""

    ram_gb: int = 0
    """Total RAM in GB (default 0)."""

    primary_storage_gb: int = 0
    """Primary storage capacity in GB."""

    primary_storage_type: str | None = None
    """Storage type: SSD, HDD, NVMe."""

    secondary_storage_gb: int | None = None
    """Secondary storage capacity in GB."""

    secondary_storage_type: str | None = None
    """Secondary storage type."""

    other_components: list[dict[str, Any]] = Field(default_factory=list)
    """Additional components: PSU, case, cooling, motherboard, etc."""

    base_price_usd: float | None = None
    """Optional base price to use instead of calculating from components."""

    condition: Condition = Condition.USED
    """Component condition: NEW, LIKE_NEW, USED, REFURBISHED."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### BuildMetricsResponse (Response)

Performance metrics calculated for a build.

```python
class BuildMetricsResponse(BaseModel):
    """Performance metrics for a build configuration."""

    dollar_per_cpu_mark_multi: float | None = None
    """Price efficiency: Adjusted price / CPU multi-thread mark."""

    dollar_per_cpu_mark_single: float | None = None
    """Single-thread price efficiency: Adjusted price / CPU single-thread mark."""

    dollar_per_gpu_mark: float | None = None
    """GPU price efficiency: Adjusted price / GPU mark (if GPU included)."""

    score_composite: float | None = None
    """Composite score 0-100 based on selected profile and thresholds."""

    cpu_mark_multi: int | None = None
    """CPU multi-thread benchmark score from PassMark."""

    cpu_mark_single: int | None = None
    """CPU single-thread benchmark score from PassMark."""

    performance_tier: str | None = None
    """Qualitative tier: BUDGET, MID_RANGE, HIGH_END, ENTHUSIAST."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### BuildValuationResponse (Response)

Complete valuation breakdown for a build.

```python
class BuildValuationResponse(BaseModel):
    """Valuation breakdown showing pricing and deal quality."""

    base_price_usd: float
    """Sum of component base prices before adjustments."""

    adjusted_price_usd: float
    """Final price after applying valuation rules and adjustments."""

    delta_usd: float
    """Difference from base to adjusted (negative = discount, positive = premium)."""

    delta_percentage: float
    """Percentage adjustment: (adjusted - base) / base * 100."""

    deal_quality: str
    """Deal quality indicator: GREAT_DEAL, GOOD_DEAL, FAIR, PREMIUM."""

    deal_quality_percentage: float
    """Savings/premium percentage matching deal_quality threshold."""

    valuation_breakdown: dict[str, Any]
    """Detailed breakdown: component costs, applied rules, adjustments."""

    metrics: BuildMetricsResponse
    """Performance metrics for the build."""

    catalog_comparison: dict[str, Any] | None = None
    """Optional: How this build compares to similar listings in database."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### SavedBuildCreate (Request)

Request schema for saving a new build configuration.

```python
class SavedBuildCreate(BaseModel):
    """Create and persist a new build configuration."""

    name: str = Field(min_length=1, max_length=200)
    """Build name (required, 1-200 characters)."""

    description: str | None = Field(default=None, max_length=1000)
    """Optional description of the build (max 1000 chars)."""

    cpu_id: int | None = None
    """Selected CPU ID (required for valuation calculation)."""

    gpu_id: int | None = None
    """Selected GPU ID (optional)."""

    ram_gb: int = 0
    """Total RAM in gigabytes."""

    primary_storage_gb: int = 0
    """Primary storage capacity."""

    primary_storage_type: str | None = None
    """Primary storage type: SSD, HDD, NVMe, etc."""

    secondary_storage_gb: int | None = None
    """Secondary storage capacity."""

    secondary_storage_type: str | None = None
    """Secondary storage type."""

    other_components: list[dict[str, Any]] = Field(default_factory=list)
    """Additional components (PSU, case, cooling, motherboard)."""

    tags: list[str] = Field(default_factory=list, max_length=10)
    """Optional tags for categorization (max 10 tags)."""

    is_public: bool = False
    """Whether build is publicly visible (default: private)."""

    visibility: str = "PRIVATE"
    """Visibility mode: PRIVATE, UNLISTED, PUBLIC."""

    notes: str | None = None
    """Additional notes about the build."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### SavedBuildUpdate (Request)

Request schema for updating an existing build (partial update).

```python
class SavedBuildUpdate(BaseModel):
    """Update an existing build configuration (PATCH)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    """Update build name."""

    description: str | None = Field(default=None, max_length=1000)
    """Update description."""

    cpu_id: int | None = None
    """Update CPU selection."""

    gpu_id: int | None = None
    """Update GPU selection."""

    ram_gb: int | None = None
    """Update RAM amount."""

    primary_storage_gb: int | None = None
    """Update primary storage size."""

    primary_storage_type: str | None = None
    """Update primary storage type."""

    secondary_storage_gb: int | None = None
    """Update secondary storage size."""

    secondary_storage_type: str | None = None
    """Update secondary storage type."""

    other_components: list[dict[str, Any]] | None = None
    """Update additional components."""

    tags: list[str] | None = None
    """Update tags."""

    is_public: bool | None = None
    """Update visibility to public."""

    visibility: str | None = None
    """Update visibility mode."""

    notes: str | None = None
    """Update notes."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### SavedBuildRead (Response)

Complete saved build response with all metadata.

```python
class SavedBuildRead(BaseModel):
    """Complete saved build record with all metadata and snapshots."""

    id: int
    """Unique build ID."""

    user_id: int
    """ID of user who created the build."""

    name: str
    """Build name."""

    description: str | None = None
    """Build description."""

    cpu_id: int | None = None
    """Selected CPU ID."""

    gpu_id: int | None = None
    """Selected GPU ID."""

    ram_gb: int
    """RAM amount in GB."""

    primary_storage_gb: int
    """Primary storage size in GB."""

    primary_storage_type: str | None = None
    """Primary storage type."""

    secondary_storage_gb: int | None = None
    """Secondary storage size in GB."""

    secondary_storage_type: str | None = None
    """Secondary storage type."""

    other_components: list[dict[str, Any]] = Field(default_factory=list)
    """Additional components stored as JSON."""

    tags: list[str] = Field(default_factory=list)
    """Associated tags."""

    # Snapshots captured at save time for historical accuracy
    pricing_snapshot: dict[str, Any]
    """Pricing data at save time: base_price, adjusted_price, delta."""

    metrics_snapshot: dict[str, Any]
    """Metrics data at save time: $/CPU Mark, scores, etc."""

    valuation_breakdown: dict[str, Any]
    """Detailed valuation breakdown JSON."""

    # Sharing and access control
    share_token: str | None = None
    """Unique token for shareable URL (null if not shared)."""

    is_public: bool
    """Whether build is publicly visible."""

    visibility: str
    """Visibility mode: PRIVATE, UNLISTED, PUBLIC."""

    # Timestamps
    created_at: datetime
    """Build creation timestamp (ISO 8601)."""

    updated_at: datetime
    """Last modification timestamp (ISO 8601)."""

    deleted_at: datetime | None = None
    """Soft delete timestamp (null if not deleted)."""

    # Related objects
    cpu: dict[str, Any] | None = None
    """CPU object details (if included in response)."""

    gpu: dict[str, Any] | None = None
    """GPU object details (if included in response)."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

### ShareResponse (Response)

Response for share token generation.

```python
class ShareResponse(BaseModel):
    """Share token and URL information."""

    share_token: str
    """Unique shareable token."""

    share_url: str
    """Full shareable URL path (/builder/shared/{token})."""

    full_url: str | None = None
    """Optional: Full absolute URL including domain."""

    is_public: bool
    """Whether build is publicly accessible."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
```

---

## Endpoints

### POST /v1/builder/preview

Calculate valuation for a hypothetical build without saving to database.

**Purpose**: Real-time valuation feedback during component selection.

**Authentication**: Not required (but encouraged for analytics)

**Request**:

```http
POST /v1/builder/preview HTTP/1.1
Host: api.dealbrain.io
Content-Type: application/json

{
  "cpu_id": 42,
  "ram_gb": 16,
  "primary_storage_gb": 512,
  "primary_storage_type": "SSD",
  "condition": "USED"
}
```

**Request Schema**: `BuildPreviewRequest`

**Response** (200 OK):

```json
{
  "data": {
    "base_price_usd": 850.00,
    "adjusted_price_usd": 765.00,
    "delta_usd": -85.00,
    "delta_percentage": -10.0,
    "deal_quality": "GOOD_DEAL",
    "deal_quality_percentage": 10.0,
    "valuation_breakdown": {
      "cpu_base_price": 350.00,
      "ram_base_price": 300.00,
      "storage_base_price": 200.00,
      "applied_rules": [
        {
          "rule_id": 5,
          "rule_name": "Used condition discount",
          "adjustment_usd": -85.00,
          "adjustment_percentage": -10.0
        }
      ],
      "total_adjustments_usd": -85.00
    },
    "metrics": {
      "dollar_per_cpu_mark_multi": 0.89,
      "dollar_per_cpu_mark_single": 1.45,
      "score_composite": 78.5,
      "cpu_mark_multi": 859,
      "cpu_mark_single": 528,
      "performance_tier": "HIGH_END"
    }
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:45Z",
    "request_id": "req_abc123xyz"
  }
}
```

**Response Schema**: `BuildValuationResponse`

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Calculation successful | Valid valuation returned |
| 400 | Invalid input | Missing required CPU, invalid condition enum |
| 422 | Business logic error | CPU ID doesn't exist in catalog |
| 429 | Rate limit exceeded | Too many preview requests |
| 500 | Server error | Unexpected exception during calculation |

**Validation Rules**:

- If `cpu_id` provided, must exist in CPU catalog
- If `gpu_id` provided, must exist in GPU catalog
- `ram_gb` must be 0-128
- Storage sizes must be positive
- `condition` must be valid enum value

**Performance**:

- **Target**: <300ms
- **p95**: <400ms
- **p99**: <600ms
- **Caching**: None (always fresh calculation)

**Integration Notes**:

- Call `BuilderService.calculate_build_valuation()` in service layer
- Internally calls `apply_valuation_rules()` from `packages/core/valuation.py`
- Internally calls `calculate_metrics()` from `packages/core/scoring.py`
- No database persistence (read-only operation)

---

### POST /v1/builder/builds

Save a new build configuration to the database.

**Purpose**: Persist a build for later retrieval and sharing.

**Authentication**: Required (JWT bearer token)

**Request**:

```http
POST /v1/builder/builds HTTP/1.1
Host: api.dealbrain.io
Content-Type: application/json
Authorization: Bearer eyJhbGc...

{
  "name": "Budget Gaming PC",
  "description": "Perfect for 1080p gaming at high settings",
  "cpu_id": 42,
  "ram_gb": 16,
  "primary_storage_gb": 512,
  "primary_storage_type": "SSD",
  "tags": ["gaming", "budget"],
  "is_public": false,
  "visibility": "PRIVATE"
}
```

**Request Schema**: `SavedBuildCreate`

**Response** (201 Created):

```json
{
  "data": {
    "id": 128,
    "user_id": 5,
    "name": "Budget Gaming PC",
    "description": "Perfect for 1080p gaming at high settings",
    "cpu_id": 42,
    "gpu_id": null,
    "ram_gb": 16,
    "primary_storage_gb": 512,
    "primary_storage_type": "SSD",
    "secondary_storage_gb": null,
    "secondary_storage_type": null,
    "tags": ["gaming", "budget"],
    "pricing_snapshot": {
      "base_price_usd": 850.00,
      "adjusted_price_usd": 765.00,
      "delta_usd": -85.00,
      "delta_percentage": -10.0,
      "deal_quality": "GOOD_DEAL"
    },
    "metrics_snapshot": {
      "dollar_per_cpu_mark_multi": 0.89,
      "dollar_per_cpu_mark_single": 1.45,
      "score_composite": 78.5
    },
    "valuation_breakdown": {
      "cpu_base_price": 350.00,
      "applied_rules": [...]
    },
    "share_token": null,
    "is_public": false,
    "visibility": "PRIVATE",
    "created_at": "2025-11-12T10:35:22Z",
    "updated_at": "2025-11-12T10:35:22Z",
    "deleted_at": null
  },
  "meta": {
    "timestamp": "2025-11-12T10:35:22Z",
    "request_id": "req_def456uvw"
  }
}
```

**Response Schema**: `SavedBuildRead`

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 201 | Build created successfully | Build ID 128 created |
| 400 | Invalid input | Missing required name field |
| 401 | Unauthorized | No valid JWT token provided |
| 409 | Conflict | Build name already exists for this user |
| 422 | Business logic error | CPU ID doesn't exist, valuation calculation failed |
| 500 | Server error | Database error during save |

**Validation Rules**:

- `name` required, 1-200 characters, unique per user
- `description` optional, max 1000 characters
- If `cpu_id` provided, must exist in catalog (required for metrics)
- All component IDs must exist if provided
- `visibility` must be one of: PRIVATE, UNLISTED, PUBLIC
- Tags max 10, each tag max 50 characters

**Performance**:

- **Target**: <500ms
- **p95**: <800ms
- **p99**: <1200ms
- **Includes**: Valuation calculation + snapshot + database save

**Side Effects**:

- Triggers valuation calculation to create pricing/metrics snapshots
- Generates unique `share_token` (UUID4) even if not shared
- Records `created_at` timestamp
- Associated with authenticated `user_id`

**Integration Notes**:

- Call `BuilderService.save_build()` in service layer
- Service internally calls `calculate_build_valuation()` for snapshots
- Repository saves with `user_id` from authenticated context
- Use eager loading for CPU/GPU relationships

---

### GET /v1/builder/builds

List all saved builds for the authenticated user.

**Purpose**: Display user's build gallery with pagination.

**Authentication**: Required (JWT bearer token)

**Request**:

```http
GET /v1/builder/builds?limit=10&offset=0&sort_by=created_at&order=desc HTTP/1.1
Host: api.dealbrain.io
Authorization: Bearer eyJhbGc...
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Number of results per page (1-100) |
| `offset` | integer | 0 | Pagination offset (0-based) |
| `sort_by` | string | created_at | Field to sort by: created_at, updated_at, name |
| `order` | string | desc | Sort direction: asc, desc |
| `visibility` | string | - | Filter by visibility: PRIVATE, UNLISTED, PUBLIC |

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": 128,
      "user_id": 5,
      "name": "Budget Gaming PC",
      "description": "Perfect for 1080p gaming",
      "cpu_id": 42,
      "ram_gb": 16,
      "primary_storage_gb": 512,
      "pricing_snapshot": {
        "adjusted_price_usd": 765.00,
        "deal_quality": "GOOD_DEAL"
      },
      "metrics_snapshot": {
        "dollar_per_cpu_mark_multi": 0.89,
        "score_composite": 78.5
      },
      "share_token": null,
      "is_public": false,
      "visibility": "PRIVATE",
      "created_at": "2025-11-12T10:35:22Z",
      "updated_at": "2025-11-12T10:35:22Z"
    },
    {
      "id": 127,
      "user_id": 5,
      "name": "High-End Workstation",
      "description": "For video editing and 3D rendering",
      "cpu_id": 45,
      "ram_gb": 32,
      "primary_storage_gb": 2000,
      "pricing_snapshot": {
        "adjusted_price_usd": 2150.00,
        "deal_quality": "FAIR"
      },
      "metrics_snapshot": {
        "dollar_per_cpu_mark_multi": 0.65,
        "score_composite": 92.0
      },
      "share_token": "abc123def456",
      "is_public": true,
      "visibility": "PUBLIC",
      "created_at": "2025-11-11T14:20:10Z",
      "updated_at": "2025-11-11T14:20:10Z"
    }
  ],
  "meta": {
    "timestamp": "2025-11-12T10:40:00Z",
    "request_id": "req_ghi789jkl",
    "pagination": {
      "limit": 10,
      "offset": 0,
      "total": 5,
      "has_more": false
    }
  }
}
```

**Response Schema**: `list[SavedBuildRead]`

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | List retrieved successfully | Returns 5 builds, has_more=false |
| 401 | Unauthorized | No valid JWT token |
| 422 | Invalid query params | offset negative, limit > 100 |
| 500 | Server error | Database error |

**Query Validation**:

- `limit`: 1-100 (default 10)
- `offset`: ≥0 (default 0)
- `sort_by`: must be valid column name
- `order`: must be asc or desc

**Performance**:

- **Target**: <500ms for 10 results
- **Typical**: <100ms for 100 builds from same user
- **p99**: <800ms for 1000+ builds
- **Query Optimization**: Use index on `(user_id, deleted_at, created_at)`

**Integration Notes**:

- Filter by `user_id` from authenticated context
- Exclude soft-deleted builds (`deleted_at IS NULL`)
- Use eager loading for CPU/GPU relationships to avoid N+1
- Return snapshots only (not full valuation_breakdown)
- Sort by `created_at desc` by default (newest first)

---

### GET /v1/builder/builds/{id}

Retrieve a specific saved build by ID.

**Purpose**: Display full build details for editing or viewing.

**Authentication**: Required (JWT bearer token)

**Request**:

```http
GET /v1/builder/builds/128 HTTP/1.1
Host: api.dealbrain.io
Authorization: Bearer eyJhbGc...
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Build ID (required) |

**Response** (200 OK):

```json
{
  "data": {
    "id": 128,
    "user_id": 5,
    "name": "Budget Gaming PC",
    "description": "Perfect for 1080p gaming at high settings",
    "cpu_id": 42,
    "gpu_id": null,
    "ram_gb": 16,
    "primary_storage_gb": 512,
    "primary_storage_type": "SSD",
    "secondary_storage_gb": null,
    "secondary_storage_type": null,
    "tags": ["gaming", "budget"],
    "pricing_snapshot": {
      "base_price_usd": 850.00,
      "adjusted_price_usd": 765.00,
      "delta_usd": -85.00,
      "delta_percentage": -10.0,
      "deal_quality": "GOOD_DEAL"
    },
    "metrics_snapshot": {
      "dollar_per_cpu_mark_multi": 0.89,
      "dollar_per_cpu_mark_single": 1.45,
      "score_composite": 78.5,
      "cpu_mark_multi": 859
    },
    "valuation_breakdown": {
      "cpu_base_price": 350.00,
      "ram_base_price": 300.00,
      "storage_base_price": 200.00,
      "applied_rules": [
        {
          "rule_id": 5,
          "rule_name": "Used condition discount",
          "adjustment_usd": -85.00
        }
      ]
    },
    "cpu": {
      "id": 42,
      "name": "AMD Ryzen 5 5600X",
      "manufacturer": "AMD",
      "cpu_mark_multi": 859,
      "cpu_mark_single": 528
    },
    "share_token": null,
    "is_public": false,
    "visibility": "PRIVATE",
    "created_at": "2025-11-12T10:35:22Z",
    "updated_at": "2025-11-12T10:35:22Z",
    "deleted_at": null
  },
  "meta": {
    "timestamp": "2025-11-12T10:45:00Z",
    "request_id": "req_mno012pqr"
  }
}
```

**Response Schema**: `SavedBuildRead`

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Build retrieved successfully | Full build details returned |
| 401 | Unauthorized | No valid JWT token |
| 403 | Forbidden | User doesn't own this build |
| 404 | Not found | Build ID doesn't exist |
| 500 | Server error | Database error |

**Access Control**:

- User must be the owner (verified via `user_id` in token)
- Soft-deleted builds return 404
- Non-owners of private builds receive 404 (not 403)

**Performance**:

- **Target**: <200ms
- **Query**: Single indexed lookup + eager load CPU/GPU

**Integration Notes**:

- Verify ownership before returning (compare `user_id` from token with build's `user_id`)
- Return complete valuation breakdown (not just snapshot)
- Include related CPU/GPU objects for frontend display

---

### PATCH /v1/builder/builds/{id}

Update an existing build configuration.

**Purpose**: Modify build components, metadata, or settings.

**Authentication**: Required (JWT bearer token)

**Request**:

```http
PATCH /v1/builder/builds/128 HTTP/1.1
Host: api.dealbrain.io
Content-Type: application/json
Authorization: Bearer eyJhbGc...

{
  "name": "Budget Gaming PC - Updated",
  "gpu_id": 15,
  "ram_gb": 32,
  "tags": ["gaming", "budget", "rtx-4060"]
}
```

**Request Schema**: `SavedBuildUpdate` (all fields optional)

**Response** (200 OK):

```json
{
  "data": {
    "id": 128,
    "user_id": 5,
    "name": "Budget Gaming PC - Updated",
    "description": "Perfect for 1080p gaming at high settings",
    "cpu_id": 42,
    "gpu_id": 15,
    "ram_gb": 32,
    "primary_storage_gb": 512,
    "primary_storage_type": "SSD",
    "tags": ["gaming", "budget", "rtx-4060"],
    "pricing_snapshot": {
      "base_price_usd": 1100.00,
      "adjusted_price_usd": 990.00,
      "delta_usd": -110.00,
      "delta_percentage": -10.0,
      "deal_quality": "GOOD_DEAL"
    },
    "metrics_snapshot": {
      "dollar_per_cpu_mark_multi": 1.15,
      "dollar_per_cpu_mark_single": 1.87,
      "score_composite": 82.3
    },
    "valuation_breakdown": {...},
    "share_token": null,
    "is_public": false,
    "visibility": "PRIVATE",
    "created_at": "2025-11-12T10:35:22Z",
    "updated_at": "2025-11-12T11:00:45Z",
    "deleted_at": null
  },
  "meta": {
    "timestamp": "2025-11-12T11:00:45Z",
    "request_id": "req_stu345vwx"
  }
}
```

**Response Schema**: `SavedBuildRead`

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Update successful | Build updated and returned |
| 400 | Invalid input | Malformed JSON, invalid enum |
| 401 | Unauthorized | No valid JWT token |
| 403 | Forbidden | User doesn't own this build |
| 404 | Not found | Build ID doesn't exist |
| 409 | Conflict | Name already exists for this user |
| 422 | Business logic error | CPU ID doesn't exist, valuation failed |
| 500 | Server error | Database error |

**Validation Rules**:

- Only provided fields are updated (PATCH semantics)
- `name` if provided: 1-200 chars, unique per user
- Component IDs if provided: must exist in catalog
- `visibility` if provided: must be valid enum
- Soft-deleted builds return 404

**Side Effects**:

- Recalculates valuation if components changed
- Updates pricing/metrics snapshots
- Updates `updated_at` timestamp
- Does NOT regenerate `share_token`

**Performance**:

- **Target**: <500ms (includes recalculation if components changed)
- **p95**: <800ms
- **Depends on**: Number of changed fields

**Integration Notes**:

- Verify ownership before updating
- If components changed, recalculate snapshots via `BuilderService.calculate_build_valuation()`
- Preserve `created_at` and `share_token`
- Only touch database fields that were provided

---

### DELETE /v1/builder/builds/{id}

Soft delete a saved build (mark as deleted but preserve data).

**Purpose**: Remove build from user's gallery while preserving audit trail.

**Authentication**: Required (JWT bearer token)

**Request**:

```http
DELETE /v1/builder/builds/128 HTTP/1.1
Host: api.dealbrain.io
Authorization: Bearer eyJhbGc...
```

**Response** (204 No Content):

```http
HTTP/1.1 204 No Content
```

No response body for successful deletion.

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 204 | Deletion successful | Build marked deleted |
| 401 | Unauthorized | No valid JWT token |
| 403 | Forbidden | User doesn't own this build |
| 404 | Not found | Build doesn't exist |
| 500 | Server error | Database error |

**Soft Delete Behavior**:

- Sets `deleted_at` to current timestamp
- Does NOT remove from database
- Subsequent GETs return 404
- Subsequent GETs in list return 404
- Data can be recovered by clearing `deleted_at`

**Performance**:

- **Target**: <100ms
- **Indexed**: Uses `(user_id, deleted_at)` index

**Integration Notes**:

- Verify ownership before deleting
- Use soft delete pattern: `update ... set deleted_at = now() where id = ? and user_id = ?`
- Include `deleted_at IS NULL` in all SELECT queries

---

### GET /v1/builder/builds/{id}/share

Generate or retrieve shareable URL for a build.

**Purpose**: Create public share link and enable sharing.

**Authentication**: Required (JWT bearer token)

**Request**:

```http
GET /v1/builder/builds/128/share HTTP/1.1
Host: api.dealbrain.io
Authorization: Bearer eyJhbGc...
```

**Response** (200 OK):

```json
{
  "data": {
    "share_token": "f7a3c8b2d1e5f9a6c4b8e2f7d1a5c9b3",
    "share_url": "/builder/shared/f7a3c8b2d1e5f9a6c4b8e2f7d1a5c9b3",
    "full_url": "https://dealbrain.io/builder/shared/f7a3c8b2d1e5f9a6c4b8e2f7d1a5c9b3",
    "is_public": true
  },
  "meta": {
    "timestamp": "2025-11-12T11:05:10Z",
    "request_id": "req_yz456abc"
  }
}
```

**Response Schema**: `ShareResponse`

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Share enabled successfully | Token returned |
| 401 | Unauthorized | No valid JWT token |
| 403 | Forbidden | User doesn't own this build |
| 404 | Not found | Build doesn't exist |
| 500 | Server error | Database error |

**Behavior**:

- If build already has `share_token`, returns existing token
- If no token exists, generates new UUID4 token
- Sets `is_public=true` and `visibility=PUBLIC`
- Token is cryptographically unique (uuid4)
- Returns both path `/builder/shared/{token}` and full URL

**Performance**:

- **Target**: <100ms (for existing token)
- **First call**: <200ms (includes token generation and DB update)

**Integration Notes**:

- Token generation: `uuid.uuid4().hex` produces 32-char hex string
- Unique constraint on `share_token` in database
- Updates `is_public` and `visibility` fields
- Does not update `updated_at` (optional)

---

### GET /v1/builder/public/{share_token}

Retrieve a publicly shared build by share token (no authentication required).

**Purpose**: Display shared build view to anyone with the link.

**Authentication**: Not required (public endpoint)

**Request**:

```http
GET /v1/builder/public/f7a3c8b2d1e5f9a6c4b8e2f7d1a5c9b3 HTTP/1.1
Host: api.dealbrain.io
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `share_token` | string | 32-character share token |

**Response** (200 OK):

```json
{
  "data": {
    "id": 128,
    "name": "Budget Gaming PC",
    "description": "Perfect for 1080p gaming at high settings",
    "cpu_id": 42,
    "gpu_id": null,
    "ram_gb": 16,
    "primary_storage_gb": 512,
    "primary_storage_type": "SSD",
    "tags": ["gaming", "budget"],
    "pricing_snapshot": {
      "base_price_usd": 850.00,
      "adjusted_price_usd": 765.00,
      "delta_usd": -85.00,
      "delta_percentage": -10.0,
      "deal_quality": "GOOD_DEAL"
    },
    "metrics_snapshot": {
      "dollar_per_cpu_mark_multi": 0.89,
      "score_composite": 78.5
    },
    "valuation_breakdown": {...},
    "cpu": {
      "id": 42,
      "name": "AMD Ryzen 5 5600X",
      "manufacturer": "AMD"
    },
    "created_at": "2025-11-12T10:35:22Z"
  },
  "meta": {
    "timestamp": "2025-11-12T11:10:00Z",
    "request_id": "req_def789ghi"
  }
}
```

**Response Schema**: `SavedBuildRead` (without `user_id` or `updated_at`)

**Status Codes**:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Shared build retrieved | Public build returned |
| 404 | Not found | Token doesn't exist or build is private |
| 500 | Server error | Database error |

**Access Control**:

- Only returns builds with `is_public=true`
- Does NOT return `user_id`, `updated_at`, `deleted_at`
- Private/unlisted builds return 404 (same response)
- No way to discover tokens (cryptographically random)

**Performance**:

- **Target**: <100ms
- **Query**: Indexed lookup on `share_token`
- **Caching**: Can cache aggressively (build immutable from share link perspective)

**Integration Notes**:

- Query: `select * from saved_builds where share_token = ? and is_public = true and deleted_at is null`
- Use index on `share_token`
- Exclude sensitive fields from response
- Does not require authentication (public endpoint)

---

## Error Responses

### Error Response Format

All errors follow the Deal Brain ErrorResponse pattern:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_name_if_applicable",
      "constraint": "constraint_name_if_applicable",
      "provided_value": "value_that_failed_validation"
    }
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:00Z",
    "request_id": "req_abc123xyz"
  }
}
```

### Common Error Codes

| Code | HTTP | Meaning | Example |
|------|------|---------|---------|
| `VALIDATION_ERROR` | 400 | Input validation failed | Missing required field, invalid type |
| `NOT_FOUND` | 404 | Resource doesn't exist | Build ID doesn't exist |
| `UNAUTHORIZED` | 401 | Missing or invalid auth | No token provided, expired token |
| `FORBIDDEN` | 403 | Access denied | User doesn't own build (though returns 404) |
| `CONFLICT` | 409 | Resource conflict | Duplicate name for user |
| `BUSINESS_LOGIC_ERROR` | 422 | Business rule violated | CPU doesn't exist in catalog |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Exceeded preview rate limit |
| `INTERNAL_ERROR` | 500 | Server error | Unexpected exception |

### Example Error Responses

**Invalid CPU ID (BUSINESS_LOGIC_ERROR)**:

```json
{
  "error": {
    "code": "BUSINESS_LOGIC_ERROR",
    "message": "CPU with ID 99999 not found in catalog",
    "details": {
      "field": "cpu_id",
      "constraint": "must_exist_in_catalog",
      "provided_value": 99999
    }
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:45Z",
    "request_id": "req_abc123xyz"
  }
}
```

**Duplicate Build Name (CONFLICT)**:

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "A build with name 'Budget Gaming PC' already exists for this user",
    "details": {
      "field": "name",
      "constraint": "unique_per_user",
      "provided_value": "Budget Gaming PC"
    }
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:45Z",
    "request_id": "req_abc123xyz"
  }
}
```

**Missing Required Field (VALIDATION_ERROR)**:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'name' is required and must be 1-200 characters",
    "details": {
      "field": "name",
      "constraint": "required|min_length|max_length",
      "provided_value": ""
    }
  },
  "meta": {
    "timestamp": "2025-11-12T10:30:45Z",
    "request_id": "req_abc123xyz"
  }
}
```

---

## Performance & Limits

### Rate Limiting

The `/v1/builder/preview` endpoint implements rate limiting to prevent abuse:

| Limit | Value | Applied To |
|-------|-------|-----------|
| Anonymous preview requests | 10 per minute | Per IP address |
| Authenticated preview requests | 100 per minute | Per user |
| Save/update operations | 50 per hour | Per user |

Rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699778445
```

When limit exceeded (429):

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 45 seconds."
  },
  "meta": {
    "retry_after": 45
  }
}
```

### Response Time Targets

| Operation | p50 | p95 | p99 | Caching |
|-----------|-----|-----|-----|---------|
| POST /preview | 150ms | 400ms | 600ms | None |
| POST /builds | 250ms | 800ms | 1200ms | None |
| GET /builds | 80ms | 500ms | 800ms | None |
| GET /builds/{id} | 60ms | 200ms | 300ms | 5 min |
| PATCH /builds/{id} | 200ms | 800ms | 1200ms | None |
| DELETE /builds/{id} | 50ms | 100ms | 150ms | None |
| GET /share | 50ms | 100ms | 150ms | 1 hour |
| GET /public/{token} | 60ms | 200ms | 300ms | 15 min |

### Database Query Optimization

**Required Indexes**:

```sql
-- Critical indexes for performance
CREATE INDEX idx_saved_builds_user_deleted
  ON saved_builds(user_id, deleted_at, created_at DESC);

CREATE INDEX idx_saved_builds_share_token
  ON saved_builds(share_token);

CREATE INDEX idx_saved_builds_visibility
  ON saved_builds(visibility, deleted_at);
```

**Query Optimization Patterns**:

- Use eager loading (`joinedload`) for CPU/GPU relationships
- Always filter by `deleted_at IS NULL` for active records
- Use `limit + offset` pagination (max 100 per page)
- Avoid N+1 queries (fetch relationships in single query)
- Cache catalog data (CPUs, GPUs) - changes infrequently

---

## Integration with Existing Systems

### Valuation System Integration

The builder API reuses the existing valuation system from `packages/core`:

```python
# From BuilderService
from dealbrain_core.valuation import apply_valuation_rules
from dealbrain_core.scoring import calculate_metrics
from dealbrain_api.services.listings import apply_listing_metrics

# Calculate valuation
adjusted_price = apply_valuation_rules(
    base_price=sum_of_component_prices,
    rules=settings.valuation_rules,
    component_conditions=conditions_dict
)

# Calculate metrics
metrics = calculate_metrics(
    cpu_mark_multi=cpu.cpu_mark_multi,
    cpu_mark_single=cpu.cpu_mark_single,
    adjusted_price=adjusted_price,
    profile=settings.profile
)
```

### ApplicationSettings Integration

Deal quality thresholds come from `ApplicationSettings`:

```python
# From BuilderService
settings = await session.get(ApplicationSettings, 1)  # Singleton

if delta_percentage >= settings.great_deal_threshold:
    deal_quality = "GREAT_DEAL"
elif delta_percentage >= settings.good_deal_threshold:
    deal_quality = "GOOD_DEAL"
elif delta_percentage >= -settings.premium_warning_threshold:
    deal_quality = "FAIR"
else:
    deal_quality = "PREMIUM"
```

### Component Catalog Integration

All component IDs must exist in the existing catalogs:

- **CPUs**: `Cpu` table with benchmark data
- **GPUs**: `Gpu` table with benchmark data
- **RAM**: Can reference specifications or use simple GB values
- **Storage**: Can use storage type and GB values

### Frontend API Client Integration

The Next.js frontend uses React Query:

```typescript
// From frontend-developer
import { useQuery, useMutation } from '@tanstack/react-query';

// Preview calculation (debounced 300ms)
const { data: valuation } = useQuery({
  queryKey: ['builder', 'preview', components],
  queryFn: () => api.calculateBuildValuation(components),
  enabled: !!components.cpu_id,
  staleTime: Infinity,  // Always fresh
});

// Save build
const saveBuild = useMutation({
  mutationFn: (build) => api.saveNewBuild(build),
  onSuccess: (data) => {
    // Reload builds list
    queryClient.invalidateQueries(['builder', 'builds']);
  },
});
```

---

## Changelog & Versioning

### API Version 1.0 (Current)

**Release Date**: 2025-11-12

**Endpoints**:
- POST /v1/builder/preview
- POST /v1/builder/builds
- GET /v1/builder/builds
- GET /v1/builder/builds/{id}
- PATCH /v1/builder/builds/{id}
- DELETE /v1/builder/builds/{id}
- GET /v1/builder/builds/{id}/share
- GET /v1/builder/public/{share_token}

**Future Versions**:
- v1.1: Component compatibility validation
- v1.2: Price history tracking
- v2.0: Build templates and presets

---

## Testing Strategy

### Test Coverage Requirements

| Component | Coverage Target | Test Type |
|-----------|-----------------|-----------|
| BuilderService | >85% | Unit + Integration |
| API Endpoints | >90% | Integration + E2E |
| Database Queries | >80% | Integration |
| Error Handling | 100% | Unit + Integration |

### Key Test Scenarios

**Happy Path**:
1. Select CPU → calculate preview → save build → share → view shared
2. Load saved build → modify → update → verify snapshots updated
3. List user's builds → paginate → delete → verify soft delete

**Error Paths**:
1. Invalid CPU ID → return 422 with error details
2. Missing authentication → return 401
3. Duplicate build name → return 409
4. Ownership validation → non-owner gets 404
5. Rate limiting → 429 with retry-after

**Performance**:
1. Preview calculation <300ms (warmup + 10 iterations)
2. Save operation <500ms including snapshot
3. List 100 builds <500ms with pagination
4. Access control validation inline (no N+1)

---

## Document Information

**Document Version**: 1.0
**Status**: Draft - Ready for Implementation
**Last Updated**: 2025-11-12
**Audience**: Backend engineers, frontend engineers, API consumers

### Next Steps

1. Review and approve API contract
2. Implement backend (Phase 1-4)
3. Implement frontend (Phase 5-7)
4. Test integration (Phase 8)
5. Deploy to production

### References

- PRD: `/home/user/deal-brain/docs/project_plans/PRDs/features/deal-builder-v1.md`
- Implementation Plan: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1.md`
- Valuation System: `/home/user/deal-brain/packages/core/dealbrain_core/valuation.py`
- Scoring System: `/home/user/deal-brain/packages/core/dealbrain_core/scoring.py`
- Existing API Patterns: `/home/user/deal-brain/apps/api/dealbrain_api/api/`
