---
title: "Deal Brain Export Format v1.0.0 Reference"
description: "Comprehensive reference for the Deal Brain export format, including schema details, field specifications, validation rules, and migration guidance for future versions."
audience: [developers, ai-agents, users]
tags: [export, import, schema, json, format, specifications, data-structure]
created: 2025-11-19
updated: 2025-11-19
category: "api-documentation"
status: published
related:
  - /docs/api/export-import-api.md
  - /docs/schemas/deal-brain-export-schema-v1.0.0.json
  - /docs/guides/export-import-user-guide.md
---

# Deal Brain Export Format v1.0.0 Reference

## Overview

The Deal Brain Export Format v1.0.0 is a portable JSON schema for exporting and importing listings and collections. The format is **LOCKED** - v1.0.0 cannot have breaking changes. Future versions (v1.1+) will maintain backward compatibility.

**Key Features:**
- Portable JSON format for data exchange
- Complete preservation of all listing and collection metadata
- Support for performance metrics and valuation data
- Custom fields and extended metadata
- Duplicate detection on import
- Two export types: `deal` (single listing) and `collection` (multiple listings)

---

## Document Structure

Every export document has this top-level structure:

```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-19T12:00:00.000Z",
    "exported_by": "550e8400-e29b-41d4-a716-446655440000",
    "type": "deal" | "collection"
  },
  "data": {
    // Export data (DealData or CollectionData)
  }
}
```

### Export Metadata

**Field**: `deal_brain_export` (Required)

The metadata wrapper for every export document.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version, must be exactly `"1.0.0"` |
| `exported_at` | string (ISO 8601) | Yes | Timestamp when export was created (UTC) |
| `exported_by` | string (UUID) | No | User ID who created the export |
| `type` | string | Yes | Export type: `"deal"` or `"collection"` |

**Validation Rules:**
- `version` must be exactly `"1.0.0"`
- `exported_at` must be valid ISO 8601 datetime format
- `exported_by` if present, must be valid UUID format
- `type` must be one of: `"deal"`, `"collection"`

**Example:**
```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-19T12:34:56.789Z",
    "exported_by": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "type": "deal"
  }
}
```

---

## Deal Data Export

### Structure

For single listing exports (`type: "deal"`), the `data` field contains a `DealData` object:

```json
{
  "deal_brain_export": { /* ... */ },
  "data": {
    "listing": { /* ListingExport */ },
    "valuation": { /* ValuationExport (optional) */ },
    "performance": { /* PerformanceExport (optional) */ },
    "metadata": { /* MetadataExport (optional) */ }
  }
}
```

### Listing

**Field**: `listing` (Required)

Core listing information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Original listing ID (reference only, not unique in target) |
| `title` | string | Yes | Listing title (1-255 chars) |
| `listing_url` | string | No | Original listing URL |
| `other_urls` | array | No | Additional URLs with optional labels |
| `seller` | string | No | Seller name (max 128 chars) |
| `price_usd` | number | Yes | Price in USD (≥ 0) |
| `price_date` | string (ISO 8601) | No | Date price was recorded |
| `condition` | string | Yes | Item condition: `"new"`, `"like_new"`, `"good"`, `"fair"`, `"poor"` |
| `status` | string | Yes | Listing status: `"active"`, `"sold"`, `"removed"`, `"draft"` |
| `device_model` | string | No | Device model name (max 255 chars) |
| `notes` | string | No | Additional notes about listing |
| `custom_fields` | object | No | Custom field values (key-value pairs) |
| `created_at` | string (ISO 8601) | Yes | Listing creation timestamp |
| `updated_at` | string (ISO 8601) | Yes | Listing last update timestamp |

**Validation Rules:**
- `title` must be 1-255 characters
- `price_usd` must be ≥ 0
- `condition` must be one of the enumerated values
- `status` must be one of the enumerated values
- Timestamps must be valid ISO 8601 format

**Example:**
```json
{
  "listing": {
    "id": 42,
    "title": "Intel Core i7 Gaming PC",
    "listing_url": "https://ebay.com/item/123456",
    "other_urls": [
      {
        "url": "https://marketplace.com/item/xyz",
        "label": "Marketplace listing"
      }
    ],
    "seller": "TechDeals Co.",
    "price_usd": 799.99,
    "price_date": "2025-11-15T10:30:00Z",
    "condition": "like_new",
    "status": "active",
    "device_model": "NZXT H510",
    "notes": "Excellent condition, tested working",
    "custom_fields": {
      "shipping_cost": "$15",
      "warranty": "1 year",
      "location": "California"
    },
    "created_at": "2025-11-15T10:30:00Z",
    "updated_at": "2025-11-18T14:20:00Z"
  }
}
```

### Valuation (Optional)

**Field**: `valuation` (Optional)

Pricing and valuation analysis applied to the listing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `base_price_usd` | number | Yes | Original listing price |
| `adjusted_price_usd` | number | No | Price after applying valuation rules |
| `valuation_breakdown` | object | No | Detailed breakdown of applied rules |
| `ruleset_name` | string | No | Name of valuation ruleset used |

**Validation Rules:**
- `base_price_usd` must be ≥ 0
- `adjusted_price_usd` if present, must be ≥ 0
- `valuation_breakdown` is free-form object for detailed analysis

**Example:**
```json
{
  "valuation": {
    "base_price_usd": 799.99,
    "adjusted_price_usd": 749.99,
    "ruleset_name": "Standard Valuation v2",
    "valuation_breakdown": {
      "cpu_adjustment": "-$30 (i7 discount)",
      "condition_adjustment": "+$20 (like new condition)",
      "age_adjustment": "-$40 (released 2022)",
      "market_adjustment": "+$0 (market neutral)"
    }
  }
}
```

### Performance (Optional)

**Field**: `performance` (Optional)

Hardware specifications and performance metrics.

```json
{
  "performance": {
    "cpu": { /* CPUExport */ },
    "gpu": { /* GPUExport */ },
    "ram": { /* RAMExport */ },
    "storage_primary": { /* StorageExport */ },
    "storage_secondary": { /* StorageExport */ },
    "metrics": { /* PerformanceMetricsExport */ },
    "ports": { /* PortsExport */ },
    "components": [ /* ComponentExport[] */ ]
  }
}
```

#### CPU

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | CPU name/model (e.g., "Intel Core i7-12700K") |
| `manufacturer` | string | Yes | Manufacturer: `"Intel"`, `"AMD"` |
| `cores` | integer | No | Core count |
| `threads` | integer | No | Thread count |
| `tdp_w` | integer | No | Thermal Design Power in watts |
| `igpu_model` | string | No | Integrated GPU model if available |
| `cpu_mark_multi` | integer | No | Multi-thread CPU Mark score |
| `cpu_mark_single` | integer | No | Single-thread CPU Mark score |
| `igpu_mark` | integer | No | Integrated GPU Mark score |
| `release_year` | integer | No | Release year |

**Example:**
```json
{
  "cpu": {
    "name": "Intel Core i7-12700K",
    "manufacturer": "Intel",
    "cores": 12,
    "threads": 20,
    "tdp_w": 125,
    "igpu_model": "Intel UHD 770",
    "cpu_mark_multi": 41234,
    "cpu_mark_single": 2598,
    "igpu_mark": 2500,
    "release_year": 2021
  }
}
```

#### GPU (Optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | GPU name/model |
| `manufacturer` | string | Yes | Manufacturer: `"NVIDIA"`, `"AMD"`, `"Intel"` |
| `gpu_mark` | integer | No | GPU Mark score |
| `metal_score` | integer | No | Metal benchmark score |

#### RAM (Optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_gb` | integer | Yes | Total RAM capacity in GB |
| `ddr_generation` | string | No | Generation: `"DDR3"`, `"DDR4"`, `"DDR5"` |
| `speed_mhz` | integer | No | Speed in MHz |
| `module_count` | integer | No | Number of RAM modules |
| `capacity_per_module_gb` | integer | No | Capacity per module in GB |
| `notes` | string | No | Additional notes about RAM |

**Example:**
```json
{
  "ram": {
    "total_gb": 32,
    "ddr_generation": "DDR4",
    "speed_mhz": 3200,
    "module_count": 2,
    "capacity_per_module_gb": 16,
    "notes": "Corsair Vengeance RGB Pro"
  }
}
```

#### Storage (Optional)

Two storage devices supported: `storage_primary` and `storage_secondary`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capacity_gb` | integer | Yes | Storage capacity in GB |
| `medium` | string | No | Storage type: `"ssd"`, `"hdd"`, `"nvme"` |
| `interface` | string | No | Interface: `"SATA"`, `"NVMe"`, `"M.2"` |
| `form_factor` | string | No | Form factor: `"2.5"`, `"3.5"`, `"M.2"` |
| `performance_tier` | string | No | Performance tier: `"consumer"`, `"professional"` |

**Example:**
```json
{
  "storage_primary": {
    "capacity_gb": 1000,
    "medium": "ssd",
    "interface": "NVMe",
    "form_factor": "M.2",
    "performance_tier": "consumer"
  }
}
```

#### Performance Metrics (Optional)

Price-to-performance calculations based on CPU Mark scores.

| Field | Type | Description |
|-------|------|-------------|
| `dollar_per_cpu_mark_single` | number | Base price / single-thread mark |
| `dollar_per_cpu_mark_single_adjusted` | number | Adjusted price / single-thread mark |
| `dollar_per_cpu_mark_multi` | number | Base price / multi-thread mark |
| `dollar_per_cpu_mark_multi_adjusted` | number | Adjusted price / multi-thread mark |
| `score_cpu_multi` | number | Multi-threaded performance score (0-100) |
| `score_cpu_single` | number | Single-threaded performance score (0-100) |
| `score_gpu` | number | GPU performance score (0-100) |
| `score_composite` | number | Composite performance score (0-100) |
| `perf_per_watt` | number | Performance per watt efficiency metric |

**Example:**
```json
{
  "metrics": {
    "dollar_per_cpu_mark_single": 0.31,
    "dollar_per_cpu_mark_single_adjusted": 0.29,
    "dollar_per_cpu_mark_multi": 0.019,
    "dollar_per_cpu_mark_multi_adjusted": 0.018,
    "score_cpu_multi": 85,
    "score_cpu_single": 78,
    "score_gpu": 0,
    "score_composite": 82,
    "perf_per_watt": 0.45
  }
}
```

#### Ports (Optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile_name` | string | No | Name of ports profile |
| `ports` | array | No | Array of port specifications |

Port specification:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Port type: `"usb_a"`, `"usb_c"`, `"hdmi"`, `"displayport"`, `"thunderbolt"`, `"ethernet"`, etc. |
| `count` | integer | Yes | Number of ports of this type (≥ 1) |
| `spec_notes` | string | No | Additional port specifications |

**Example:**
```json
{
  "ports": {
    "profile_name": "Gaming Build Ports",
    "ports": [
      { "type": "usb_a", "count": 4, "spec_notes": "3.0 speed" },
      { "type": "usb_c", "count": 2, "spec_notes": "Thunderbolt 4" },
      { "type": "hdmi", "count": 1, "spec_notes": "2.1 version" },
      { "type": "displayport", "count": 1, "spec_notes": "1.4 version" },
      { "type": "ethernet", "count": 1, "spec_notes": "Gigabit" }
    ]
  }
}
```

#### Components (Optional)

Additional hardware components with adjustment values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component_type` | string | Yes | Type: `"psu"`, `"cooler"`, `"case"`, `"motherboard"`, etc. |
| `name` | string | No | Component name/model |
| `quantity` | integer | No | Quantity (default: 1, must be ≥ 1) |
| `metadata` | object | No | Free-form component metadata |
| `adjustment_value_usd` | number | No | Price adjustment value in USD |

**Example:**
```json
{
  "components": [
    {
      "component_type": "psu",
      "name": "EVGA SuperNOVA 850W Gold",
      "quantity": 1,
      "adjustment_value_usd": 15,
      "metadata": {
        "efficiency_rating": "Gold",
        "warranty_years": 10
      }
    }
  ]
}
```

### Metadata (Optional)

**Field**: `metadata` (Optional)

Product metadata and identifying information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturer` | string | No | Manufacturer name (max 64 chars) |
| `series` | string | No | Product series (max 128 chars) |
| `model_number` | string | No | Model number (max 128 chars) |
| `form_factor` | string | No | Form factor (max 32 chars) |

**Example:**
```json
{
  "metadata": {
    "manufacturer": "NZXT",
    "series": "H5 Flow",
    "model_number": "CA-H51F-01",
    "form_factor": "ATX"
  }
}
```

---

## Collection Data Export

### Structure

For collection exports (`type: "collection"`), the `data` field contains a `CollectionData` object:

```json
{
  "deal_brain_export": { /* ... */ },
  "data": {
    "collection": { /* CollectionExport */ },
    "items": [ /* CollectionItemExport[] */ ]
  }
}
```

### Collection

**Field**: `collection` (Required)

Collection metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Original collection ID (reference only) |
| `name` | string | Yes | Collection name (1-100 chars) |
| `description` | string | No | Collection description (max 1000 chars) |
| `visibility` | string | Yes | Visibility: `"private"`, `"unlisted"`, `"public"` |
| `created_at` | string (ISO 8601) | Yes | Collection creation timestamp |
| `updated_at` | string (ISO 8601) | Yes | Last update timestamp |

**Example:**
```json
{
  "collection": {
    "id": 5,
    "name": "Best Gaming Deals - Q4 2025",
    "description": "Curated collection of excellent gaming PC deals",
    "visibility": "public",
    "created_at": "2025-11-01T10:00:00Z",
    "updated_at": "2025-11-19T12:00:00Z"
  }
}
```

### Collection Items

**Field**: `items` (Required, can be empty)

Array of items in the collection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `listing` | object | Yes | DealData for the listing |
| `status` | string | Yes | Item status: `"active"`, `"archived"`, `"removed"` |
| `notes` | string | No | Item-specific notes (max 500 chars) |
| `position` | integer | No | Position in collection (for ordering) |
| `added_at` | string (ISO 8601) | Yes | Timestamp when item was added |

**Example:**
```json
{
  "items": [
    {
      "listing": {
        "listing": { /* ListingExport */ },
        "valuation": { /* ValuationExport */ },
        "performance": { /* PerformanceExport */ }
      },
      "status": "active",
      "notes": "Excellent price for specs",
      "position": 1,
      "added_at": "2025-11-15T10:30:00Z"
    }
  ]
}
```

---

## Complete Examples

### Deal Export Example

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
      "listing_url": "https://ebay.com/item/123456",
      "seller": "TechDeals Co.",
      "price_usd": 799.99,
      "price_date": "2025-11-15T10:30:00Z",
      "condition": "like_new",
      "status": "active",
      "device_model": "NZXT H510",
      "notes": "Tested working, excellent condition",
      "custom_fields": { "warranty": "1 year" },
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-18T14:20:00Z"
    },
    "valuation": {
      "base_price_usd": 799.99,
      "adjusted_price_usd": 749.99,
      "ruleset_name": "Standard Valuation v2",
      "valuation_breakdown": {
        "cpu_adjustment": "-$30",
        "condition_adjustment": "+$20"
      }
    },
    "performance": {
      "cpu": {
        "name": "Intel Core i7-12700K",
        "manufacturer": "Intel",
        "cores": 12,
        "threads": 20,
        "cpu_mark_multi": 41234,
        "cpu_mark_single": 2598
      },
      "ram": {
        "total_gb": 32,
        "ddr_generation": "DDR4",
        "speed_mhz": 3200
      },
      "storage_primary": {
        "capacity_gb": 1000,
        "medium": "ssd",
        "interface": "NVMe"
      },
      "metrics": {
        "dollar_per_cpu_mark_multi": 0.019,
        "dollar_per_cpu_mark_single": 0.31,
        "score_cpu_multi": 85,
        "score_cpu_single": 78,
        "score_composite": 82
      }
    },
    "metadata": {
      "manufacturer": "NZXT",
      "series": "H5 Flow",
      "form_factor": "ATX"
    }
  }
}
```

### Collection Export Example

See `/docs/schemas/collection-export-example.json` for a complete collection export with multiple items.

---

## Validation Rules

### Required Fields

These fields are always required in the export:
- `deal_brain_export` (wrapper)
- `deal_brain_export.version` (must be "1.0.0")
- `deal_brain_export.exported_at` (valid ISO 8601)
- `deal_brain_export.type` (must be "deal" or "collection")
- `data` (structure depends on type)

For deal exports:
- `data.listing` (listing data)
- `listing.id`, `listing.title`, `listing.price_usd`, `listing.condition`, `listing.status`
- `listing.created_at`, `listing.updated_at`

For collection exports:
- `data.collection` (collection metadata)
- `collection.id`, `collection.name`, `collection.visibility`
- `collection.created_at`, `collection.updated_at`
- `data.items` (can be empty array)

### Optional Fields

All other fields are optional. Missing optional fields should be omitted (not set to `null`) for cleaner exports.

### Type Constraints

- Strings with length constraints must respect min/max length
- Numeric fields must be valid numbers
- Enums must use exact string values (case-sensitive)
- ISO 8601 timestamps must be valid datetime format
- UUID fields must be valid UUID format v4

### Null Handling

- Optional fields should be omitted rather than set to `null`
- Arrays should be omitted or provided as empty array `[]`
- Objects should be omitted or provided with required fields

---

## Future Versions & Migration

### v1.0.0 Lock

The v1.0.0 schema is **LOCKED**. Breaking changes are not allowed. This ensures:
- Existing exports remain valid indefinitely
- Tools reading v1.0.0 exports will always work
- Backward compatibility is guaranteed

### Future Version Strategy

When v1.1.0 or later is released:

1. **New fields** can be added to existing objects
2. **New optional objects** can be added
3. **Existing fields** cannot be removed or changed
4. **Existing enum values** cannot change meaning
5. **Version validation** is strict - tools must accept both 1.0.0 and newer compatible versions

### Migration Path

If you're using older export formats:

**v0.9.0 → v1.0.0 Migration:**
- Not yet implemented (planned for v1.1.0 release)
- Will handle schema changes from earlier versions
- Migration guide will be provided with v1.1.0 release

To use old exports with current system:
1. Re-export listings to v1.0.0 format
2. Or contact support for migration assistance

---

## JSON Schema File

The complete JSON Schema definition is available at:

**File**: `/docs/schemas/deal-brain-export-schema-v1.0.0.json`

**Usage:**
```javascript
// Validate export file against schema
const schema = require('./deal-brain-export-schema-v1.0.0.json');
const Ajv = require('ajv');
const ajv = new Ajv();
const validate = ajv.compile(schema);

const valid = validate(exportData);
if (!valid) {
  console.error('Validation errors:', validate.errors);
}
```

---

## Common Questions

**Q: Can I modify an export file and re-import it?**
A: Yes, you can modify listings and custom fields, but avoid modifying performance metrics and valuation data to prevent inconsistencies.

**Q: What happens if I import an export with old IDs?**
A: The imported listing gets a new ID in the target system. The original ID is preserved in the export for reference but doesn't affect import.

**Q: Can I import an export multiple times?**
A: Yes, but duplicate detection will alert you. You can choose to create a new listing or update an existing one.

**Q: Is there a file size limit for exports?**
A: No hard limit, but large collections (1000+ items) should be split into smaller exports for better performance.

**Q: Can I export and re-import to backup data?**
A: Yes, but for full system backups, use the database backup feature instead.

---

## Related Documentation

- **API Documentation**: See `/docs/api/export-import-api.md` for endpoint specifications
- **User Guide**: See `/docs/guides/export-import-user-guide.md` for user-facing instructions
- **Developer Guide**: See `/docs/development/export-import-developer-guide.md` for integration details
