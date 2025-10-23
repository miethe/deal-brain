# Data Model & Schema Requirements

**Status:** Draft
**Last Updated:** October 22, 2025

---

## Database Schema Changes

**No schema changes required.** All necessary fields already exist in the database.

**Optional Future Enhancement:**

```sql
-- Audit log table for history tab
CREATE TABLE listing_history (
  id SERIAL PRIMARY KEY,
  listing_id INTEGER REFERENCES listings(id) ON DELETE CASCADE,
  changed_by VARCHAR(255),
  changed_at TIMESTAMP DEFAULT NOW(),
  field_name VARCHAR(100),
  old_value TEXT,
  new_value TEXT,
  change_type VARCHAR(50)
);
```

---

## API Contracts

### Enhanced Listing Detail

**GET `/v1/listings/{id}`**

**Response (200 OK):**

```json
{
  "id": 123,
  "title": "Intel NUC i7-1165G7 16GB 512GB",
  "price_usd": 450.00,
  "adjusted_price_usd": 375.00,
  "thumbnail_url": "https://example.com/image.jpg",
  "seller": "TechDeals",
  "status": "available",
  "condition": "refurbished",
  "manufacturer": "Intel",
  "series": "NUC",
  "model_number": "NUC11PAHi7",
  "form_factor": "mini_pc",
  "cpu": {
    "id": 45,
    "name": "Intel Core i7-1165G7",
    "manufacturer": "Intel",
    "cores": 4,
    "threads": 8,
    "tdp_w": 28,
    "cpu_mark_multi": 10500,
    "cpu_mark_single": 3200,
    "igpu_model": "Intel Iris Xe Graphics",
    "igpu_mark": 1800,
    "release_year": 2020
  },
  "gpu": null,
  "ram_spec": {
    "id": 12,
    "label": "16GB DDR4-3200",
    "ddr_generation": "DDR4",
    "speed_mhz": 3200,
    "module_count": 2,
    "capacity_per_module_gb": 8,
    "total_capacity_gb": 16
  },
  "primary_storage_profile": {
    "id": 8,
    "label": "512GB NVMe SSD",
    "medium": "ssd",
    "interface": "nvme",
    "form_factor": "m.2",
    "capacity_gb": 512,
    "performance_tier": "high"
  },
  "ports_profile": {
    "id": 5,
    "name": "NUC Standard Ports",
    "ports": [
      {"port_type": "usb-c", "quantity": 2, "version": "3.2"},
      {"port_type": "usb-a", "quantity": 4, "version": "3.0"},
      {"port_type": "hdmi", "quantity": 1, "version": "2.0"},
      {"port_type": "ethernet", "quantity": 1, "version": "gigabit"}
    ]
  },
  "valuation_breakdown": {
    "listing_price": 450.00,
    "adjusted_price": 375.00,
    "total_adjustment": -75.00,
    "matched_rules_count": 12,
    "ruleset": {"id": 1, "name": "Production Rules v2"},
    "adjustments": [
      {
        "rule_id": 10,
        "rule_name": "RAM Deduction - 16GB",
        "rule_description": "Deduct value for RAM capacity",
        "rule_group_id": 2,
        "rule_group_name": "Hardware",
        "adjustment_amount": -50.00,
        "actions": [
          {
            "action_type": "deduct_fixed",
            "metric": "ram_gb",
            "value": -50.00
          }
        ]
      }
    ]
  },
  "attributes": {
    "custom_field_1": "value",
    "warranty_months": 12
  },
  "created_at": "2025-10-15T14:30:00Z",
  "updated_at": "2025-10-20T09:15:00Z"
}
```

### Enhanced Valuation Breakdown

**GET `/v1/listings/{id}/valuation-breakdown`**

**Changes:**

- Add `rule_description`, `rule_group_id`, `rule_group_name` to adjustments
- Ensure all inactive rules included (with zero adjustment amounts)

**Response (200 OK):**

```json
{
  "listing_id": 123,
  "listing_title": "Intel NUC i7-1165G7 16GB 512GB",
  "base_price_usd": 450.00,
  "adjusted_price_usd": 375.00,
  "total_adjustment": -75.00,
  "matched_rules_count": 12,
  "ruleset_id": 1,
  "ruleset_name": "Production Rules v2",
  "adjustments": [
    {
      "rule_id": 10,
      "rule_name": "RAM Deduction - 16GB",
      "rule_description": "Deduct value based on RAM capacity",
      "rule_group_id": 2,
      "rule_group_name": "Hardware",
      "adjustment_amount": -50.00,
      "actions": [
        {
          "action_type": "deduct_fixed",
          "metric": "ram_gb",
          "value": -25.00
        },
        {
          "action_type": "multiply",
          "metric": "condition_multiplier",
          "value": -25.00,
          "details": {"multiplier": 0.95}
        }
      ]
    }
  ],
  "legacy_lines": []
}
```

---

## Frontend TypeScript Interfaces

### Enhanced Listing Detail

```typescript
interface ListingDetail extends ListingRecord {
  cpu: CpuRecord | null;
  gpu: GpuRecord | null;
  ram_spec: RamSpecRecord | null;
  primary_storage_profile: StorageProfileRecord | null;
  secondary_storage_profile: StorageProfileRecord | null;
  ports_profile: PortsProfileRecord | null;
  valuation_breakdown: ValuationBreakdown | null;
}
```

### Enhanced Valuation Adjustment

```typescript
interface ValuationAdjustment {
  rule_id?: number | null;
  rule_name: string;
  rule_description?: string | null;      // NEW
  rule_group_id?: number | null;         // NEW
  rule_group_name?: string | null;       // NEW
  adjustment_amount: number;
  actions: ValuationAdjustmentAction[];
}
```

### Entity Link Props

```typescript
interface EntityLinkProps {
  type: 'cpu' | 'gpu' | 'ram_spec' | 'storage_profile' | 'ports_profile';
  id: number;
  name: string;
  showTooltip?: boolean;
  className?: string;
}
```

### Summary Card Props

```typescript
interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'success' | 'warning' | 'error';
}
```

### CPU Record

```typescript
interface CpuRecord {
  id: number;
  name: string;
  manufacturer: string;
  cores: number;
  threads: number;
  tdp_w: number;
  cpu_mark_multi: number;
  cpu_mark_single: number;
  igpu_model?: string;
  igpu_mark?: number;
  release_year: number;
}
```

### GPU Record

```typescript
interface GpuRecord {
  id: number;
  name: string;
  manufacturer: string;
  vram_gb: number;
  tdp_w: number;
  performance_tier?: string;
  release_year: number;
}
```

### RAM Spec Record

```typescript
interface RamSpecRecord {
  id: number;
  label: string;
  ddr_generation: string;       // e.g., "DDR4", "DDR5"
  speed_mhz: number;
  module_count: number;
  capacity_per_module_gb: number;
  total_capacity_gb: number;
}
```

### Storage Profile Record

```typescript
interface StorageProfileRecord {
  id: number;
  label: string;
  medium: 'ssd' | 'hdd' | 'nvme';
  interface: string;            // e.g., "SATA", "NVMe", "M.2"
  form_factor: string;          // e.g., "2.5\"", "M.2", "3.5\""
  capacity_gb: number;
  performance_tier: 'low' | 'medium' | 'high';
}
```

### Ports Profile Record

```typescript
interface PortsProfileRecord {
  id: number;
  name: string;
  ports: PortRecord[];
}

interface PortRecord {
  port_type: string;            // e.g., "usb-c", "usb-a", "hdmi"
  quantity: number;
  version?: string;             // e.g., "3.0", "3.2", "2.0"
}
```

---

## React Query Cache Keys

```typescript
// Listings table data
['listings', 'records', { page, filters }]

// Total listings count
['listings', 'count', { filters }]

// Single listing (modal context)
['listings', 'single', listingId]

// Listing detail page (server prefetch)
['listing', 'detail', listingId]

// Valuation breakdown
['listing', 'valuation', listingId]

// Entity tooltips
['cpu', cpuId]
['gpu', gpuId]
['ram-spec', ramSpecId]
['storage-profile', storageProfileId]

// Rulesets
['rulesets', 'active']
```

---

## URL State

```typescript
// Tab selection on detail page
/listings/[id]?tab=valuation

// Highlight new listing in table (optional)
/listings?highlight=123
```

---

## Backend Implementation Notes

### Service Layer Enhancement

```python
# apps/api/dealbrain_api/services/listings.py

async def get_listing_detail_with_relationships(
    session: AsyncSession,
    listing_id: int
) -> Listing:
    """
    Fetch listing with all relationships eager-loaded.
    """
    stmt = (
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.cpu),
            selectinload(Listing.gpu),
            selectinload(Listing.ram_spec),
            selectinload(Listing.primary_storage_profile),
            selectinload(Listing.secondary_storage_profile),
            selectinload(Listing.ports_profile).selectinload(PortsProfile.ports)
        )
    )
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
```

### API Endpoint Enhancement

```python
# apps/api/dealbrain_api/api/listings.py

@router.get("/{id}", response_model=ListingDetailSchema)
async def get_listing_detail(id: int, session: AsyncSession = Depends(get_db_session)):
    """Get complete listing detail with all relationships."""
    listing = await listings_service.get_listing_detail_with_relationships(session, id)
    return listing
```

---

## Migration Path

1. **Phase 1-2:** No database changes needed (existing fields used)
2. **Phase 3:** Backend API enhancement to include rule metadata
3. **Phase 4-6:** Frontend components utilize enhanced API
4. **Future:** Optional audit logging table for history tab

---

## Related Documentation

- **[Technical Requirements](./technical.md)** - Component architecture, state management
- **[Enhanced Breakdown Requirement](./enhanced-breakdown.md)** - Uses rule metadata
- **[Detail Page Requirement](./detail-page.md)** - Uses complete listing schema
