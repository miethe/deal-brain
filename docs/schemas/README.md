# Deal Brain Export Schema v1.0.0

This directory contains the JSON Schema definition and documentation for the Deal Brain portable export format.

## Overview

The Deal Brain Export Format is a **LOCKED v1.0.0 schema** for portable interchange of Deal Brain artifacts (listings and collections). This format enables users to:

- Export individual deals with complete valuation, performance, and metadata
- Export entire collections with multiple deals and collection metadata
- Share artifacts across Deal Brain instances
- Archive and backup deal data
- Integrate with external tools and systems

## Schema Files

- **`deal-brain-export-schema-v1.0.0.json`** - JSON Schema (draft-07) definition
- **`examples/sample-deal-export-v1.0.0.json`** - Sample deal export
- **`examples/sample-collection-export-v1.0.0.json`** - Sample collection export

## Version Locking

**IMPORTANT**: The v1.0.0 schema is LOCKED and cannot have breaking changes.

- **Current version**: `1.0.0` (LOCKED)
- **Future versions**: Must be `1.1.x`, `1.2.x`, etc. with full backward compatibility
- **Breaking changes**: Require new major version (e.g., `2.0.0`)

This ensures that exports created with v1.0.0 can be imported by any future 1.x version of Deal Brain.

## Schema Structure

### Top-Level Wrapper

All exports use a common wrapper structure:

```json
{
  "deal_brain_export": {
    "version": "1.0.0",
    "exported_at": "2025-11-19T10:30:00Z",
    "exported_by": "550e8400-e29b-41d4-a716-446655440000",
    "type": "deal" | "collection"
  },
  "data": { ... }
}
```

**Fields:**
- `version` (string, required): Semver version, MUST be `"1.0.0"` for this schema
- `exported_at` (datetime, required): ISO 8601 timestamp when export was created
- `exported_by` (UUID, optional): UUID of user who created the export
- `type` (enum, required): Export type - `"deal"` or `"collection"`

### Deal Export Structure

```json
{
  "deal_brain_export": { ... },
  "data": {
    "listing": { ... },       // Listing details (required)
    "valuation": { ... },     // Valuation breakdown (optional)
    "performance": { ... },   // Performance metrics (optional)
    "metadata": { ... }       // Product metadata (optional)
  }
}
```

**Listing Fields:**
- Basic info: `id`, `title`, `price_usd`, `seller`, `condition`, `status`
- URLs: `listing_url`, `other_urls[]`
- Dates: `price_date`, `created_at`, `updated_at`
- Details: `device_model`, `notes`, `custom_fields{}`

**Valuation Fields:**
- `base_price_usd` (number): Original listing price
- `adjusted_price_usd` (number): Price after applying rules
- `valuation_breakdown` (object): Detailed breakdown of applied rules
- `ruleset_name` (string): Name of ruleset used

**Performance Fields:**
- `cpu` (object): CPU specifications with PassMark scores
- `gpu` (object): GPU specifications
- `ram` (object): RAM configuration (DDR generation, speed, modules)
- `storage_primary` (object): Primary storage details
- `storage_secondary` (object): Secondary storage details
- `metrics` (object): Performance metrics ($/mark ratios, scores)
- `ports` (object): Port configuration
- `components[]` (array): Additional components (WiFi, etc.)

**Metadata Fields:**
- `manufacturer` (string): Device manufacturer (e.g., "Dell")
- `series` (string): Product series (e.g., "OptiPlex")
- `model_number` (string): Model number (e.g., "7050")
- `form_factor` (string): Form factor (e.g., "Micro")

### Collection Export Structure

```json
{
  "deal_brain_export": { ... },
  "data": {
    "collection": {
      "id": 15,
      "name": "Best Budget Builds",
      "description": "...",
      "visibility": "public",
      "created_at": "...",
      "updated_at": "..."
    },
    "items": [
      {
        "listing": { ... },  // Full deal export
        "status": "shortlisted",
        "notes": "Top pick",
        "position": 1,
        "added_at": "..."
      }
    ]
  }
}
```

**Collection Fields:**
- `id` (integer): Original collection ID (reference only)
- `name` (string): Collection name (1-100 chars)
- `description` (string): Optional description (max 1000 chars)
- `visibility` (enum): `"private"`, `"unlisted"`, or `"public"`

**Collection Item Fields:**
- `listing` (object): Full deal export for this item
- `status` (enum): `"undecided"`, `"shortlisted"`, `"rejected"`, or `"bought"`
- `notes` (string): Optional user notes (max 500 chars)
- `position` (integer): Display order position
- `added_at` (datetime): When item was added to collection

## Enumerations

### Condition
- `new` - Brand new, sealed
- `refurb` - Manufacturer refurbished
- `used` - Previously owned

### Listing Status
- `active` - Currently active listing
- `archived` - Archived (no longer available)
- `pending` - Pending review/approval

### Collection Visibility
- `private` - Only visible to owner
- `unlisted` - Accessible via direct link
- `public` - Visible to all users

### Collection Item Status
- `undecided` - No decision made yet
- `shortlisted` - Marked as potential purchase
- `rejected` - Not interested
- `bought` - Already purchased

### RAM Generation
- `ddr3`, `ddr4`, `ddr5` - Standard DDR
- `lpddr4`, `lpddr4x`, `lpddr5`, `lpddr5x` - Low-power DDR
- `hbm2`, `hbm3` - High Bandwidth Memory
- `unknown` - Unknown or unspecified

### Storage Medium
- `nvme` - NVMe SSD
- `sata_ssd` - SATA SSD
- `hdd` - Hard Disk Drive
- `hybrid` - Hybrid drive (SSD + HDD)
- `emmc` - eMMC flash storage
- `ufs` - Universal Flash Storage
- `unknown` - Unknown or unspecified

### Port Types
- `usb_a`, `usb_c` - USB Type-A and Type-C
- `thunderbolt` - Thunderbolt ports
- `hdmi`, `displayport` - Video outputs
- `rj45_1g`, `rj45_2_5g`, `rj45_10g` - Ethernet ports
- `audio` - Audio jacks
- `sdxc` - SD card reader
- `pcie_x16`, `pcie_x8` - PCIe slots
- `m2_slot` - M.2 expansion slots
- `sata_bay` - SATA drive bays
- `other` - Other port types

### Component Types
- `ram` - RAM modules
- `ssd` - SSD storage
- `hdd` - HDD storage
- `os_license` - Operating system license
- `wifi` - WiFi adapter
- `gpu` - Graphics card
- `misc` - Miscellaneous components

## Usage Examples

### Exporting a Deal (Python)

```python
from dealbrain_api.schemas.export_import import (
    PortableDealExport,
    ExportMetadata,
    DealDataExport,
    ListingExport,
    ValuationExport,
)
from datetime import datetime

export = PortableDealExport(
    deal_brain_export=ExportMetadata(
        version="1.0.0",
        exported_at=datetime.now(),
        type="deal"
    ),
    data=DealDataExport(
        listing=ListingExport(...),
        valuation=ValuationExport(...)
    )
)

# Serialize to JSON
json_str = export.model_dump_json(indent=2)
```

### Importing a Deal (Python)

```python
from dealbrain_api.schemas.export_import import PortableDealExport
import json

# Load from file
with open("export.json") as f:
    data = json.load(f)

# Validate and parse
export = PortableDealExport(**data)

# Access data
listing = export.data.listing
valuation = export.data.valuation
```

### Generic Export Parsing

```python
from dealbrain_api.schemas.export_import import PortableExport

# Load unknown export type
with open("export.json") as f:
    data = json.load(f)

export = PortableExport(**data)

# Check type and handle accordingly
if export.deal_brain_export.type == "deal":
    # Handle deal export
    listing = export.data.listing
elif export.deal_brain_export.type == "collection":
    # Handle collection export
    collection = export.data.collection
    items = export.data.items
```

## Validation

The schema includes comprehensive Pydantic validators:

- **Version validation**: Ensures version is exactly "1.0.0"
- **Type validation**: Ensures export type matches wrapper
- **Field constraints**: Min/max lengths, value ranges
- **Format validation**: UUIDs, datetimes, URLs
- **Enum validation**: All enum fields validated against allowed values

## Implementation Notes

### Pydantic Models

Pydantic models are defined in `/home/user/deal-brain/apps/api/dealbrain_api/schemas/export_import.py`:

- **Top-level**: `PortableDealExport`, `PortableCollectionExport`, `PortableExport`
- **Metadata**: `ExportMetadata`
- **Deal**: `DealDataExport`, `ListingExport`, `ValuationExport`, `PerformanceExport`, `MetadataExport`
- **Collection**: `CollectionDataExport`, `CollectionExport`, `CollectionItemExport`
- **Components**: `CPUExport`, `GPUExport`, `RAMExport`, `StorageExport`, `PortExport`, etc.

### Backward Compatibility

Future versions (v1.1.x, v1.2.x, etc.) MUST:

1. Add only optional fields (never required)
2. Never remove existing fields
3. Never change field types or semantics
4. Never change enum values (only add new ones)
5. Accept v1.0.0 exports unchanged

### Forward Compatibility

v1.0.0 implementations SHOULD:

1. Ignore unknown fields in newer versions
2. Use default values for missing optional fields
3. Handle additional enum values gracefully
4. Preserve unknown data when re-exporting

## Testing

Test suite located at `/home/user/deal-brain/tests/test_export_import_schemas.py`:

- Component schema validation
- Deal export validation
- Collection export validation
- Sample file validation
- Edge cases and error handling
- Backward/forward compatibility

Run tests:
```bash
poetry run pytest tests/test_export_import_schemas.py -v
```

## References

- **JSON Schema Specification**: https://json-schema.org/specification.html
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Semantic Versioning**: https://semver.org/

## Support

For questions or issues with the export schema:

1. Check the sample exports in `examples/`
2. Review the JSON Schema definition
3. Run the test suite for validation examples
4. Consult the Pydantic model documentation

## Changelog

### v1.0.0 (2025-11-19)

Initial release of the Deal Brain Export Format.

**Features:**
- Deal export with complete listing, valuation, performance, and metadata
- Collection export with multiple items
- Comprehensive validation via Pydantic models
- Sample exports for reference
- Full test coverage

**Schema locked**: No breaking changes allowed in 1.x versions.
