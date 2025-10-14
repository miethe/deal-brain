# API Documentation

Complete REST API reference for Deal Brain v1 API. All endpoints follow RESTful conventions and return JSON responses.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Listings API](#listings-api)
3. [Catalog API](#catalog-api)
4. [Rules API](#rules-api)
5. [Baseline API](#baseline-api)
6. [Dashboard API](#dashboard-api)
7. [Custom Fields API](#custom-fields-api)
8. [Field Data API](#field-data-api)
9. [Settings API](#settings-api)
10. [Import API](#import-api)
11. [Health API](#health-api)
12. [Common Patterns](#common-patterns)

---

## API Overview

### Base URL

**Local Development:**
```
http://localhost:8000
```

**Docker Compose:**
```
http://<host-ip>:8020
```

Environment variable: `NEXT_PUBLIC_API_URL`

### Versioning

API endpoints are versioned using URL path prefixes:
- **v1**: `/v1/` or `/api/v1/`

### Authentication

Currently no authentication is implemented. All endpoints are publicly accessible.

**Future**: RBAC integration points are marked in baseline endpoints requiring `baseline:admin` permission.

### Response Format

All endpoints return JSON with consistent structure:

**Success Response (200-299):**
```json
{
  "id": 1,
  "field": "value",
  ...
}
```

**Error Response (400-599):**
```json
{
  "detail": "Error message"
}
```

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common HTTP Status Codes

- `200 OK` - Successful GET/PUT/PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate, dependencies)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Pagination

List endpoints support offset-based pagination:

**Query Parameters:**
- `limit` - Number of items to return (default: 50, max: 200)
- `offset` - Number of items to skip (default: 0)

**Example:**
```
GET /v1/listings?limit=20&offset=40
```

---

## Listings API

Base path: `/v1/listings`

### List Listings

Get a paginated list of all listings.

**Endpoint:** `GET /v1/listings`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Max items to return (max: 200) |
| offset | integer | 0 | Number of items to skip |

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Intel NUC 11 Pro - i7-1165G7",
    "listing_url": "https://example.com/listing",
    "price_usd": 599.99,
    "adjusted_price_usd": 549.99,
    "condition": "used_excellent",
    "status": "active",
    "cpu_id": 42,
    "gpu_id": null,
    "ram_gb": 16,
    "primary_storage_gb": 512,
    "primary_storage_type": "NVMe",
    "score_composite": 8.5,
    "dollar_per_cpu_mark": 0.42,
    "created_at": "2025-10-12T10:30:00Z",
    "updated_at": "2025-10-14T08:15:00Z"
  }
]
```

### Get Listing

Get a single listing by ID.

**Endpoint:** `GET /v1/listings/{listing_id}`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| listing_id | integer | Listing ID |

**Response:** `200 OK` - Returns single listing object (same structure as list)

**Error Responses:**
- `404 Not Found` - Listing does not exist

### Create Listing

Create a new listing.

**Endpoint:** `POST /v1/listings`

**Request Body:**
```json
{
  "title": "Intel NUC 12 Pro - i7-1260P",
  "listing_url": "https://example.com/listing",
  "price_usd": 749.99,
  "condition": "new",
  "status": "active",
  "cpu_id": 45,
  "ram_gb": 32,
  "primary_storage_gb": 1024,
  "primary_storage_type": "NVMe",
  "notes": "Excellent condition, includes warranty",
  "components": [
    {
      "component_type": "ram",
      "quantity": 32.0,
      "unit_value_usd": 2.5
    }
  ]
}
```

**Required Fields:**
- `title` (string, min 3 chars)
- `price_usd` (number, >= 0)

**Response:** `201 Created`
```json
{
  "id": 123,
  "title": "Intel NUC 12 Pro - i7-1260P",
  ...
}
```

### Update Listing (Full)

Replace all listing fields.

**Endpoint:** `PUT /v1/listings/{listing_id}`

**Request Body:** Same as POST (all fields)

**Response:** `200 OK` - Returns updated listing

### Update Listing (Partial)

Update specific listing fields.

**Endpoint:** `PATCH /v1/listings/{listing_id}`

**Request Body:**
```json
{
  "fields": {
    "price_usd": 699.99,
    "notes": "Price reduced"
  },
  "attributes": {
    "discount_applied": true
  }
}
```

**Fields:**
- `fields` - Core listing fields to update
- `attributes` - Custom field values to update

**Response:** `200 OK` - Returns updated listing

### Get Listing Schema

Get field definitions for listings (core + custom fields).

**Endpoint:** `GET /v1/listings/schema`

**Response:** `200 OK`
```json
{
  "core_fields": [
    {
      "key": "title",
      "label": "Title",
      "data_type": "string",
      "required": true,
      "description": "Canonical listing label",
      "validation": {
        "min_length": 3
      }
    },
    {
      "key": "price_usd",
      "label": "Price (USD)",
      "data_type": "number",
      "required": true,
      "validation": {
        "min": 0
      }
    }
  ],
  "custom_fields": [
    {
      "id": 5,
      "entity": "listing",
      "key": "warranty_months",
      "label": "Warranty (Months)",
      "data_type": "number",
      "required": false
    }
  ]
}
```

### Get Valuation Breakdown

Get detailed valuation breakdown showing how adjusted price was calculated.

**Endpoint:** `GET /v1/listings/{listing_id}/valuation-breakdown`

**Response:** `200 OK`
```json
{
  "listing_id": 123,
  "listing_title": "Intel NUC 11 Pro - i7-1165G7",
  "base_price_usd": 599.99,
  "adjusted_price_usd": 549.99,
  "total_adjustment": -50.00,
  "matched_rules_count": 3,
  "ruleset_id": 1,
  "ruleset_name": "Baseline v1.2.0",
  "adjustments": [
    {
      "rule_id": 42,
      "rule_name": "RAM Capacity Deduction",
      "adjustment_amount": -30.00,
      "actions": [
        {
          "action_type": "adjust_price",
          "metric": "adjusted_price_usd",
          "value": -30.00,
          "details": "16GB RAM: $2.50/GB * 12GB under baseline"
        }
      ]
    },
    {
      "rule_id": 48,
      "rule_name": "Used Condition Multiplier",
      "adjustment_amount": -20.00,
      "actions": [
        {
          "action_type": "apply_multiplier",
          "metric": "adjusted_price_usd",
          "value": 0.95,
          "details": "Excellent condition: 5% discount"
        }
      ]
    }
  ],
  "legacy_lines": []
}
```

### Update Valuation Overrides

Configure valuation ruleset assignment and exclusions for a listing.

**Endpoint:** `PATCH /v1/listings/{listing_id}/valuation-overrides`

**Request Body:**
```json
{
  "mode": "static",
  "ruleset_id": 5,
  "disabled_rulesets": [2, 3]
}
```

**Fields:**
- `mode` - "auto" (use active ruleset) or "static" (pin to specific ruleset)
- `ruleset_id` - Required if mode is "static"
- `disabled_rulesets` - List of ruleset IDs to exclude from evaluation

**Response:** `200 OK`
```json
{
  "mode": "static",
  "ruleset_id": 5,
  "disabled_rulesets": [2, 3]
}
```

### Bulk Update Listings

Update multiple listings at once.

**Endpoint:** `POST /v1/listings/bulk-update`

**Request Body:**
```json
{
  "listing_ids": [1, 2, 3],
  "fields": {
    "status": "archived"
  },
  "attributes": {
    "bulk_action_date": "2025-10-14"
  }
}
```

**Response:** `200 OK`
```json
{
  "updated": [
    { "id": 1, "title": "...", ... },
    { "id": 2, "title": "...", ... },
    { "id": 3, "title": "...", ... }
  ],
  "updated_count": 3
}
```

### Recalculate Listing Metrics

Recalculate all performance metrics for a single listing.

**Endpoint:** `POST /v1/listings/{listing_id}/recalculate-metrics`

**Response:** `200 OK` - Returns updated listing

### Bulk Recalculate Metrics

Recalculate metrics for multiple listings.

**Endpoint:** `POST /v1/listings/bulk-recalculate-metrics`

**Request Body:**
```json
{
  "listing_ids": [1, 2, 3]
}
```

Leave `listing_ids` null or empty to update all listings.

**Response:** `200 OK`
```json
{
  "updated_count": 3,
  "message": "Updated 3 listing(s)"
}
```

### Get Listing Ports

Get connectivity ports for a listing.

**Endpoint:** `GET /v1/listings/{listing_id}/ports`

**Response:** `200 OK`
```json
{
  "ports": [
    {
      "port_type": "USB-A",
      "version": "3.2",
      "count": 4
    },
    {
      "port_type": "USB-C",
      "version": "4.0",
      "count": 2,
      "features": ["Thunderbolt", "Power Delivery"]
    },
    {
      "port_type": "HDMI",
      "version": "2.1",
      "count": 1
    }
  ]
}
```

### Update Listing Ports

Create or update ports for a listing.

**Endpoint:** `POST /v1/listings/{listing_id}/ports`

**Request Body:**
```json
{
  "ports": [
    {
      "port_type": "USB-A",
      "version": "3.2",
      "count": 4
    },
    {
      "port_type": "USB-C",
      "version": "4.0",
      "count": 2,
      "features": ["Thunderbolt"]
    }
  ]
}
```

**Response:** `200 OK` - Returns ports (same structure as GET)

---

## Catalog API

Base path: `/v1/catalog`

### CPUs

#### List CPUs

**Endpoint:** `GET /v1/catalog/cpus`

**Response:** `200 OK`
```json
[
  {
    "id": 42,
    "name": "Intel Core i7-1165G7",
    "manufacturer": "Intel",
    "series": "Tiger Lake",
    "model_number": "i7-1165G7",
    "cpu_mark": 10450,
    "single_thread_mark": 3200,
    "igpu_mark": 2100,
    "tdp_watts": 28,
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
  }
]
```

#### Create CPU

**Endpoint:** `POST /v1/catalog/cpus`

**Request Body:**
```json
{
  "name": "AMD Ryzen 7 5800H",
  "manufacturer": "AMD",
  "series": "Cezanne",
  "model_number": "5800H",
  "cpu_mark": 21345,
  "single_thread_mark": 3150,
  "igpu_mark": 1800,
  "tdp_watts": 45
}
```

**Required Fields:**
- `name` (unique)

**Response:** `201 Created` - Returns created CPU

**Error Responses:**
- `400 Bad Request` - CPU already exists

### GPUs

#### List GPUs

**Endpoint:** `GET /v1/catalog/gpus`

**Response:** `200 OK`
```json
[
  {
    "id": 15,
    "name": "NVIDIA GeForce RTX 3060",
    "manufacturer": "NVIDIA",
    "series": "GeForce RTX 30",
    "model_number": "RTX 3060",
    "vram_gb": 12,
    "tdp_watts": 170,
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
  }
]
```

#### Create GPU

**Endpoint:** `POST /v1/catalog/gpus`

**Request Body:**
```json
{
  "name": "NVIDIA GeForce RTX 4060",
  "manufacturer": "NVIDIA",
  "series": "GeForce RTX 40",
  "model_number": "RTX 4060",
  "vram_gb": 8,
  "tdp_watts": 115
}
```

**Response:** `201 Created` - Returns created GPU

### Profiles

#### List Profiles

**Endpoint:** `GET /v1/catalog/profiles`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Gaming Profile",
    "description": "Optimized for gaming workloads",
    "is_default": false,
    "metric_weights": {
      "cpu_performance": 0.3,
      "gpu_performance": 0.4,
      "value": 0.3
    },
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
  }
]
```

#### Create Profile

**Endpoint:** `POST /v1/catalog/profiles`

**Request Body:**
```json
{
  "name": "Productivity Profile",
  "description": "For office and productivity tasks",
  "is_default": false,
  "metric_weights": {
    "cpu_performance": 0.5,
    "efficiency": 0.3,
    "value": 0.2
  }
}
```

**Response:** `201 Created` - Returns created profile

### RAM Specs

#### List RAM Specs

**Endpoint:** `GET /v1/catalog/ram-specs`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Filter by label, generation, or capacity |
| generation | enum | Filter by DDR generation (ddr3, ddr4, ddr5) |
| min_capacity_gb | integer | Minimum capacity |
| max_capacity_gb | integer | Maximum capacity |
| limit | integer | Max results (default: 50, max: 200) |

**Response:** `200 OK`
```json
[
  {
    "id": 8,
    "label": "32GB DDR4-3200",
    "ddr_generation": "ddr4",
    "total_capacity_gb": 32,
    "speed_mhz": 3200,
    "module_count": 2,
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
  }
]
```

#### Create RAM Spec

Get-or-create endpoint (idempotent).

**Endpoint:** `POST /v1/catalog/ram-specs`

**Request Body:**
```json
{
  "label": "64GB DDR5-4800",
  "ddr_generation": "ddr5",
  "total_capacity_gb": 64,
  "speed_mhz": 4800,
  "module_count": 2
}
```

**Response:** `201 Created` - Returns created or existing RAM spec

### Storage Profiles

#### List Storage Profiles

**Endpoint:** `GET /v1/catalog/storage-profiles`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Filter by label, interface, or capacity |
| medium | enum | Filter by medium (nvme, ssd, hdd, emmc, ufs, hybrid) |
| min_capacity_gb | integer | Minimum capacity |
| max_capacity_gb | integer | Maximum capacity |
| limit | integer | Max results (default: 50, max: 200) |

**Response:** `200 OK`
```json
[
  {
    "id": 12,
    "label": "1TB NVMe PCIe 4.0",
    "medium": "nvme",
    "capacity_gb": 1024,
    "interface": "PCIe 4.0 x4",
    "form_factor": "M.2 2280",
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
  }
]
```

#### Create Storage Profile

Get-or-create endpoint (idempotent).

**Endpoint:** `POST /v1/catalog/storage-profiles`

**Request Body:**
```json
{
  "label": "2TB NVMe PCIe 4.0",
  "medium": "nvme",
  "capacity_gb": 2048,
  "interface": "PCIe 4.0 x4",
  "form_factor": "M.2 2280"
}
```

**Response:** `201 Created` - Returns created or existing profile

### Ports Profiles

#### List Ports Profiles

**Endpoint:** `GET /v1/catalog/ports-profiles`

**Response:** `200 OK`
```json
[
  {
    "id": 3,
    "name": "Standard Desktop I/O",
    "description": "Common desktop connectivity",
    "ports": [
      {
        "id": 15,
        "port_type": "USB-A",
        "version": "3.2",
        "count": 6
      },
      {
        "id": 16,
        "port_type": "USB-C",
        "version": "3.2",
        "count": 2
      }
    ],
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
  }
]
```

#### Create Ports Profile

**Endpoint:** `POST /v1/catalog/ports-profiles`

**Request Body:**
```json
{
  "name": "Mini PC Ports",
  "description": "Typical mini PC connectivity",
  "ports": [
    {
      "port_type": "USB-A",
      "version": "3.2",
      "count": 4
    },
    {
      "port_type": "USB-C",
      "version": "4.0",
      "count": 1,
      "features": ["Thunderbolt", "Power Delivery"]
    },
    {
      "port_type": "HDMI",
      "version": "2.1",
      "count": 2
    }
  ]
}
```

**Response:** `201 Created` - Returns created profile

---

## Rules API

Base path: `/api/v1`

The Rules API manages valuation rulesets, rule groups, and individual rules that determine how listings are priced and adjusted.

### Rulesets

#### List Rulesets

**Endpoint:** `GET /api/v1/rulesets`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| active_only | boolean | false | Filter to active rulesets only |
| skip | integer | 0 | Number to skip |
| limit | integer | 100 | Max results (max: 500) |

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Baseline v1.2.0",
    "description": "Standard baseline valuation",
    "version": "1.2.0",
    "is_active": true,
    "priority": 100,
    "created_by": "system",
    "created_at": "2025-10-01T00:00:00Z",
    "updated_at": "2025-10-01T00:00:00Z",
    "metadata": {
      "system_baseline": "true",
      "source_hash": "abc123..."
    },
    "conditions": null,
    "rule_groups": []
  }
]
```

#### Get Ruleset

Get a ruleset with all nested groups and rules.

**Endpoint:** `GET /api/v1/rulesets/{ruleset_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Baseline v1.2.0",
  "description": "Standard baseline valuation",
  "version": "1.2.0",
  "is_active": true,
  "priority": 100,
  "metadata": {
    "system_baseline": "true"
  },
  "conditions": null,
  "rule_groups": [
    {
      "id": 5,
      "ruleset_id": 1,
      "name": "RAM",
      "category": "component",
      "description": "RAM capacity and speed adjustments",
      "display_order": 100,
      "weight": 1.0,
      "is_active": true,
      "metadata": {},
      "basic_managed": false,
      "entity_key": null,
      "rules": [
        {
          "id": 42,
          "group_id": 5,
          "name": "RAM Capacity Deduction",
          "description": "Deduct for RAM below baseline",
          "priority": 100,
          "is_active": true,
          "evaluation_order": 1,
          "version": "1.0",
          "conditions": [
            {
              "field_name": "ram_gb",
              "field_type": "number",
              "operator": "lt",
              "value": 32,
              "logical_operator": "and",
              "group_order": 0
            }
          ],
          "actions": [
            {
              "action_type": "adjust_price",
              "metric": "adjusted_price_usd",
              "value_usd": -30.00,
              "unit_type": "fixed",
              "formula": null,
              "modifiers": null
            }
          ],
          "metadata": {}
        }
      ]
    }
  ]
}
```

#### Create Ruleset

**Endpoint:** `POST /api/v1/rulesets`

**Request Body:**
```json
{
  "name": "Custom Valuation v1.0",
  "description": "Custom pricing rules",
  "version": "1.0.0",
  "priority": 200,
  "is_active": true,
  "metadata": {
    "author": "admin"
  },
  "conditions": null
}
```

**Response:** `200 OK` - Returns created ruleset

#### Update Ruleset

**Endpoint:** `PUT /api/v1/rulesets/{ruleset_id}`

**Request Body:**
```json
{
  "description": "Updated description",
  "is_active": false
}
```

**Response:** `200 OK` - Returns updated ruleset

#### Delete Ruleset

Cascades to all groups and rules.

**Endpoint:** `DELETE /api/v1/rulesets/{ruleset_id}`

**Response:** `200 OK`
```json
{
  "message": "Ruleset deleted successfully"
}
```

### Rule Groups

#### List Rule Groups

**Endpoint:** `GET /api/v1/rule-groups`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| ruleset_id | integer | Filter by ruleset |
| category | string | Filter by category |

**Response:** `200 OK` - Returns array of rule groups

#### Get Rule Group

Get a rule group with all nested rules.

**Endpoint:** `GET /api/v1/rule-groups/{group_id}`

**Response:** `200 OK` - Returns rule group with rules array

#### Create Rule Group

**Endpoint:** `POST /api/v1/rule-groups`

**Request Body:**
```json
{
  "ruleset_id": 1,
  "name": "Storage",
  "category": "component",
  "description": "Storage capacity and type adjustments",
  "display_order": 200,
  "weight": 1.0,
  "is_active": true,
  "metadata": {},
  "basic_managed": false,
  "entity_key": null
}
```

**Response:** `200 OK` - Returns created rule group

#### Update Rule Group

**Endpoint:** `PUT /api/v1/rule-groups/{group_id}`

**Request Body:**
```json
{
  "description": "Updated description",
  "display_order": 150
}
```

**Response:** `200 OK` - Returns updated rule group

**Error Responses:**
- `400 Bad Request` - Cannot edit basic-managed groups

### Valuation Rules

#### List Rules

**Endpoint:** `GET /api/v1/valuation-rules`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| group_id | integer | null | Filter by group |
| active_only | boolean | false | Active rules only |
| skip | integer | 0 | Number to skip |
| limit | integer | 100 | Max results (max: 500) |

**Response:** `200 OK` - Returns array of rules

#### Get Rule

**Endpoint:** `GET /api/v1/valuation-rules/{rule_id}`

**Response:** `200 OK`
```json
{
  "id": 42,
  "group_id": 5,
  "name": "RAM Capacity Deduction",
  "description": "Deduct for RAM below baseline",
  "priority": 100,
  "is_active": true,
  "evaluation_order": 1,
  "version": "1.0",
  "created_by": "system",
  "created_at": "2025-10-01T00:00:00Z",
  "updated_at": "2025-10-01T00:00:00Z",
  "conditions": [
    {
      "field_name": "ram_gb",
      "field_type": "number",
      "operator": "lt",
      "value": 32,
      "logical_operator": "and",
      "group_order": 0
    }
  ],
  "actions": [
    {
      "action_type": "adjust_price",
      "metric": "adjusted_price_usd",
      "value_usd": -30.00,
      "unit_type": "fixed",
      "formula": null,
      "modifiers": null
    }
  ],
  "metadata": {}
}
```

#### Create Rule

**Endpoint:** `POST /api/v1/valuation-rules`

**Request Body:**
```json
{
  "group_id": 5,
  "name": "Storage Upgrade Premium",
  "description": "Add value for NVMe storage",
  "priority": 100,
  "evaluation_order": 1,
  "conditions": [
    {
      "field_name": "primary_storage_type",
      "field_type": "string",
      "operator": "eq",
      "value": "NVMe",
      "logical_operator": "and",
      "group_order": 0
    }
  ],
  "actions": [
    {
      "action_type": "adjust_price",
      "metric": "adjusted_price_usd",
      "value_usd": 25.00,
      "unit_type": "fixed",
      "formula": null,
      "modifiers": null
    }
  ],
  "metadata": {}
}
```

**Condition Operators:**
- `eq` - Equals
- `ne` - Not equals
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `in` - In list
- `not_in` - Not in list
- `contains` - String contains
- `regex` - Regex match

**Action Types:**
- `adjust_price` - Add/subtract from price
- `set_price` - Set absolute price
- `apply_multiplier` - Multiply price by factor
- `calculate` - Formula-based calculation

**Response:** `201 Created` - Returns created rule

#### Update Rule

**Endpoint:** `PUT /api/v1/valuation-rules/{rule_id}`

**Request Body:**
```json
{
  "description": "Updated description",
  "priority": 150,
  "is_active": false
}
```

**Response:** `200 OK` - Returns updated rule

#### Delete Rule

**Endpoint:** `DELETE /api/v1/valuation-rules/{rule_id}`

**Response:** `200 OK`
```json
{
  "message": "Rule deleted successfully"
}
```

### Rule Preview

Preview the impact of a rule before saving.

**Endpoint:** `POST /api/v1/valuation-rules/preview`

**Request Body:**
```json
{
  "conditions": [
    {
      "field_name": "ram_gb",
      "field_type": "number",
      "operator": "gte",
      "value": 64,
      "logical_operator": "and",
      "group_order": 0
    }
  ],
  "actions": [
    {
      "action_type": "adjust_price",
      "metric": "adjusted_price_usd",
      "value_usd": 50.00,
      "unit_type": "fixed"
    }
  ],
  "sample_size": 100,
  "category_filter": null
}
```

**Response:** `200 OK`
```json
{
  "matched_count": 12,
  "total_sampled": 100,
  "match_percentage": 12.0,
  "avg_delta": 50.00,
  "min_delta": 50.00,
  "max_delta": 50.00,
  "sample_listings": [
    {
      "listing_id": 45,
      "title": "Workstation with 64GB RAM",
      "current_price": 1200.00,
      "projected_price": 1250.00,
      "delta": 50.00
    }
  ]
}
```

### Rule Evaluation

#### Evaluate Single Listing

**Endpoint:** `POST /api/v1/valuation-rules/evaluate/{listing_id}`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| ruleset_id | integer | Specific ruleset to use (optional) |

**Response:** `200 OK`
```json
{
  "listing_id": 123,
  "ruleset_id": 1,
  "matched_rules": 5,
  "total_adjustment": -75.00,
  "original_price": 599.99,
  "adjusted_price": 524.99,
  "breakdown": [
    {
      "rule_id": 42,
      "rule_name": "RAM Capacity Deduction",
      "adjustment": -30.00
    }
  ]
}
```

#### Apply Ruleset to Listings

**Endpoint:** `POST /api/v1/valuation-rules/apply`

**Request Body:**
```json
{
  "ruleset_id": 1,
  "listing_ids": [1, 2, 3]
}
```

Leave `listing_ids` null/empty to apply to all active listings.

**Response:** `200 OK`
```json
{
  "results": [
    {
      "listing_id": 1,
      "success": true,
      "matched_rules": 3
    }
  ]
}
```

### Ruleset Packaging

#### Export Ruleset Package

Export a ruleset as a `.dbrs` package file.

**Endpoint:** `POST /api/v1/rulesets/{ruleset_id}/package`

**Request Body:**
```json
{
  "name": "My Custom Ruleset",
  "version": "1.0.0",
  "author": "admin",
  "description": "Custom valuation rules for specific use case",
  "min_app_version": "1.0.0",
  "required_custom_fields": [],
  "tags": ["custom", "valuation"],
  "include_examples": false
}
```

**Response:** `200 OK` - Returns `.dbrs` file download

#### Install Ruleset Package

**Endpoint:** `POST /api/v1/rulesets/install`

**Request:** Multipart form with file upload

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| actor | string | "system" | User installing package |
| merge_strategy | string | "replace" | Conflict resolution (replace/skip/merge) |

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Package installed successfully",
  "rulesets_created": 1,
  "rulesets_updated": 0,
  "rule_groups_created": 5,
  "rules_created": 23,
  "warnings": []
}
```

#### Preview Package Export

Preview what will be included in a package.

**Endpoint:** `POST /api/v1/rulesets/{ruleset_id}/package/preview`

**Request Body:** Same as export package

**Response:** `200 OK`
```json
{
  "package_name": "My Custom Ruleset",
  "package_version": "1.0.0",
  "rulesets_count": 1,
  "rule_groups_count": 5,
  "rules_count": 23,
  "custom_fields_count": 2,
  "dependencies": [],
  "estimated_size_kb": 45.6,
  "readme": "# My Custom Ruleset\n\n..."
}
```

### Audit Log

**Endpoint:** `GET /api/v1/valuation-rules/audit-log`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| rule_id | integer | Filter by rule ID |
| limit | integer | Max results (default: 100, max: 500) |

**Response:** `200 OK`
```json
[
  {
    "id": 156,
    "rule_id": 42,
    "action": "updated",
    "actor": "admin",
    "changes": {
      "priority": [100, 150],
      "description": ["Old", "New"]
    },
    "impact_summary": "Affected 12 listings",
    "created_at": "2025-10-14T10:30:00Z"
  }
]
```

---

## Baseline API

Base path: `/api/v1/baseline`

The Baseline API manages system baseline valuation data and metadata.

### Get Baseline Metadata

Get metadata for the currently active baseline ruleset.

**Endpoint:** `GET /api/v1/baseline/meta`

**Alias:** `GET /api/v1/baseline/metadata`

**Response:** `200 OK`
```json
{
  "version": "1.2.0",
  "source_hash": "abc123def456...",
  "ruleset_id": 1,
  "created_at": "2025-10-01T00:00:00Z",
  "fields": [
    {
      "field_name": "cpu_base_value",
      "field_type": "scalar",
      "unit": "USD",
      "category": "component",
      "description": "Base CPU valuation",
      "default_value": 150.00
    },
    {
      "field_name": "ram_per_gb",
      "field_type": "multiplier",
      "unit": "multiplier",
      "category": "component",
      "description": "RAM value per GB",
      "default_value": 2.50
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - No active baseline ruleset found

### Instantiate Baseline

Create a baseline ruleset from a JSON file (idempotent).

**Endpoint:** `POST /api/v1/baseline/instantiate`

**Request Body:**
```json
{
  "baseline_path": "/path/to/baseline.json",
  "create_adjustments_group": true,
  "actor": "admin"
}
```

**Response:** `200 OK`
```json
{
  "ruleset_id": 1,
  "version": "1.2.0",
  "created": true,
  "hash_match": false,
  "source_hash": "abc123def456...",
  "ruleset_name": "Baseline v1.2.0",
  "created_groups": 8,
  "created_rules": 45,
  "skipped_reason": null
}
```

If ruleset with same hash exists:
```json
{
  "created": false,
  "hash_match": true,
  "skipped_reason": "ruleset_with_hash_exists"
}
```

### Diff Baseline

Compare candidate baseline against current active baseline.

**Endpoint:** `POST /api/v1/baseline/diff`

**Request Body:**
```json
{
  "candidate_json": {
    "version": "1.3.0",
    "fields": {
      "cpu_base_value": 175.00,
      "ram_per_gb": 3.00,
      "new_field": 50.00
    }
  },
  "actor": "admin"
}
```

**Response:** `200 OK`
```json
{
  "added_fields": [
    {
      "field_name": "new_field",
      "new_value": 50.00,
      "field_type": "scalar"
    }
  ],
  "changed_fields": [
    {
      "field_name": "cpu_base_value",
      "old_value": 150.00,
      "new_value": 175.00,
      "delta": 25.00,
      "field_type": "scalar"
    },
    {
      "field_name": "ram_per_gb",
      "old_value": 2.50,
      "new_value": 3.00,
      "delta": 0.50,
      "field_type": "multiplier"
    }
  ],
  "removed_fields": [],
  "summary": {
    "total_changes": 3,
    "added_count": 1,
    "changed_count": 2,
    "removed_count": 0
  },
  "current_version": "1.2.0",
  "candidate_version": "1.3.0"
}
```

### Adopt Baseline

Adopt selected changes from candidate baseline, creating new version.

**Endpoint:** `POST /api/v1/baseline/adopt`

**Request Body:**
```json
{
  "candidate_json": {
    "version": "1.3.0",
    "fields": {
      "cpu_base_value": 175.00,
      "ram_per_gb": 3.00
    }
  },
  "selected_changes": ["cpu_base_value", "ram_per_gb"],
  "trigger_recalculation": true,
  "actor": "admin"
}
```

Leave `selected_changes` null to adopt all changes.

**Response:** `200 OK`
```json
{
  "new_ruleset_id": 2,
  "new_version": "1.3.0",
  "changes_applied": 2,
  "recalculation_job_id": "job-uuid-123",
  "adopted_fields": ["cpu_base_value", "ram_per_gb"],
  "skipped_fields": [],
  "previous_ruleset_id": 1,
  "audit_log_id": 45
}
```

### Field Overrides (Stub Endpoints)

The following endpoints are placeholders for future override management:

**Get Entity Overrides:** `GET /api/v1/baseline/overrides/{entity_key}`

**Upsert Override:** `POST /api/v1/baseline/overrides`

**Delete Field Override:** `DELETE /api/v1/baseline/overrides/{entity_key}/{field_name}`

**Delete Entity Overrides:** `DELETE /api/v1/baseline/overrides/{entity_key}`

### Preview Impact (Stub)

**Endpoint:** `GET /api/v1/baseline/preview`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| entity_key | string | Optional entity filter |
| sample_size | integer | Number of listings to sample (default: 100) |

**Response:** `200 OK` - Returns preview statistics

### Export Baseline (Stub)

**Endpoint:** `GET /api/v1/baseline/export`

**Response:** `200 OK` - Returns baseline metadata with overrides

### Validate Baseline (Stub)

**Endpoint:** `POST /api/v1/baseline/validate`

**Request Body:**
```json
{
  "baseline_json": { ... }
}
```

**Response:** `200 OK`
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

---

## Dashboard API

Base path: `/v1/dashboard`

### Get Dashboard Summary

Get summary statistics and top listings.

**Endpoint:** `GET /v1/dashboard`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| budget | number | 400.0 | Budget for best-under-budget query |

**Response:** `200 OK`
```json
{
  "best_value": {
    "id": 45,
    "title": "Intel NUC 11 - i5-1135G7",
    "price_usd": 399.99,
    "dollar_per_cpu_mark": 0.38,
    ...
  },
  "best_perf_per_watt": {
    "id": 67,
    "title": "AMD Ryzen Mini PC",
    "perf_per_watt": 245.6,
    ...
  },
  "best_under_budget": [
    {
      "id": 23,
      "title": "Budget Gaming NUC",
      "adjusted_price_usd": 375.00,
      "score_composite": 8.2,
      ...
    }
  ]
}
```

---

## Custom Fields API

Base path: `/v1/reference/custom-fields`

### List Custom Fields

**Endpoint:** `GET /v1/reference/custom-fields`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| entity | string | null | Filter by entity type |
| include_inactive | boolean | false | Include inactive fields |
| include_deleted | boolean | false | Include deleted fields |

**Response:** `200 OK`
```json
{
  "fields": [
    {
      "id": 5,
      "entity": "listing",
      "key": "warranty_months",
      "label": "Warranty (Months)",
      "data_type": "number",
      "description": "Warranty period in months",
      "required": false,
      "default_value": null,
      "options": null,
      "is_active": true,
      "visibility": "visible",
      "created_by": "admin",
      "validation": {
        "min": 0,
        "max": 60
      },
      "display_order": 100,
      "created_at": "2025-10-01T00:00:00Z",
      "updated_at": "2025-10-01T00:00:00Z"
    }
  ]
}
```

### Create Custom Field

**Endpoint:** `POST /v1/reference/custom-fields`

**Request Body:**
```json
{
  "entity": "listing",
  "key": "certification",
  "label": "Certification",
  "data_type": "dropdown",
  "description": "Product certifications",
  "required": false,
  "default_value": "None",
  "options": ["None", "ENERGY STAR", "EPEAT Gold", "TCO Certified"],
  "is_active": true,
  "visibility": "visible",
  "created_by": "admin",
  "validation": null,
  "display_order": 200
}
```

**Data Types:**
- `string` - Text field
- `text` - Multi-line text
- `number` - Numeric value
- `boolean` - True/false
- `date` - Date picker
- `dropdown` - Single selection from options
- `multiselect` - Multiple selections from options
- `reference` - Foreign key reference

**Response:** `201 Created` - Returns created field

### Update Custom Field

**Endpoint:** `PATCH /v1/reference/custom-fields/{field_id}`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| force | boolean | false | Allow update despite dependencies |

**Request Body:**
```json
{
  "label": "Product Certification",
  "description": "Environmental and quality certifications",
  "options": ["None", "ENERGY STAR", "EPEAT Gold", "TCO Certified", "ISO 14001"]
}
```

**Response:** `200 OK` - Returns updated field

**Error Responses:**
- `404 Not Found` - Field does not exist
- `409 Conflict` - Field has dependencies (use force=true to override)

### Add Field Option

Add a new option to a dropdown/multiselect field.

**Endpoint:** `POST /v1/reference/custom-fields/{field_id}/options`

**Request Body:**
```json
{
  "value": "RoHS Compliant"
}
```

**Response:** `201 Created`
```json
{
  "field_id": 5,
  "entity": "listing",
  "key": "certification",
  "options": [
    "None",
    "ENERGY STAR",
    "EPEAT Gold",
    "TCO Certified",
    "ISO 14001",
    "RoHS Compliant"
  ]
}
```

### Delete Custom Field

**Endpoint:** `DELETE /v1/reference/custom-fields/{field_id}`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| hard_delete | boolean | false | Permanently remove (vs soft delete) |
| force | boolean | false | Allow delete despite dependencies |

**Response:** `204 No Content`

**Error Responses:**
- `409 Conflict` - Field has dependencies

---

## Field Data API

Base path: `/v1/fields-data`

Generic entity management API for catalog and custom entities.

### List Entities

Get all registered entities.

**Endpoint:** `GET /v1/fields-data/entities`

**Response:** `200 OK`
```json
{
  "entities": [
    {
      "entity": "cpu",
      "label": "CPUs",
      "primary_key": "id",
      "supports_custom_fields": "true"
    },
    {
      "entity": "listing",
      "label": "Listings",
      "primary_key": "id",
      "supports_custom_fields": "true"
    }
  ]
}
```

### Get Entity Schema

Get field schema for an entity (core + custom fields).

**Endpoint:** `GET /v1/fields-data/{entity}/schema`

**Response:** `200 OK`
```json
{
  "entity": "cpu",
  "primary_key": "id",
  "core_fields": [
    {
      "key": "name",
      "label": "Name",
      "data_type": "string",
      "required": true
    }
  ],
  "custom_fields": [
    {
      "id": 12,
      "key": "release_year",
      "label": "Release Year",
      "data_type": "number"
    }
  ]
}
```

### List Entity Records

**Endpoint:** `GET /v1/fields-data/{entity}/records`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Max results (max: 200) |
| offset | integer | 0 | Number to skip |

**Response:** `200 OK`
```json
{
  "entity": "cpu",
  "total": 150,
  "records": [
    {
      "id": 42,
      "name": "Intel Core i7-1165G7",
      "manufacturer": "Intel",
      "release_year": 2020
    }
  ]
}
```

### Create Entity Record

**Endpoint:** `POST /v1/fields-data/{entity}/records`

**Request Body:**
```json
{
  "name": "AMD Ryzen 7 5800H",
  "manufacturer": "AMD",
  "release_year": 2021
}
```

**Response:** `201 Created` - Returns created record

### Update Entity Record

**Endpoint:** `PATCH /v1/fields-data/{entity}/records/{record_id}`

**Request Body:**
```json
{
  "release_year": 2020
}
```

**Response:** `200 OK` - Returns updated record

---

## Settings API

Base path: `/settings`

### Get Setting

**Endpoint:** `GET /settings/{key}`

**Response:** `200 OK`
```json
{
  "good_deal_threshold": 0.85,
  "great_deal_threshold": 0.75,
  "premium_threshold": 1.15
}
```

**Error Responses:**
- `404 Not Found` - Setting does not exist

### Update Setting

**Endpoint:** `PUT /settings/{key}`

**Request Body:**
```json
{
  "value": {
    "good_deal_threshold": 0.80,
    "great_deal_threshold": 0.70,
    "premium_threshold": 1.20
  },
  "description": "Updated valuation thresholds"
}
```

**Response:** `200 OK` - Returns updated value

### Get Valuation Thresholds

Backwards compatibility endpoint.

**Endpoint:** `GET /settings/valuation_thresholds/default`

**Response:** `200 OK`
```json
{
  "good_deal_threshold": 0.85,
  "great_deal_threshold": 0.75,
  "premium_threshold": 1.15
}
```

---

## Import API

Base path: `/v1/imports`

Manage spreadsheet imports and data validation.

### Create Import Session

Upload a spreadsheet file to create an import session.

**Endpoint:** `POST /v1/imports/sessions`

**Request:** Multipart form data
- `upload` (file) - Spreadsheet file (xlsx, csv)
- `declared_entities` (string, optional) - JSON object mapping sheet names to entity types

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "listings.xlsx",
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "status": "pending",
  "checksum": "abc123...",
  "sheet_meta": [
    {
      "sheet_name": "Listings",
      "row_count": 50,
      "columns": ["Title", "Price", "CPU", "RAM GB"]
    }
  ],
  "mappings": {},
  "preview": {},
  "conflicts": {},
  "declared_entities": {},
  "created_at": "2025-10-14T10:30:00Z",
  "updated_at": "2025-10-14T10:30:00Z"
}
```

### List Import Sessions

**Endpoint:** `GET /v1/imports/sessions`

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "listings.xlsx",
      "status": "completed",
      ...
    }
  ]
}
```

### Get Import Session

**Endpoint:** `GET /v1/imports/sessions/{session_id}`

**Response:** `200 OK` - Returns session with latest preview

### Update Import Mappings

Map spreadsheet columns to entity fields.

**Endpoint:** `POST /v1/imports/sessions/{session_id}/mappings`

**Request Body:**
```json
{
  "mappings": {
    "Listings": {
      "Title": "title",
      "Price": "price_usd",
      "CPU": "cpu_name",
      "RAM GB": "ram_gb"
    }
  }
}
```

**Response:** `200 OK` - Returns updated session with conflicts

### Refresh Conflicts

Re-check for import conflicts.

**Endpoint:** `POST /v1/imports/sessions/{session_id}/conflicts`

**Response:** `200 OK` - Returns session with updated conflicts

### Commit Import Session

Execute the import, applying conflict resolutions.

**Endpoint:** `POST /v1/imports/sessions/{session_id}/commit`

**Request Body:**
```json
{
  "conflict_resolutions": [
    {
      "entity": "cpu",
      "identifier": "Intel Core i7-1165G7",
      "action": "use_existing"
    }
  ],
  "component_overrides": [
    {
      "row_index": 5,
      "cpu_match": "Intel Core i7-1165G7",
      "gpu_match": null
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "status": "completed",
  "counts": {
    "listings_created": 45,
    "listings_updated": 5,
    "cpus_created": 2,
    "gpus_created": 1
  },
  "session": { ... },
  "auto_created_cpus": ["AMD Ryzen 5 5600H"]
}
```

### Create Import Field

Create a custom field during import workflow.

**Endpoint:** `POST /v1/imports/sessions/{session_id}/fields`

**Request Body:**
```json
{
  "entity": "listing",
  "key": "vendor",
  "label": "Vendor",
  "data_type": "string",
  "required": false
}
```

**Response:** `201 Created`
```json
{
  "field": {
    "id": 15,
    "entity": "listing",
    "key": "vendor",
    ...
  },
  "session": { ... }
}
```

### Import Workbook (Legacy)

Direct import from file path (CLI-style).

**Endpoint:** `POST /v1/imports/workbook`

**Request Body:**
```json
{
  "path": "/path/to/workbook.xlsx"
}
```

**Response:** `200 OK`
```json
{
  "status": "completed",
  "path": "/path/to/workbook.xlsx",
  "counts": {
    "listings": 50,
    "cpus": 12,
    "gpus": 5
  }
}
```

---

## Health API

Base path: `/api/v1/health`

### Check Overall Health

**Endpoint:** `GET /api/v1/health/`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "subsystems": {
    "baseline": "healthy",
    "database": "healthy",
    "api": "healthy"
  },
  "timestamp": "2025-10-14T10:30:00Z"
}
```

**Status Values:**
- `healthy` - All checks passed
- `warning` - Non-critical issues detected
- `error` - Critical issues detected

### Check Baseline Health

**Endpoint:** `GET /api/v1/health/baseline`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| expected_hash | string | Expected baseline source hash |

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "checks": {
    "baseline_exists": true,
    "baseline_version": "1.2.0",
    "baseline_age_days": 14,
    "adjustments_group_exists": true,
    "hash_match": true
  },
  "warnings": [],
  "errors": [],
  "timestamp": "2025-10-14T10:30:00Z"
}
```

**Warnings:**
- Baseline older than 90 days
- No Basic Adjustments group found

**Errors:**
- No active baseline ruleset
- Hash mismatch (if expected_hash provided)

---

## Common Patterns

### Error Handling

All endpoints follow consistent error handling:

**Validation Errors (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "price_usd"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Business Logic Errors (400):**
```json
{
  "detail": "CPU already exists"
}
```

**Resource Not Found (404):**
```json
{
  "detail": "Listing not found"
}
```

**Conflict Errors (409):**
```json
{
  "detail": {
    "message": "Field has dependencies and cannot be modified",
    "usage": {
      "total": 45,
      "counts": {
        "listing": 45
      }
    }
  }
}
```

### Pagination

Endpoints using pagination accept:
- `limit` - Max results (default varies, typically 50)
- `offset` - Number to skip

**Example:**
```
GET /v1/listings?limit=25&offset=50
```

Returns items 51-75.

### Filtering

List endpoints support various filters via query parameters:

**String Search:**
```
GET /v1/catalog/ram-specs?search=ddr4
```

**Enum Filtering:**
```
GET /v1/catalog/storage-profiles?medium=nvme
```

**Range Filtering:**
```
GET /v1/catalog/ram-specs?min_capacity_gb=32&max_capacity_gb=64
```

### Sorting

Sorting is built into specific endpoints (not universally configurable):
- Listings: By `created_at DESC`
- CPUs/GPUs: By `name ASC`
- RAM Specs: By capacity DESC, speed DESC
- Storage Profiles: By capacity DESC, medium ASC

### Idempotency

Certain endpoints are idempotent (safe to retry):
- `POST /v1/catalog/ram-specs` - Get-or-create
- `POST /v1/catalog/storage-profiles` - Get-or-create
- `POST /api/v1/baseline/instantiate` - Only creates if hash doesn't exist

### Async Operations

Some operations trigger background jobs:
- Bulk metric recalculation
- Baseline adoption with recalculation
- Large imports

These return immediately with a job ID for status polling (future enhancement).

### CORS

CORS is enabled for frontend access. Allowed origins configured via environment.

### Rate Limiting

Not currently implemented. Future consideration for production deployments.

---

## File Locations

**API Route Definitions:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/`

**Service Layer:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/`

**Database Models:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`

**Request/Response Schemas:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/schemas/`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/`

**Settings:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/settings.py`
