# Product Requirements Document: Performance Metrics & Data Enrichment

**Date:** October 5, 2025
**Version:** 1.0
**Status:** Draft

---

## Executive Summary

This PRD outlines enhancements to Deal Brain's performance metrics system, CPU/Listing data model, and valuation methodology. The changes introduce dual CPU Mark metrics (single-thread and multi-thread), adjusted performance calculations, comprehensive CPU data enrichment, and enhanced listing metadata. These improvements provide users with more accurate price-to-performance analysis and richer product intelligence.

---

## Problem Statement

### Current Limitations

1. **Incomplete Performance Metrics**
   - Only one CPU Mark metric exists (`dollar_per_cpu_mark`)
   - No distinction between single-thread and multi-thread performance
   - Missing adjusted performance calculations that account for valuation deductions

2. **Limited CPU Data**
   - CPU model lacks critical PassMark benchmark fields (single-thread, multi-thread, iGPU scores)
   - Missing thermal and release metadata (TDP, release year)
   - No integrated graphics information

3. **Insufficient Listing Metadata**
   - Missing manufacturer, series, model number fields
   - No form factor classification (Desktop, Laptop, Server)
   - Ports data exists but lacks structured entry/display

4. **Valuation Clarity Gap**
   - Single "adjusted price" doesn't distinguish between base and component-adjusted valuations
   - Users cannot easily compare raw vs. component-adjusted performance metrics

### User Impact

- **PC Enthusiasts** struggle to compare single-thread vs multi-thread value for specific workloads
- **Deal Hunters** cannot accurately assess CPU performance value after component deductions
- **Power Users** lack thermal and timing data to evaluate efficiency and generational positioning
- **Product Managers** miss manufacturer/model context for inventory categorization

---

## Goals & Success Criteria

### Primary Goals

1. **Enhanced Performance Analysis**
   - Provide dual CPU Mark metrics (single/multi-thread) for workload-specific comparisons
   - Introduce adjusted performance calculations that reflect actual CPU value after component deductions

2. **Comprehensive CPU Data**
   - Enrich CPU model with PassMark benchmarks (single, multi, iGPU)
   - Add thermal and release metadata for efficiency analysis

3. **Improved Listing Intelligence**
   - Capture manufacturer, series, model, form factor metadata
   - Enable structured ports data entry and display

4. **Valuation Transparency**
   - Distinguish between base listing price and component-adjusted valuation
   - Show both raw and adjusted performance metrics side-by-side

### Success Metrics

- **Data Completeness:** 95%+ of listings have manufacturer, series, model populated within 30 days
- **User Adoption:** 80%+ of users utilize dual CPU Mark metrics for filtering/sorting
- **Performance Accuracy:** Adjusted $/CPU Mark calculations reflect valuation deductions with <1% variance
- **Form Factor Coverage:** All major categories (Desktop, Laptop, Server, Mini-PC, SFF) represented

---

## Requirements

### 1. Dual CPU Mark Performance Metrics

#### 1.1 Listing Fields

**New Calculated Fields:**

| Field Name | Data Type | Calculation | Display Format |
|-----------|-----------|-------------|----------------|
| `dollar_per_cpu_mark_single` | Float | `price_usd / cpu.cpu_mark_single` | `$0.XX` |
| `dollar_per_cpu_mark_single_adjusted` | Float | `adjusted_price_usd / cpu.cpu_mark_single` | `$0.XX` (green if < raw) |
| `dollar_per_cpu_mark_multi` | Float | `price_usd / cpu.cpu_mark_multi` | `$0.XX` |
| `dollar_per_cpu_mark_multi_adjusted` | Float | `adjusted_price_usd / cpu.cpu_mark_multi` | `$0.XX` (green if < raw) |

**Display Requirements:**
- Each metric shows **two values** in a compact layout:
  - **Top value:** Raw calculation (listing price / CPU Mark)
  - **Bottom value (smaller, green if lower):** Adjusted calculation (adjusted price / CPU Mark)
  - Example: `$0.15` / `$0.12` (20% improvement indicator)

**Behavior:**
- Auto-calculate on listing save/update
- Recalculate when valuation rules change adjusted price
- Handle null CPU gracefully (display "—")

#### 1.2 Listings Table Integration

**Column Configuration:**
- Replace existing "$/CPU Mark" column with two columns:
  - **$/CPU Mark (Single)** — Single-thread performance value
  - **$/CPU Mark (Multi)** — Multi-thread performance value
- Each column displays raw/adjusted values as specified above
- Sortable by either raw or adjusted value (default: adjusted)
- Filterable with range inputs (min/max)
- Tooltip: "Lower is better. Adjusted value accounts for RAM/storage deductions."

**Column Metadata:**
```typescript
{
  id: 'dollar_per_cpu_mark_single',
  header: '$/CPU Mark (Single)',
  meta: {
    tooltip: 'Single-thread price efficiency. Lower = better value.',
    filterType: 'number',
    minWidth: 160,
  }
}
```

### 2. CPU Data Enrichment

#### 2.1 New CPU Model Fields

**PassMark Benchmarks:**
- `cpu_mark_single` (Integer, nullable) — PassMark Single-Thread Rating
- `cpu_mark_multi` (Integer, nullable) — PassMark Multi-Thread Rating (already exists)
- `igpu_mark` (Integer, nullable) — PassMark iGPU G3D Mark (already exists)

**Thermal & Timing:**
- `tdp_w` (Integer, nullable) — Thermal Design Power in Watts (already exists)
- `release_year` (Integer, nullable) — CPU release year (already exists)

**Integrated Graphics:**
- `igpu_model` (String(255), nullable) — iGPU model name (already exists)
- `has_igpu` (Boolean, computed) — Derived from `igpu_model IS NOT NULL`

**Migration Notes:**
- Most fields already exist in CPU model (verified from context)
- Only missing field is `has_igpu` (computed/derived, no migration needed)
- Seed script should populate PassMark data from existing sources

#### 2.2 CPU Auto-Population

**Data Flow:**
1. User selects CPU from dropdown in Listing form
2. Frontend fetches CPU details via existing `/v1/catalog/cpus/{id}` endpoint
3. Auto-populate derived fields:
   - `dollar_per_cpu_mark_single` (calculated)
   - `dollar_per_cpu_mark_multi` (calculated)
   - Display-only: TDP, release year, iGPU status

**UI Behavior:**
- CPU selection triggers immediate calculation
- Show "Calculating..." state during API call
- Display benchmark scores in read-only fields below CPU selector
- Example layout:
  ```
  CPU: [Intel Core i7-12700K ▼]
  ─────────────────────────────────
  Single-Thread: 3,985   TDP: 125W
  Multi-Thread:  35,864  Year: 2021
  iGPU: Intel UHD 770 (G3D: 1,850)
  ```

### 3. Listing Metadata Enhancements

#### 3.1 New Listing Fields

**Product Identification:**

| Field Name | Type | Options/Format | Required |
|-----------|------|----------------|----------|
| `manufacturer` | String(64) | Dropdown (Dell, HP, Lenovo, Apple, Custom, etc.) | No |
| `series` | String(128) | Text input | No |
| `model_number` | String(128) | Text input | No |
| `form_factor` | Enum | Desktop, Laptop, Server, Mini-PC, SFF, AIO, Other | No |

**Dropdown Options (Manufacturer):**
- Dell, HP, Lenovo, Apple, ASUS, Acer, MSI, Custom Build, Boutique Builder, Other

**Form Factor Options:**
- Desktop (Full Tower / Mid Tower)
- Laptop (Notebook / Ultrabook)
- Server (Rack / Tower)
- Mini-PC (NUC / SFF)
- All-in-One (AIO)
- Other

#### 3.2 Ports Data Structure

**Current State:**
- `ports_profile_id` links to `PortsProfile` table
- `PortsProfile` has `ports` relationship to `Port` table
- Port model: `port_type`, `quantity`, `port_profile_id`

**Enhancement Requirements:**
- **Global Fields UI:** Add "Ports" field management
- **Field Type:** Multi-value structured field
- **Input Component:** Port builder with type + quantity pairs
  - Port Type: Dropdown (USB-A, USB-C, HDMI, DisplayPort, Ethernet, Thunderbolt, Audio, etc.)
  - Quantity: Number input (1-16)
  - Add/Remove buttons for multiple entries

**Display Format (Listings Table):**
- Compact badge list: `3× USB-A  2× HDMI  1× Ethernet`
- Expandable popover for full details
- Filterable by port type (multi-select)

**Data Storage:**
- Reuse existing `PortsProfile` + `Port` tables
- Create default profile per listing if inline editing
- Link via `ports_profile_id`

### 4. Valuation System Enhancements

#### 4.1 Base vs. Adjusted Valuation

**Definitions:**
- **Base Valuation:** Original listing price (`price_usd`)
- **Adjusted Valuation:** Price after component deductions (`adjusted_price_usd`)

**Display Modes (Toggle in Listings View):**

1. **Base Valuation Mode:**
   - Show `price_usd` in Valuation column
   - Hide component breakdown
   - Performance metrics use raw price

2. **Adjusted Valuation Mode (Default):**
   - Show `adjusted_price_usd` in Valuation column
   - Show delta badge (savings/premium)
   - Performance metrics use adjusted price
   - Breakdown modal available

**Toggle Implementation:**
- Add toggle button above Listings table: `[ Base Price ] [ Adjusted Price ]`
- Persist selection in localStorage
- Update all calculated fields on toggle

#### 4.2 Valuation Display Updates

**Current Valuation Cell:**
```tsx
<ValuationCell
  adjustedPrice={adjustedPrice}
  listPrice={listPrice}
  thresholds={thresholds}
/>
```

**Enhanced Valuation Cell:**
```tsx
<ValuationCell
  basePrice={price_usd}
  adjustedPrice={adjusted_price_usd}
  showMode={valuationMode} // 'base' | 'adjusted'
  thresholds={thresholds}
  onDetailsClick={() => openBreakdown(listing.id)}
/>
```

**Visual Design:**
- **Base Mode:** Show price with neutral gray badge
- **Adjusted Mode:** Show price with color-coded delta (existing behavior)
- Icon indicator: 📊 (base) vs 🔍 (adjusted with breakdown)

---

## User Stories

### Story 1: Workload-Specific Performance Analysis
**As a** PC builder comparing CPUs for different workloads
**I want to** see both single-thread and multi-thread $/CPU Mark metrics
**So that** I can identify the best value for gaming (single) vs. productivity (multi)

**Acceptance Criteria:**
- [ ] Listings table shows "$/CPU Mark (Single)" and "$/CPU Mark (Multi)" columns
- [ ] Each column displays raw and adjusted values
- [ ] Columns are sortable and filterable
- [ ] Tooltip explains single vs. multi-thread use cases

### Story 2: Accurate Value After Deductions
**As a** deal hunter evaluating listings
**I want to** see CPU performance metrics using adjusted prices (after RAM/storage deductions)
**So that** I can accurately assess the value of the CPU itself

**Acceptance Criteria:**
- [ ] Adjusted $/CPU Mark calculations use `adjusted_price_usd`
- [ ] Adjusted values display in green when lower than raw values
- [ ] Percentage improvement shown in tooltip
- [ ] Valuation breakdown modal explains deductions

### Story 3: Comprehensive CPU Intelligence
**As a** power user researching CPUs
**I want to** see PassMark scores, TDP, release year, and iGPU info automatically populated
**So that** I can evaluate thermal efficiency and generational positioning

**Acceptance Criteria:**
- [ ] CPU selection auto-populates PassMark single/multi/iGPU scores
- [ ] TDP and release year displayed in CPU info panel
- [ ] iGPU status shown (model + G3D mark or "None")
- [ ] All data sourced from CPU catalog table

### Story 4: Product Metadata for Inventory Management
**As a** reseller managing inventory
**I want to** capture manufacturer, series, model, and form factor
**So that** I can categorize and filter listings by product lineage

**Acceptance Criteria:**
- [ ] Listing form includes manufacturer dropdown
- [ ] Series and model number text inputs available
- [ ] Form factor dropdown with 7 options
- [ ] All fields optional, filterable in table

### Story 5: Structured Ports Data Entry
**As a** user specifying connectivity options
**I want to** enter ports as type + quantity pairs
**So that** I can accurately represent multiple ports of the same type

**Acceptance Criteria:**
- [ ] Ports builder allows adding multiple entries
- [ ] Each entry has port type dropdown + quantity input
- [ ] Listings table displays compact badge list (e.g., "3× USB-A  2× HDMI")
- [ ] Filterable by port type (multi-select)

### Story 6: Toggle Between Base and Adjusted Pricing
**As a** user comparing raw list prices
**I want to** toggle between base and adjusted valuation modes
**So that** I can view pricing before/after component deductions

**Acceptance Criteria:**
- [ ] Toggle button above table with "Base Price" / "Adjusted Price" options
- [ ] Base mode shows `price_usd`, hides delta badges
- [ ] Adjusted mode shows `adjusted_price_usd`, shows delta badges
- [ ] Performance metrics recalculate based on selected mode
- [ ] Selection persisted in localStorage

---

## Technical Architecture

### Database Schema Changes

#### Migration 1: Listing Performance Metrics

```sql
-- Add dual CPU Mark fields to listings table
ALTER TABLE listing
  ADD COLUMN dollar_per_cpu_mark_single FLOAT,
  ADD COLUMN dollar_per_cpu_mark_single_adjusted FLOAT,
  ADD COLUMN dollar_per_cpu_mark_multi FLOAT,
  ADD COLUMN dollar_per_cpu_mark_multi_adjusted FLOAT;

-- Create indexes for filtering/sorting
CREATE INDEX idx_listing_dollar_per_cpu_single ON listing(dollar_per_cpu_mark_single);
CREATE INDEX idx_listing_dollar_per_cpu_multi ON listing(dollar_per_cpu_mark_multi);
```

#### Migration 2: Listing Metadata Fields

```sql
-- Add product identification fields
ALTER TABLE listing
  ADD COLUMN manufacturer VARCHAR(64),
  ADD COLUMN series VARCHAR(128),
  ADD COLUMN model_number VARCHAR(128),
  ADD COLUMN form_factor VARCHAR(32);

-- Create indexes for filtering
CREATE INDEX idx_listing_manufacturer ON listing(manufacturer);
CREATE INDEX idx_listing_form_factor ON listing(form_factor);
```

**Note:** CPU fields already exist (verified from models/core.py). No CPU migration needed.

### Backend Services

#### 1. Listing Calculation Service

**Location:** `apps/api/dealbrain_api/services/listings.py`

**New Methods:**

```python
def calculate_cpu_performance_metrics(listing: Listing) -> dict:
    """Calculate all CPU performance metrics for a listing."""
    if not listing.cpu:
        return {}

    cpu = listing.cpu
    base_price = listing.price_usd
    adjusted_price = listing.adjusted_price_usd or base_price

    metrics = {}

    if cpu.cpu_mark_single:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_price / cpu.cpu_mark_single

    if cpu.cpu_mark_multi:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_price / cpu.cpu_mark_multi

    return metrics

async def update_listing_metrics(
    session: AsyncSession,
    listing_id: int
) -> Listing:
    """Recalculate and persist performance metrics."""
    listing = await get_listing_by_id(session, listing_id)
    metrics = calculate_cpu_performance_metrics(listing)

    for key, value in metrics.items():
        setattr(listing, key, value)

    await session.commit()
    await session.refresh(listing)
    return listing
```

**Trigger Points:**
- Listing create/update
- CPU assignment change
- Valuation rule execution (adjusted_price update)

#### 2. Ports Profile Service

**Location:** `apps/api/dealbrain_api/services/ports.py` (new)

**Methods:**

```python
async def create_or_update_ports_profile(
    session: AsyncSession,
    listing_id: int,
    ports_data: list[dict]
) -> PortsProfile:
    """Create/update ports profile from structured data.

    Args:
        ports_data: [{"port_type": "USB-A", "quantity": 3}, ...]
    """
    listing = await get_listing_by_id(session, listing_id)

    if listing.ports_profile_id:
        profile = await get_ports_profile(session, listing.ports_profile_id)
        # Clear existing ports
        for port in profile.ports:
            await session.delete(port)
    else:
        profile = PortsProfile(name=f"Listing {listing_id} Ports")
        session.add(profile)
        await session.flush()
        listing.ports_profile_id = profile.id

    # Add new ports
    for port_data in ports_data:
        port = Port(
            port_profile_id=profile.id,
            port_type=port_data['port_type'],
            quantity=port_data['quantity']
        )
        session.add(port)

    await session.commit()
    return profile
```

### Frontend Components

#### 1. Dual CPU Mark Columns

**Location:** `apps/web/components/listings/listings-table.tsx`

**Column Definitions:**

```typescript
{
  id: 'dollar_per_cpu_mark_single',
  header: '$/CPU Mark (Single)',
  cell: ({ row }) => (
    <DualMetricCell
      raw={row.original.dollar_per_cpu_mark_single}
      adjusted={row.original.dollar_per_cpu_mark_single_adjusted}
    />
  ),
  meta: {
    tooltip: 'Single-thread price efficiency. Adjusted value uses price after deductions.',
    filterType: 'number',
    minWidth: 160,
  }
}
```

**DualMetricCell Component:**

```typescript
interface DualMetricCellProps {
  raw: number | null;
  adjusted: number | null;
}

export function DualMetricCell({ raw, adjusted }: DualMetricCellProps) {
  if (!raw) return <span className="text-muted-foreground">—</span>;

  const improvement = adjusted && raw > adjusted
    ? ((raw - adjusted) / raw * 100).toFixed(0)
    : null;

  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-sm font-medium">${raw.toFixed(2)}</span>
      {adjusted && (
        <span className={cn(
          "text-xs",
          improvement ? "text-green-600 font-medium" : "text-muted-foreground"
        )}>
          ${adjusted.toFixed(2)}
          {improvement && <span className="ml-1">↓{improvement}%</span>}
        </span>
      )}
    </div>
  );
}
```

#### 2. CPU Info Panel

**Location:** `apps/web/components/listings/cpu-info-panel.tsx` (new)

**Component:**

```typescript
interface CpuInfoPanelProps {
  cpu: {
    name: string;
    cpu_mark_single?: number;
    cpu_mark_multi?: number;
    tdp_w?: number;
    release_year?: number;
    igpu_model?: string;
    igpu_mark?: number;
  };
}

export function CpuInfoPanel({ cpu }: CpuInfoPanelProps) {
  return (
    <div className="rounded-lg border bg-muted/20 p-3 space-y-2">
      <h4 className="text-sm font-semibold">{cpu.name}</h4>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div>
          <span className="text-muted-foreground">Single-Thread:</span>{' '}
          <span className="font-medium">{cpu.cpu_mark_single?.toLocaleString() || '—'}</span>
        </div>
        <div>
          <span className="text-muted-foreground">TDP:</span>{' '}
          <span className="font-medium">{cpu.tdp_w ? `${cpu.tdp_w}W` : '—'}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Multi-Thread:</span>{' '}
          <span className="font-medium">{cpu.cpu_mark_multi?.toLocaleString() || '—'}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Year:</span>{' '}
          <span className="font-medium">{cpu.release_year || '—'}</span>
        </div>
        <div className="col-span-2">
          <span className="text-muted-foreground">iGPU:</span>{' '}
          <span className="font-medium">
            {cpu.igpu_model ? `${cpu.igpu_model} (${cpu.igpu_mark || 'N/A'})` : 'None'}
          </span>
        </div>
      </div>
    </div>
  );
}
```

#### 3. Ports Builder

**Location:** `apps/web/components/listings/ports-builder.tsx` (new)

**Component:**

```typescript
interface PortEntry {
  port_type: string;
  quantity: number;
}

interface PortsBuilderProps {
  value: PortEntry[];
  onChange: (ports: PortEntry[]) => void;
}

export function PortsBuilder({ value, onChange }: PortsBuilderProps) {
  const addPort = () => {
    onChange([...value, { port_type: '', quantity: 1 }]);
  };

  const removePort = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const updatePort = (index: number, updates: Partial<PortEntry>) => {
    onChange(value.map((port, i) =>
      i === index ? { ...port, ...updates } : port
    ));
  };

  return (
    <div className="space-y-2">
      {value.map((port, index) => (
        <div key={index} className="flex gap-2">
          <select
            value={port.port_type}
            onChange={(e) => updatePort(index, { port_type: e.target.value })}
            className="flex-1 rounded-md border px-3 py-2 text-sm"
          >
            <option value="">Select type...</option>
            <option value="USB-A">USB-A</option>
            <option value="USB-C">USB-C</option>
            <option value="HDMI">HDMI</option>
            <option value="DisplayPort">DisplayPort</option>
            <option value="Ethernet">Ethernet (RJ45)</option>
            <option value="Thunderbolt">Thunderbolt</option>
            <option value="Audio">3.5mm Audio</option>
            <option value="Other">Other</option>
          </select>
          <input
            type="number"
            min="1"
            max="16"
            value={port.quantity}
            onChange={(e) => updatePort(index, { quantity: parseInt(e.target.value) })}
            className="w-20 rounded-md border px-3 py-2 text-sm"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => removePort(index)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button variant="outline" size="sm" onClick={addPort}>
        <Plus className="h-4 w-4 mr-2" /> Add Port
      </Button>
    </div>
  );
}
```

#### 4. Valuation Mode Toggle

**Location:** `apps/web/components/listings/valuation-mode-toggle.tsx` (new)

**Component:**

```typescript
type ValuationMode = 'base' | 'adjusted';

interface ValuationModeToggleProps {
  value: ValuationMode;
  onChange: (mode: ValuationMode) => void;
}

export function ValuationModeToggle({ value, onChange }: ValuationModeToggleProps) {
  return (
    <div className="inline-flex rounded-lg border bg-muted/20 p-1">
      <button
        className={cn(
          "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
          value === 'base'
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={() => onChange('base')}
      >
        📊 Base Price
      </button>
      <button
        className={cn(
          "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
          value === 'adjusted'
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={() => onChange('adjusted')}
      >
        🔍 Adjusted Price
      </button>
    </div>
  );
}
```

### API Endpoints

#### New Endpoints

**1. Recalculate Listing Metrics**
- `POST /v1/listings/{listing_id}/recalculate-metrics`
- Triggers metric recalculation
- Returns updated listing with all performance fields

**2. Bulk Metric Update**
- `POST /v1/listings/bulk-recalculate-metrics`
- Body: `{ listing_ids: number[] }`
- Triggers batch recalculation (for valuation rule updates)

**3. Ports Profile CRUD**
- `POST /v1/listings/{listing_id}/ports` — Create/update ports
- `GET /v1/listings/{listing_id}/ports` — Get ports breakdown
- `DELETE /v1/listings/{listing_id}/ports` — Clear ports

#### Updated Endpoints

**Enhanced Listing Response:**
```typescript
interface ListingResponse {
  // ... existing fields

  // New performance metrics
  dollar_per_cpu_mark_single: number | null;
  dollar_per_cpu_mark_single_adjusted: number | null;
  dollar_per_cpu_mark_multi: number | null;
  dollar_per_cpu_mark_multi_adjusted: number | null;

  // New metadata
  manufacturer: string | null;
  series: string | null;
  model_number: string | null;
  form_factor: string | null;

  // Enhanced CPU data (from relationship)
  cpu: {
    id: number;
    name: string;
    cpu_mark_single: number | null;
    cpu_mark_multi: number | null;
    igpu_mark: number | null;
    tdp_w: number | null;
    release_year: number | null;
    igpu_model: string | null;
  } | null;

  // Ports data
  ports_profile: {
    id: number;
    ports: Array<{
      port_type: string;
      quantity: number;
    }>;
  } | null;
}
```

---

## Design Specifications

### UI/UX Guidelines

#### 1. Dual Metric Display Pattern

**Layout:**
```
┌─────────────────────┐
│  $0.15              │  ← Raw value (default text)
│  $0.12 ↓20%        │  ← Adjusted value (green, smaller, with improvement %)
└─────────────────────┘
```

**Color Coding:**
- Raw value: Default text color (`text-foreground`)
- Adjusted (better): Green (`text-green-600`)
- Adjusted (worse): Red (`text-red-600`)
- Adjusted (same): Muted (`text-muted-foreground`)

#### 2. CPU Info Panel Design

**Visual Hierarchy:**
1. CPU name (semibold, text-sm)
2. Grid of metrics (2 columns, text-xs)
3. Muted background (`bg-muted/20`)
4. Clear labels with values

**Placement:**
- Below CPU selector in Listing form
- Auto-update on CPU change
- Collapsible on mobile

#### 3. Ports Builder Interface

**Interaction Flow:**
1. Click "Add Port" → New row appears
2. Select type from dropdown → Quantity input enabled
3. Enter quantity (1-16) → Validation on blur
4. Click X → Confirmation, then remove
5. Drag handle (optional) → Reorder ports

**Compact Display:**
- Badge style: `3× USB-A` (quantity × type)
- Space-separated list
- Popover for full details

#### 4. Valuation Mode Toggle

**States:**
- Base (inactive): Gray text, no background
- Base (active): White bg, shadow, dark text
- Adjusted (inactive): Gray text, no background
- Adjusted (active): White bg, shadow, dark text

**Placement:**
- Top-right of Listings table header
- Sticky on scroll
- Next to "Add Listing" button

### Accessibility Requirements

- **Color Contrast:** All text meets WCAG AA (4.5:1 for normal, 3:1 for large)
- **Icon + Text:** Performance indicators use both (↓ + "20%" not just color)
- **Keyboard Navigation:** All interactive elements tab-accessible
- **Screen Readers:** ARIA labels on toggle buttons, port controls
- **Focus Indicators:** Visible focus rings on all inputs

---

## Dependencies & Constraints

### Technical Dependencies

- **Backend:** SQLAlchemy 2.0, Alembic, FastAPI
- **Frontend:** React 18, Next.js 14, TanStack Table, TanStack Query
- **Database:** PostgreSQL 14+
- **Existing Tables:** `cpu`, `listing`, `ports_profile`, `port`

### Constraints

1. **Data Availability:** PassMark benchmark data must be sourced externally (API or manual CSV import)
2. **Backward Compatibility:** Existing `dollar_per_cpu_mark` field remains for legacy support
3. **Migration Impact:** Recalculation required for all existing listings (run as background job)
4. **Ports Complexity:** PortsProfile table reuse requires careful foreign key management

### Assumptions

- PassMark benchmark data available for 95%+ of CPUs in catalog
- Users understand single-thread vs multi-thread performance tradeoffs
- Adjusted price calculations already functioning correctly from valuation rules
- Ports data entry is optional (not required for listing creation)

---

## Rollout Plan

### Phase 1: Database & Backend (Week 1)

1. **Migrations:**
   - Create listing performance metric fields
   - Create listing metadata fields
   - Add indexes

2. **Backend Services:**
   - Implement `calculate_cpu_performance_metrics()`
   - Add metric recalculation endpoints
   - Create ports profile service
   - Add bulk update support

3. **Data Seeding:**
   - Import PassMark benchmark data for existing CPUs
   - Run bulk metric recalculation for all listings

### Phase 2: Core UI Components (Week 2)

1. **Listings Table:**
   - Add dual CPU Mark columns
   - Implement DualMetricCell component
   - Add column filters/sorting

2. **Listing Form:**
   - Add manufacturer/series/model fields
   - Add form factor dropdown
   - Integrate CPU info panel
   - Add ports builder

3. **Valuation Toggle:**
   - Implement mode toggle component
   - Wire to listing table state
   - Add localStorage persistence

### Phase 3: Polish & Testing (Week 3)

1. **Performance:**
   - Optimize metric calculations
   - Add React.memo to table cells
   - Implement virtual scrolling if needed

2. **Accessibility:**
   - Audit color contrast
   - Add ARIA labels
   - Test keyboard navigation

3. **Documentation:**
   - Update user guide
   - Add API docs
   - Create data import guide (PassMark CSV)

### Phase 4: Release & Monitor (Week 4)

1. **Staged Release:**
   - Deploy backend changes
   - Enable feature flag for beta users
   - Monitor performance/errors

2. **Full Release:**
   - Enable for all users
   - Announce in changelog
   - Gather feedback

---

## Open Questions

1. **PassMark Data Source:**
   - Use PassMark API (paid) or manual CSV updates?
   - Frequency of benchmark data updates (weekly/monthly)?
   - Fallback strategy for missing CPU data?

2. **Ports Field Scope:**
   - Should ports be filterable (e.g., "Show listings with ≥2 USB-C")?
   - Display in table cell or tooltip/modal only?
   - Support for port specifications (e.g., "USB-C 3.2 Gen 2")?

3. **Valuation Toggle Persistence:**
   - User-level preference (DB) or browser-only (localStorage)?
   - Should toggle affect other views (dashboard, details page)?
   - Default mode for new users (base or adjusted)?

4. **Performance at Scale:**
   - Acceptable recalculation time for 10,000+ listings?
   - Background job vs. on-demand calculation?
   - Caching strategy for frequently accessed metrics?

---

## Appendix

### A. Database Schema Reference

**Listing Table (Updated):**
```sql
CREATE TABLE listing (
  id SERIAL PRIMARY KEY,
  -- Existing fields...

  -- Performance Metrics (New)
  dollar_per_cpu_mark_single FLOAT,
  dollar_per_cpu_mark_single_adjusted FLOAT,
  dollar_per_cpu_mark_multi FLOAT,
  dollar_per_cpu_mark_multi_adjusted FLOAT,

  -- Product Metadata (New)
  manufacturer VARCHAR(64),
  series VARCHAR(128),
  model_number VARCHAR(128),
  form_factor VARCHAR(32),

  -- Existing relationships
  cpu_id INTEGER REFERENCES cpu(id),
  ports_profile_id INTEGER REFERENCES ports_profile(id),
  -- ...
);
```

**CPU Table (No Changes):**
```sql
-- All required fields already exist:
-- cpu_mark_single, cpu_mark_multi, igpu_mark, tdp_w, release_year, igpu_model
```

### B. API Contract Examples

**POST /v1/listings/{id}/recalculate-metrics**

Request:
```json
{} // Empty body, triggers recalculation
```

Response:
```json
{
  "id": 123,
  "price_usd": 599.99,
  "adjusted_price_usd": 499.99,
  "dollar_per_cpu_mark_single": 0.15,
  "dollar_per_cpu_mark_single_adjusted": 0.125,
  "dollar_per_cpu_mark_multi": 0.017,
  "dollar_per_cpu_mark_multi_adjusted": 0.014,
  "cpu": {
    "id": 45,
    "name": "Intel Core i7-12700K",
    "cpu_mark_single": 3985,
    "cpu_mark_multi": 35864,
    "tdp_w": 125,
    "release_year": 2021
  }
}
```

**POST /v1/listings/{id}/ports**

Request:
```json
{
  "ports": [
    { "port_type": "USB-A", "quantity": 4 },
    { "port_type": "USB-C", "quantity": 2 },
    { "port_type": "HDMI", "quantity": 1 },
    { "port_type": "Ethernet", "quantity": 1 }
  ]
}
```

Response:
```json
{
  "ports_profile": {
    "id": 67,
    "name": "Listing 123 Ports",
    "ports": [
      { "port_type": "USB-A", "quantity": 4 },
      { "port_type": "USB-C", "quantity": 2 },
      { "port_type": "HDMI", "quantity": 1 },
      { "port_type": "Ethernet", "quantity": 1 }
    ]
  }
}
```

### C. Metric Calculation Examples

**Example 1: Desktop Gaming PC**
- CPU: Intel Core i7-12700K
- List Price: $799
- Adjusted Price: $649 (after $150 RAM/storage deduction)
- CPU Mark Single: 3985
- CPU Mark Multi: 35864

**Calculations:**
- `$/CPU Mark (Single)`: $799 / 3985 = **$0.200**
- `$/CPU Mark (Single) Adjusted`: $649 / 3985 = **$0.163** (↓18.5%)
- `$/CPU Mark (Multi)`: $799 / 35864 = **$0.022**
- `$/CPU Mark (Multi) Adjusted`: $649 / 35864 = **$0.018** (↓18.5%)

**Display:**
```
┌─ $/CPU Mark (Single) ─┐  ┌─ $/CPU Mark (Multi) ─┐
│  $0.20                 │  │  $0.022              │
│  $0.16 ↓18%           │  │  $0.018 ↓18%         │
└────────────────────────┘  └──────────────────────┘
```

---

**Document Status:** Ready for Review
**Next Steps:** Implementation plan creation, technical feasibility review, PassMark data source selection
