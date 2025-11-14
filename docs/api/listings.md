# Listings API

Comprehensive API documentation for managing PC listings with pricing adjustments, performance metrics, and valuation rules.

## Overview

The Listings API provides endpoints for creating, reading, updating, and managing PC listings in Deal Brain. Each listing can include component specifications, pricing adjustments via valuation rules, and calculated performance metrics. The API supports both individual and bulk operations, making it easy to manage large inventories.

## Authentication

All endpoints require authentication via JWT bearer token from Clerk:

```bash
Authorization: Bearer <token>
```

## List Listings

### `GET /api/v1/listings`

Retrieve a paginated list of all listings, ordered by most recent first.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum number of listings to return (max: 200) |
| `offset` | integer | 0 | Number of listings to skip for pagination |

**Response (200 OK):**

```typescript
interface ListingRead {
  // Identifiers and Metadata
  id: number;                          // Unique listing ID
  title: string;                       // Listing title (required)
  listing_url: string | null;          // Primary marketplace URL
  other_urls: Array<{                  // Additional URLs with optional labels
    url: string;
    label: string | null;
  }>;
  seller: string | null;               // Seller or vendor name

  // Pricing
  price_usd: number;                   // Original listing price in USD
  price_date: string | null;           // ISO 8601 timestamp of price capture
  adjusted_price_usd: number | null;   // Price after valuation rule adjustments

  // Condition and Status
  condition: "new" | "refurb" | "used";
  status: "active" | "sold" | "delisted";

  // Components
  cpu_id: number | null;
  cpu: CpuRead | null;                 // Resolved CPU with benchmark data
  cpu_name: string | null;             // Denormalized CPU name
  gpu_id: number | null;
  gpu: GpuRead | null;                 // Resolved GPU data
  gpu_name: string | null;             // Denormalized GPU name

  // RAM Configuration
  ram_gb: number;                      // Total RAM in GB
  ram_spec_id: number | null;
  ram_spec: RamSpecRead | null;        // Detailed RAM spec (DDR generation, speed)
  ram_type: string | null;             // DDR generation (e.g., DDR4, DDR5)
  ram_speed_mhz: number | null;        // RAM speed in MHz
  ram_notes: string | null;

  // Storage
  primary_storage_gb: number;
  primary_storage_type: string | null; // NVMe, SSD, HDD, Hybrid, eMMC, UFS
  primary_storage_profile_id: number | null;
  primary_storage_profile: StorageProfileRead | null;
  secondary_storage_gb: number | null;
  secondary_storage_type: string | null;
  secondary_storage_profile_id: number | null;
  secondary_storage_profile: StorageProfileRead | null;

  // Product Metadata
  device_model: string | null;
  manufacturer: string | null;
  series: string | null;
  model_number: string | null;
  form_factor: string | null;          // Laptop, Desktop, Mini-PC, etc.

  // Performance Metrics
  score_cpu_multi: number | null;      // Multi-thread CPU Mark score
  score_cpu_single: number | null;     // Single-thread CPU Mark score
  score_gpu: number | null;            // GPU performance score
  score_composite: number | null;      // Weighted composite score
  dollar_per_cpu_mark: number | null;  // Deprecated: use dollar_per_cpu_mark_multi
  dollar_per_single_mark: number | null;
  perf_per_watt: number | null;        // CPU performance per watt

  // New Performance Metrics (v1.1+)
  dollar_per_cpu_mark_single: number | null;
  dollar_per_cpu_mark_single_adjusted: number | null;
  dollar_per_cpu_mark_multi: number | null;
  dollar_per_cpu_mark_multi_adjusted: number | null;

  // Valuation
  valuation_breakdown: object | null;  // Detailed breakdown of adjustments
  active_profile_id: number | null;    // Score profile used for metrics
  ruleset_id: number | null;           // Static ruleset override if any

  // Ports and Connectivity
  ports_profile_id: number | null;
  ports_profile: PortsProfileRead | null;

  // Metadata
  os_license: string | null;
  other_components: string[];
  notes: string | null;
  components: ListingComponentRead[];
  thumbnail_url: string | null;        // Extracted from raw_listing_json

  // Timestamps
  created_at: string;                  // ISO 8601 creation timestamp
  updated_at: string;                  // ISO 8601 last update timestamp
}
```

**Example Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/listings?limit=10&offset=0' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Example Response:**

```json
[
  {
    "id": 1,
    "title": "Dell XPS 13 Gaming Laptop",
    "price_usd": 799.99,
    "adjusted_price_usd": 749.99,
    "condition": "refurb",
    "status": "active",
    "cpu_id": 5,
    "cpu_name": "Intel Core i7-12700H",
    "ram_gb": 16,
    "ram_type": "DDR4",
    "primary_storage_gb": 512,
    "primary_storage_type": "SSD",
    "score_cpu_multi": 18500,
    "score_cpu_single": 2100,
    "dollar_per_cpu_mark_multi": 0.041,
    "adjusted_price_usd": 749.99,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:22:00Z"
  }
]
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |
| 400 | Bad Request | Invalid query parameters (e.g., limit > 200) |

---

## Create Listing

### `POST /api/v1/listings`

Create a new listing with optional components and valuation configuration.

**Request Body:**

```typescript
interface ListingCreate {
  // Required
  title: string;                       // Listing title (min length: 3)
  price_usd: number;                   // Price in USD (must be >= 0)

  // Optional: URLs
  listing_url: string | null;          // Primary marketplace URL (http/https required)
  other_urls: Array<{
    url: string;
    label: string | null;
  }> | null;

  // Optional: Seller
  seller: string | null;

  // Optional: Condition & Status
  condition?: "new" | "refurb" | "used";  // Default: "used"
  status?: "active" | "sold" | "delisted"; // Default: "active"

  // Optional: Components (CPU, GPU, RAM, Storage)
  cpu_id: number | null;
  gpu_id: number | null;
  ram_gb: number;
  ram_spec_id: number | null;          // Or provide ram_spec object
  ram_spec?: {
    ddr_generation: string;            // ddr3, ddr4, ddr5
    speed_mhz: number;
    capacity_gb: number;
  };

  // Optional: Primary Storage
  primary_storage_gb: number;
  primary_storage_type: string | null; // NVMe, SSD, HDD, Hybrid, eMMC, UFS
  primary_storage_profile_id: number | null;
  primary_storage_profile?: {
    medium: string;
    capacity_gb: number;
  };

  // Optional: Secondary Storage
  secondary_storage_gb: number | null;
  secondary_storage_type: string | null;
  secondary_storage_profile_id: number | null;
  secondary_storage_profile?: {
    medium: string;
    capacity_gb: number;
  };

  // Optional: Product Metadata
  device_model: string | null;
  manufacturer: string | null;
  series: string | null;
  model_number: string | null;
  form_factor: string | null;

  // Optional: Ports
  ports_profile_id: number | null;

  // Optional: OS & Notes
  os_license: string | null;
  other_components: string[];
  notes: string | null;

  // Optional: Valuation
  ruleset_id: number | null;           // Static ruleset override

  // Optional: Components List
  components?: Array<{
    component_type: string;
    name: string | null;
    quantity: number;
    metadata_json: object | null;
    adjustment_value_usd: number | null;
  }>;

  // Optional: Custom Attributes
  attributes?: Record<string, any>;
}
```

**Response (201 Created):**

Returns the created `ListingRead` object (see List Listings response schema).

**Example Request:**

```bash
curl -X POST 'http://localhost:8000/api/v1/listings' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "title": "Dell XPS 13 Gaming Laptop",
    "price_usd": 799.99,
    "condition": "refurb",
    "cpu_id": 5,
    "ram_gb": 16,
    "primary_storage_gb": 512,
    "primary_storage_type": "SSD",
    "listing_url": "https://ebay.com/itm/123456789",
    "seller": "TechStore",
    "notes": "Excellent condition, minimal use"
  }'
```

**TypeScript Example:**

```typescript
import axios from 'axios';

const createListing = async (token: string) => {
  const response = await axios.post('/api/v1/listings', {
    title: 'Dell XPS 13 Gaming Laptop',
    price_usd: 799.99,
    condition: 'refurb',
    cpu_id: 5,
    ram_gb: 16,
    primary_storage_gb: 512,
    primary_storage_type: 'SSD',
    listing_url: 'https://ebay.com/itm/123456789',
    seller: 'TechStore',
    notes: 'Excellent condition, minimal use'
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });

  return response.data; // ListingRead
};
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Validation Error | Invalid input (e.g., missing title, invalid price) |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Referenced CPU, GPU, or ruleset doesn't exist |
| 422 | Unprocessable Entity | Invalid enum values or reference IDs |

---

## Get Listing Schema

### `GET /api/v1/listings/schema`

Retrieve the schema definition for listings, including all core and custom fields with their metadata and validation rules.

**Response (200 OK):**

```typescript
interface ListingSchemaResponse {
  core_fields: ListingFieldSchema[];
  custom_fields: CustomFieldResponse[];
}

interface ListingFieldSchema {
  key: string;                         // Field identifier
  label: string;                       // Display label
  data_type: string;                   // string, number, enum, reference, text, list
  required: boolean;                   // Whether field is required
  editable: boolean;                   // Whether field can be modified
  description: string | null;
  options: string[] | null;            // For enum fields
  validation: {                        // Validation constraints
    min_length?: number;
    max_length?: number;
    min?: number;
    max?: number;
    pattern?: string;
  } | null;
  origin: "core" | "custom";           // Whether field is built-in or custom
}

interface CustomFieldResponse {
  id: number;
  key: string;
  label: string;
  data_type: string;
  required: boolean;
  options: string[] | null;
  default_value: any | null;
  entity_type: string;                 // "listing"
}
```

**Example Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/listings/schema' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Example Response:**

```json
{
  "core_fields": [
    {
      "key": "title",
      "label": "Title",
      "data_type": "string",
      "required": true,
      "editable": true,
      "description": "Canonical listing label",
      "validation": { "min_length": 3 },
      "origin": "core"
    },
    {
      "key": "price_usd",
      "label": "Price (USD)",
      "data_type": "number",
      "required": true,
      "editable": true,
      "validation": { "min": 0 },
      "origin": "core"
    },
    {
      "key": "condition",
      "label": "Condition",
      "data_type": "enum",
      "required": false,
      "editable": true,
      "options": ["new", "refurb", "used"],
      "origin": "core"
    },
    {
      "key": "cpu_id",
      "label": "CPU",
      "data_type": "reference",
      "required": false,
      "editable": true,
      "description": "Linked CPU identifier",
      "origin": "core"
    }
  ],
  "custom_fields": [
    {
      "id": 1,
      "key": "warranty_months",
      "label": "Warranty Period (Months)",
      "data_type": "number",
      "required": false,
      "options": null,
      "default_value": 0,
      "entity_type": "listing"
    }
  ]
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |

---

## Get Listing

### `GET /api/v1/listings/{listing_id}`

Retrieve detailed information about a specific listing.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing to retrieve |

**Response (200 OK):**

Returns a `ListingRead` object (see List Listings response schema).

**Example Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/listings/1' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Example Response:**

```json
{
  "id": 1,
  "title": "Dell XPS 13 Gaming Laptop",
  "price_usd": 799.99,
  "adjusted_price_usd": 749.99,
  "condition": "refurb",
  "status": "active",
  "cpu_id": 5,
  "cpu_name": "Intel Core i7-12700H",
  "ram_gb": 16,
  "ram_type": "DDR4",
  "ram_speed_mhz": 3200,
  "primary_storage_gb": 512,
  "primary_storage_type": "SSD",
  "score_cpu_multi": 18500,
  "score_cpu_single": 2100,
  "dollar_per_cpu_mark_multi": 0.041,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:22:00Z"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing with given ID doesn't exist |

---

## Update Listing (Full)

### `PUT /api/v1/listings/{listing_id}`

Perform a full replacement update of a listing. This replaces the entire listing with the provided data.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing to update |

**Request Body:**

Same schema as POST /api/v1/listings (ListingCreate).

**Response (200 OK):**

Returns the updated `ListingRead` object.

**Example Request:**

```bash
curl -X PUT 'http://localhost:8000/api/v1/listings/1' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "title": "Dell XPS 13 Updated",
    "price_usd": 899.99,
    "condition": "new",
    "cpu_id": 5,
    "ram_gb": 32,
    "primary_storage_gb": 1024,
    "primary_storage_type": "NVMe"
  }'
```

**TypeScript Example:**

```typescript
const updateListing = async (listingId: number, token: string) => {
  const response = await axios.put(`/api/v1/listings/${listingId}`, {
    title: 'Dell XPS 13 Updated',
    price_usd: 899.99,
    condition: 'new',
    cpu_id: 5,
    ram_gb: 32,
    primary_storage_gb: 1024,
    primary_storage_type: 'NVMe'
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });

  return response.data;
};
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Validation Error | Invalid input data |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing doesn't exist |
| 422 | Unprocessable Entity | Invalid enum or reference values |

---

## Partial Update Listing

### `PATCH /api/v1/listings/{listing_id}`

Update specific fields of a listing without replacing the entire record. Only provided fields are updated.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing to update |

**Request Body:**

```typescript
interface ListingPartialUpdateRequest {
  fields?: {                           // Fields to update (optional)
    title?: string;
    price_usd?: number;
    condition?: "new" | "refurb" | "used";
    status?: "active" | "sold" | "delisted";
    cpu_id?: number | null;
    gpu_id?: number | null;
    ram_gb?: number;
    ram_spec_id?: number | null;
    primary_storage_gb?: number;
    primary_storage_type?: string | null;
    secondary_storage_gb?: number | null;
    secondary_storage_type?: string | null;
    os_license?: string | null;
    notes?: string | null;
    ruleset_id?: number | null;
    [key: string]: any;                // Other mutable fields
  };
  attributes?: {                       // Custom attributes to update
    [key: string]: any;
  };
}
```

**Response (200 OK):**

Returns the updated `ListingRead` object.

**Example Request:**

```bash
curl -X PATCH 'http://localhost:8000/api/v1/listings/1' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "fields": {
      "price_usd": 749.99,
      "condition": "refurb"
    },
    "attributes": {
      "notes_updated_by": "admin",
      "last_price_check": "2024-01-20"
    }
  }'
```

**TypeScript Example:**

```typescript
const partialUpdateListing = async (listingId: number, token: string) => {
  const response = await axios.patch(`/api/v1/listings/${listingId}`, {
    fields: {
      price_usd: 749.99,
      condition: 'refurb',
      notes: 'Price reduced for quick sale'
    },
    attributes: {
      last_updated_reason: 'price_adjustment'
    }
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });

  return response.data;
};
```

**Notes:**

- Only provided fields are updated; omitted fields remain unchanged
- Metrics are automatically recalculated when relevant fields change
- Use this endpoint for making targeted changes without replacing entire listing

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Validation Error | Invalid field values |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing doesn't exist |
| 422 | Unprocessable Entity | Invalid enum or reference values |

---

## Update Valuation Overrides

### `PATCH /api/v1/listings/{listing_id}/valuation-overrides`

Update the valuation ruleset configuration for a listing. Allows switching between automatic ruleset selection and static assignment.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing |

**Request Body:**

```typescript
interface ListingValuationOverrideRequest {
  mode: "auto" | "static";            // auto = dynamic selection, static = fixed ruleset
  ruleset_id?: number | null;          // Required when mode is "static"
  disabled_rulesets?: number[];        // Rulesets to exclude when mode is "auto"
}
```

**Response (200 OK):**

```typescript
interface ListingValuationOverrideResponse {
  mode: "auto" | "static";
  ruleset_id: number | null;
  disabled_rulesets: number[];
}
```

**Example Request (Static Mode):**

```bash
curl -X PATCH 'http://localhost:8000/api/v1/listings/1/valuation-overrides' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "mode": "static",
    "ruleset_id": 3
  }'
```

**Example Request (Auto Mode with Exclusions):**

```bash
curl -X PATCH 'http://localhost:8000/api/v1/listings/1/valuation-overrides' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "mode": "auto",
    "disabled_rulesets": [2, 5]
  }'
```

**TypeScript Example:**

```typescript
// Switch to static ruleset
const setStaticRuleset = async (listingId: number, rulesetId: number, token: string) => {
  const response = await axios.patch(
    `/api/v1/listings/${listingId}/valuation-overrides`,
    {
      mode: 'static',
      ruleset_id: rulesetId
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};

// Switch to auto with exclusions
const setAutoMode = async (listingId: number, token: string) => {
  const response = await axios.patch(
    `/api/v1/listings/${listingId}/valuation-overrides`,
    {
      mode: 'auto',
      disabled_rulesets: []
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
};
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Ruleset is inactive and cannot be assigned |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing or ruleset doesn't exist |
| 422 | Unprocessable Entity | Invalid mode or missing ruleset_id for static mode |

---

## Bulk Update Listings

### `POST /api/v1/listings/bulk-update`

Update the same fields across multiple listings in a single request.

**Request Body:**

```typescript
interface ListingBulkUpdateRequest {
  listing_ids: number[];               // IDs of listings to update
  fields?: {                           // Fields to update
    [key: string]: any;
  };
  attributes?: {                       // Custom attributes to update
    [key: string]: any;
  };
}
```

**Response (200 OK):**

```typescript
interface ListingBulkUpdateResponse {
  updated: ListingRead[];              // Updated listings
  updated_count: number;               // Count of updated listings
}
```

**Example Request:**

```bash
curl -X POST 'http://localhost:8000/api/v1/listings/bulk-update' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "listing_ids": [1, 2, 3, 4, 5],
    "fields": {
      "status": "active"
    },
    "attributes": {
      "bulk_update_date": "2024-01-20",
      "bulk_update_reason": "inventory_refresh"
    }
  }'
```

**TypeScript Example:**

```typescript
const bulkUpdateListings = async (
  listingIds: number[],
  updates: { fields?: Record<string, any>; attributes?: Record<string, any> },
  token: string
) => {
  const response = await axios.post('/api/v1/listings/bulk-update', {
    listing_ids: listingIds,
    ...updates
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });

  return response.data; // { updated: ListingRead[], updated_count: number }
};

// Usage
const result = await bulkUpdateListings(
  [1, 2, 3],
  {
    fields: { status: 'sold' },
    attributes: { archived: true }
  },
  token
);

console.log(`Updated ${result.updated_count} listings`);
```

**Notes:**

- Metrics are automatically recalculated for all updated listings
- If no listings match the IDs, endpoint returns 404
- Empty listing_ids array returns empty response

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Validation Error | Invalid field values |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | No listings matched the provided IDs |
| 422 | Unprocessable Entity | Invalid reference values |

---

## Get Valuation Breakdown

### `GET /api/v1/listings/{listing_id}/valuation-breakdown`

Retrieve a detailed breakdown of how a listing's adjusted price was calculated, including all applied valuation rules and their individual contributions.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing |

**Response (200 OK):**

```typescript
interface ValuationBreakdownResponse {
  listing_id: number;
  listing_title: string;

  // Pricing
  base_price_usd: number;              // Original listing price
  adjusted_price_usd: number;          // Price after adjustments
  total_adjustment: number;            // Total adjustment (positive or negative)
  total_deductions: number | null;     // Sum of deductions (legacy format)

  // Rules Applied
  matched_rules_count: number;         // Number of rules that matched
  ruleset_id: number | null;
  ruleset_name: string | null;

  // Detailed Adjustments
  adjustments: ValuationAdjustmentDetail[];
  legacy_lines: LegacyValuationLine[]; // For backwards compatibility
}

interface ValuationAdjustmentDetail {
  rule_id: number | null;
  rule_name: string;                   // Rule display name
  rule_description: string | null;
  rule_group_id: number | null;
  rule_group_name: string | null;
  adjustment_amount: number;           // USD adjustment
  actions: ValuationAdjustmentAction[];
}

interface ValuationAdjustmentAction {
  action_type: string | null;
  metric: string | null;               // Metric affected
  value: number;                       // Value contributed (USD)
  details: object | null;              // Raw config details
  error: string | null;                // Error if action failed
}

interface LegacyValuationLine {
  label: string;
  component_type: string;
  quantity: number;
  unit_value: number;
  condition_multiplier: number;
  deduction_usd: number;
  adjustment_usd: number | null;
}
```

**Example Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/listings/1/valuation-breakdown' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Example Response:**

```json
{
  "listing_id": 1,
  "listing_title": "Dell XPS 13 Gaming Laptop",
  "base_price_usd": 799.99,
  "adjusted_price_usd": 749.99,
  "total_adjustment": -50.00,
  "matched_rules_count": 2,
  "ruleset_id": 1,
  "ruleset_name": "Gaming PC Valuation v2",
  "adjustments": [
    {
      "rule_id": 10,
      "rule_name": "Refurbished Condition Penalty",
      "rule_group_name": "Condition Adjustments",
      "adjustment_amount": -50.00,
      "actions": [
        {
          "action_type": "multiply",
          "metric": "price",
          "value": -50.00,
          "details": {
            "condition": "refurb",
            "multiplier": 0.9375
          }
        }
      ]
    },
    {
      "rule_id": 11,
      "rule_name": "High RAM Bonus",
      "rule_group_name": "Component Bonuses",
      "adjustment_amount": 0.00,
      "actions": []
    }
  ],
  "legacy_lines": []
}
```

**TypeScript Example:**

```typescript
const getValuationBreakdown = async (listingId: number, token: string) => {
  const response = await axios.get(
    `/api/v1/listings/${listingId}/valuation-breakdown`,
    { headers: { Authorization: `Bearer ${token}` } }
  );

  const breakdown = response.data;

  console.log(`Base price: $${breakdown.base_price_usd}`);
  console.log(`Adjusted price: $${breakdown.adjusted_price_usd}`);
  console.log(`Total adjustment: $${breakdown.total_adjustment}`);
  console.log(`Matched rules: ${breakdown.matched_rules_count}`);

  breakdown.adjustments.forEach(adj => {
    console.log(`- ${adj.rule_name}: $${adj.adjustment_amount}`);
    adj.actions.forEach(action => {
      console.log(`  Action: ${action.action_type} on ${action.metric} = $${action.value}`);
    });
  });

  return breakdown;
};
```

**Notes:**

- Includes both active rules (with adjustments) and inactive rules (zero adjustment)
- Actions show the detailed breakdown of how each rule calculated its adjustment
- Legacy lines provide backwards compatibility with older valuation format

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing doesn't exist |

---

## Recalculate Listing Metrics

### `POST /api/v1/listings/{listing_id}/recalculate-metrics`

Recalculate all performance metrics for a single listing based on its CPU and other components.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing |

**Request Body:**

No request body required.

**Response (200 OK):**

Returns the updated `ListingRead` object with recalculated metrics.

**Example Request:**

```bash
curl -X POST 'http://localhost:8000/api/v1/listings/1/recalculate-metrics' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**TypeScript Example:**

```typescript
const recalculateMetrics = async (listingId: number, token: string) => {
  const response = await axios.post(
    `/api/v1/listings/${listingId}/recalculate-metrics`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
  );

  return response.data; // Updated ListingRead
};
```

**Notes:**

- Recalculates metrics including:
  - `score_cpu_multi` - Multi-thread CPU performance score
  - `score_cpu_single` - Single-thread CPU performance score
  - `score_gpu` - GPU performance score
  - `score_composite` - Weighted composite score
  - `dollar_per_cpu_mark_multi` - $/CPU Mark (multi-thread)
  - `dollar_per_cpu_mark_single` - $/CPU Mark (single-thread)
  - `perf_per_watt` - Performance per watt
- Requires listing to have a CPU assigned
- Useful when CPU benchmark data is updated

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing doesn't exist |

---

## Bulk Recalculate Metrics

### `POST /api/v1/listings/bulk-recalculate-metrics`

Recalculate performance metrics for multiple listings. If no listing IDs provided, updates all listings.

**Request Body:**

```typescript
interface BulkRecalculateRequest {
  listing_ids?: number[] | null;       // IDs to update. If null, updates all listings.
}
```

**Response (200 OK):**

```typescript
interface BulkRecalculateResponse {
  updated_count: number;               // Number of listings updated
  message: string;                     // Status message
}
```

**Example Request (Specific Listings):**

```bash
curl -X POST 'http://localhost:8000/api/v1/listings/bulk-recalculate-metrics' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "listing_ids": [1, 2, 3, 4, 5]
  }'
```

**Example Request (All Listings):**

```bash
curl -X POST 'http://localhost:8000/api/v1/listings/bulk-recalculate-metrics' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"listing_ids": null}'
```

**TypeScript Example:**

```typescript
// Recalculate for specific listings
const recalculateBatch = async (listingIds: number[], token: string) => {
  const response = await axios.post(
    '/api/v1/listings/bulk-recalculate-metrics',
    { listing_ids: listingIds },
    { headers: { Authorization: `Bearer ${token}` } }
  );

  console.log(`${response.data.updated_count} listings updated`);
  return response.data;
};

// Recalculate all
const recalculateAll = async (token: string) => {
  const response = await axios.post(
    '/api/v1/listings/bulk-recalculate-metrics',
    { listing_ids: null },
    { headers: { Authorization: `Bearer ${token}` } }
  );

  console.log(response.data.message); // "Updated X listing(s)"
  return response.data;
};
```

**Notes:**

- Omitting `listing_ids` or setting it to `null` triggers full database recalculation
- Use for batch updates after CPU benchmark data imports
- Only updates listings with assigned CPUs

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |

---

## Update Listing Ports

### `POST /api/v1/listings/{listing_id}/ports`

Create or update connectivity ports for a listing.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing |

**Request Body:**

```typescript
interface UpdatePortsRequest {
  ports: Array<{
    port_type: string;                 // e.g., USB-A, USB-C, HDMI, DisplayPort
    quantity: number;                  // 1-16
  }>;
}
```

**Response (200 OK):**

```typescript
interface PortsResponse {
  ports: Array<{
    port_type: string;
    quantity: number;
  }>;
}
```

**Example Request:**

```bash
curl -X POST 'http://localhost:8000/api/v1/listings/1/ports' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "ports": [
      { "port_type": "USB-A", "quantity": 3 },
      { "port_type": "USB-C", "quantity": 2 },
      { "port_type": "HDMI", "quantity": 1 },
      { "port_type": "DisplayPort", "quantity": 1 },
      { "port_type": "3.5mm Audio Jack", "quantity": 1 }
    ]
  }'
```

**TypeScript Example:**

```typescript
const updatePorts = async (listingId: number, token: string) => {
  const response = await axios.post(
    `/api/v1/listings/${listingId}/ports`,
    {
      ports: [
        { port_type: 'USB-A', quantity: 3 },
        { port_type: 'USB-C', quantity: 2 },
        { port_type: 'HDMI', quantity: 1 },
        { port_type: 'DisplayPort', quantity: 1 }
      ]
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );

  return response.data;
};
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Validation Error | Invalid port type or quantity |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing doesn't exist |
| 422 | Unprocessable Entity | Quantity out of range (1-16) |

---

## Get Listing Ports

### `GET /api/v1/listings/{listing_id}/ports`

Retrieve the connectivity ports for a listing.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `listing_id` | integer | ID of the listing |

**Response (200 OK):**

```typescript
interface PortsResponse {
  ports: Array<{
    port_type: string;
    quantity: number;
  }>;
}
```

**Example Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/listings/1/ports' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Example Response:**

```json
{
  "ports": [
    { "port_type": "USB-A", "quantity": 3 },
    { "port_type": "USB-C", "quantity": 2 },
    { "port_type": "HDMI", "quantity": 1 },
    { "port_type": "DisplayPort", "quantity": 1 }
  ]
}
```

**TypeScript Example:**

```typescript
const getPorts = async (listingId: number, token: string) => {
  const response = await axios.get(
    `/api/v1/listings/${listingId}/ports`,
    { headers: { Authorization: `Bearer ${token}` } }
  );

  const ports = response.data.ports;
  console.log(`Listing ${listingId} has ${ports.length} port types`);

  ports.forEach(port => {
    console.log(`- ${port.quantity}x ${port.port_type}`);
  });

  return response.data;
};
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Listing doesn't exist |

---

## Error Response Format

All error responses follow this format:

```typescript
interface ErrorResponse {
  detail: string;                      // Error message
}
```

**Example:**

```json
{
  "detail": "Listing not found"
}
```

---

## Filtering and Search

While the basic list endpoint (`GET /api/v1/listings`) doesn't include advanced filtering, you can implement client-side filtering on the returned data. For server-side advanced filtering, consider implementing additional query parameters in future versions:

Potential enhancements:
- `?condition=refurb` - Filter by condition
- `?status=active` - Filter by status
- `?min_price=100&max_price=1000` - Price range
- `?search=Dell` - Full-text search on title
- `?has_cpu=1` - Filter by component availability
- `?min_score=0.5` - Filter by composite score

---

## Performance Notes

- **List endpoint**: Pagination is required (default 50 items)
- **Bulk operations**: Maximum listing IDs per request is not enforced, but recommend batches of 100-1000
- **Metrics recalculation**: Can be CPU-intensive for large batches; consider scheduling during low-traffic periods
- **Valuation breakdown**: Includes database joins for rule details; optimize with caching if called frequently
- **Request timeout**: 30 seconds for bulk operations, 10 seconds for single-item operations

---

## Common Workflows

### Create and Score a Listing

```typescript
// 1. Create listing
const listing = await createListing(token, {
  title: 'Gaming PC',
  price_usd: 999.99,
  cpu_id: 5,
  ram_gb: 16
});

// 2. Get valuation breakdown
const breakdown = await getValuationBreakdown(listing.id, token);
console.log(`Adjusted price: $${breakdown.adjusted_price_usd}`);

// 3. Get full metrics
const updated = await recalculateMetrics(listing.id, token);
console.log(`Dollar per CPU Mark: $${updated.dollar_per_cpu_mark_multi}`);
```

### Bulk Import and Configure

```typescript
// 1. Create multiple listings
const listings = [];
for (const data of importData) {
  const listing = await createListing(token, data);
  listings.push(listing.id);
}

// 2. Apply bulk updates
await bulkUpdateListings(
  listings,
  { fields: { status: 'active', ruleset_id: 1 } },
  token
);

// 3. Recalculate all metrics
await bulkRecalculateMetrics(listings, token);
```

### Update Valuation Strategy

```typescript
// 1. Switch to specific ruleset
await updateValuationOverrides(listingId, {
  mode: 'static',
  ruleset_id: 3
}, token);

// 2. Get updated valuation
const breakdown = await getValuationBreakdown(listingId, token);
console.log(`New adjusted price: $${breakdown.adjusted_price_usd}`);
```

---

## Related Endpoints

- **CPU Catalog**: GET /api/v1/cpus - Manage CPU database
- **GPU Catalog**: GET /api/v1/gpus - Manage GPU database
- **Valuation Rulesets**: GET /api/v1/rulesets - Configure pricing rules
- **Profiles**: GET /api/v1/profiles - Manage scoring profiles
- **Custom Fields**: GET /api/v1/custom-fields - Manage dynamic fields

