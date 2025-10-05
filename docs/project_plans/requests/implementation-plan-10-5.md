# Implementation Plan: Performance Metrics & Data Enrichment

**PRD Reference:** `prd-10-5-performance-metrics.md`
**Date:** October 5, 2025
**Version:** 1.0

---

## Overview

This implementation plan breaks down the Performance Metrics & Data Enrichment feature into concrete, actionable phases. The work spans database migrations, backend calculation services, frontend UI components, and data population workflows.

**Estimated Timeline:** 3-4 weeks
**Complexity:** Medium-High

---

## Phase 1: Database Schema & Migrations

**Duration:** 1-2 days
**Dependencies:** None

### Tasks

#### 1.1 Create Migration for Listing Performance Metrics

**File:** `apps/api/alembic/versions/0012_add_listing_performance_metrics.py`

```python
"""Add dual CPU Mark performance metrics to listings

Revision ID: 0012
Revises: 0011
Create Date: 2025-10-05
"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add performance metric columns
    op.add_column('listing', sa.Column('dollar_per_cpu_mark_single', sa.Float(), nullable=True))
    op.add_column('listing', sa.Column('dollar_per_cpu_mark_single_adjusted', sa.Float(), nullable=True))
    op.add_column('listing', sa.Column('dollar_per_cpu_mark_multi', sa.Float(), nullable=True))
    op.add_column('listing', sa.Column('dollar_per_cpu_mark_multi_adjusted', sa.Float(), nullable=True))

    # Create indexes for filtering and sorting
    op.create_index('idx_listing_dollar_per_cpu_single', 'listing', ['dollar_per_cpu_mark_single'])
    op.create_index('idx_listing_dollar_per_cpu_multi', 'listing', ['dollar_per_cpu_mark_multi'])
    op.create_index('idx_listing_dollar_per_cpu_single_adj', 'listing', ['dollar_per_cpu_mark_single_adjusted'])
    op.create_index('idx_listing_dollar_per_cpu_multi_adj', 'listing', ['dollar_per_cpu_mark_multi_adjusted'])

def downgrade() -> None:
    op.drop_index('idx_listing_dollar_per_cpu_multi_adj', table_name='listing')
    op.drop_index('idx_listing_dollar_per_cpu_single_adj', table_name='listing')
    op.drop_index('idx_listing_dollar_per_cpu_multi', table_name='listing')
    op.drop_index('idx_listing_dollar_per_cpu_single', table_name='listing')

    op.drop_column('listing', 'dollar_per_cpu_mark_multi_adjusted')
    op.drop_column('listing', 'dollar_per_cpu_mark_multi')
    op.drop_column('listing', 'dollar_per_cpu_mark_single_adjusted')
    op.drop_column('listing', 'dollar_per_cpu_mark_single')
```

**Commands:**
```bash
poetry run alembic revision --autogenerate -m "add listing performance metrics"
# Edit generated migration to match above
poetry run alembic upgrade head
```

#### 1.2 Create Migration for Listing Metadata

**File:** `apps/api/alembic/versions/0013_add_listing_metadata_fields.py`

```python
"""Add product metadata fields to listings

Revision ID: 0013
Revises: 0012
Create Date: 2025-10-05
"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add product identification columns
    op.add_column('listing', sa.Column('manufacturer', sa.String(64), nullable=True))
    op.add_column('listing', sa.Column('series', sa.String(128), nullable=True))
    op.add_column('listing', sa.Column('model_number', sa.String(128), nullable=True))
    op.add_column('listing', sa.Column('form_factor', sa.String(32), nullable=True))

    # Create indexes for filtering
    op.create_index('idx_listing_manufacturer', 'listing', ['manufacturer'])
    op.create_index('idx_listing_form_factor', 'listing', ['form_factor'])

def downgrade() -> None:
    op.drop_index('idx_listing_form_factor', table_name='listing')
    op.drop_index('idx_listing_manufacturer', table_name='listing')

    op.drop_column('listing', 'form_factor')
    op.drop_column('listing', 'model_number')
    op.drop_column('listing', 'series')
    op.drop_column('listing', 'manufacturer')
```

**Commands:**
```bash
poetry run alembic revision --autogenerate -m "add listing metadata fields"
# Edit generated migration to match above
poetry run alembic upgrade head
```

#### 1.3 Update SQLAlchemy Models

**File:** `apps/api/dealbrain_api/models/core.py`

**Changes to `Listing` class:**

```python
class Listing(Base, TimestampMixin):
    __tablename__ = "listing"

    # ... existing fields ...

    # Performance Metrics (NEW)
    dollar_per_cpu_mark_single: Mapped[float | None]
    dollar_per_cpu_mark_single_adjusted: Mapped[float | None]
    dollar_per_cpu_mark_multi: Mapped[float | None]
    dollar_per_cpu_mark_multi_adjusted: Mapped[float | None]

    # Product Metadata (NEW)
    manufacturer: Mapped[str | None] = mapped_column(String(64))
    series: Mapped[str | None] = mapped_column(String(128))
    model_number: Mapped[str | None] = mapped_column(String(128))
    form_factor: Mapped[str | None] = mapped_column(String(32))

    # ... existing relationships ...
```

**Validation:**
- Run `poetry run alembic check` to verify model/migration alignment
- Test migration on local database
- Verify indexes created successfully

**Acceptance Criteria:**
- [ ] Migrations created and tested
- [ ] SQLAlchemy models updated
- [ ] Indexes created for performance
- [ ] Backward compatibility verified (existing listings unaffected)

---

## Phase 2: Backend Calculation Services

**Duration:** 2-3 days
**Dependencies:** Phase 1 complete

### Tasks

#### 2.1 Implement CPU Performance Calculation Service

**File:** `apps/api/dealbrain_api/services/listings.py`

**Add new method:**

```python
def calculate_cpu_performance_metrics(listing: Listing) -> dict[str, float]:
    """Calculate all CPU-based performance metrics for a listing.

    Returns:
        Dictionary with metric keys and calculated values.
        Empty dict if CPU not assigned or missing benchmark data.
    """
    if not listing.cpu:
        return {}

    cpu = listing.cpu
    base_price = float(listing.price_usd)
    adjusted_price = float(listing.adjusted_price_usd) if listing.adjusted_price_usd else base_price

    metrics = {}

    # Single-thread metrics
    if cpu.cpu_mark_single and cpu.cpu_mark_single > 0:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_price / cpu.cpu_mark_single

    # Multi-thread metrics
    if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_price / cpu.cpu_mark_multi

    return metrics
```

**Add update method:**

```python
async def update_listing_metrics(
    session: AsyncSession,
    listing_id: int
) -> Listing:
    """Recalculate and persist all performance metrics for a listing.

    Args:
        session: Database session
        listing_id: ID of listing to update

    Returns:
        Updated listing with recalculated metrics

    Raises:
        ValueError: If listing not found
    """
    # Fetch with CPU relationship
    stmt = select(Listing).where(Listing.id == listing_id).options(joinedload(Listing.cpu))
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    # Calculate metrics
    metrics = calculate_cpu_performance_metrics(listing)

    # Update listing
    for key, value in metrics.items():
        setattr(listing, key, value)

    await session.commit()
    await session.refresh(listing)
    return listing
```

**Add bulk update method:**

```python
async def bulk_update_listing_metrics(
    session: AsyncSession,
    listing_ids: list[int] | None = None
) -> int:
    """Recalculate metrics for multiple listings.

    Args:
        session: Database session
        listing_ids: List of IDs to update. If None, updates all listings.

    Returns:
        Count of listings updated
    """
    stmt = select(Listing).options(joinedload(Listing.cpu))
    if listing_ids:
        stmt = stmt.where(Listing.id.in_(listing_ids))

    result = await session.execute(stmt)
    listings = result.scalars().all()

    updated_count = 0
    for listing in listings:
        metrics = calculate_cpu_performance_metrics(listing)
        for key, value in metrics.items():
            setattr(listing, key, value)
        updated_count += 1

    await session.commit()
    return updated_count
```

**Test Coverage:**

```python
# tests/test_listing_metrics.py

async def test_calculate_cpu_performance_metrics():
    """Test metric calculation with valid CPU data."""
    cpu = Cpu(
        name="Intel Core i7-12700K",
        cpu_mark_single=3985,
        cpu_mark_multi=35864
    )
    listing = Listing(
        title="Test PC",
        price_usd=799.99,
        adjusted_price_usd=649.99,
        cpu=cpu
    )

    metrics = calculate_cpu_performance_metrics(listing)

    assert metrics['dollar_per_cpu_mark_single'] == pytest.approx(0.200, rel=0.01)
    assert metrics['dollar_per_cpu_mark_single_adjusted'] == pytest.approx(0.163, rel=0.01)
    assert metrics['dollar_per_cpu_mark_multi'] == pytest.approx(0.0223, rel=0.01)
    assert metrics['dollar_per_cpu_mark_multi_adjusted'] == pytest.approx(0.0181, rel=0.01)

async def test_calculate_cpu_performance_metrics_no_cpu():
    """Test graceful handling when CPU not assigned."""
    listing = Listing(title="Test", price_usd=500)
    metrics = calculate_cpu_performance_metrics(listing)
    assert metrics == {}

async def test_update_listing_metrics(session):
    """Test metric persistence."""
    # Create CPU and listing
    cpu = Cpu(name="Test CPU", cpu_mark_single=4000, cpu_mark_multi=30000)
    session.add(cpu)
    await session.flush()

    listing = Listing(title="Test", price_usd=800, cpu_id=cpu.id)
    session.add(listing)
    await session.commit()

    # Update metrics
    updated = await update_listing_metrics(session, listing.id)

    assert updated.dollar_per_cpu_mark_single == 0.2  # 800 / 4000
    assert updated.dollar_per_cpu_mark_multi == pytest.approx(0.0267, rel=0.01)
```

**Acceptance Criteria:**
- [ ] Calculation service implemented
- [ ] Null/missing CPU handled gracefully
- [ ] Bulk update method working
- [ ] Unit tests passing (>90% coverage)
- [ ] Edge cases tested (zero CPU marks, null adjusted price)

#### 2.2 Implement Ports Management Service

**File:** `apps/api/dealbrain_api/services/ports.py` (new)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from dealbrain_api.models.core import Listing, PortsProfile, Port

async def get_or_create_ports_profile(
    session: AsyncSession,
    listing_id: int
) -> PortsProfile:
    """Get existing ports profile or create new one for listing."""
    stmt = select(Listing).where(Listing.id == listing_id).options(
        joinedload(Listing.ports_profile).joinedload(PortsProfile.ports)
    )
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    if listing.ports_profile:
        return listing.ports_profile

    # Create new profile
    profile = PortsProfile(name=f"Listing {listing_id} Ports")
    session.add(profile)
    await session.flush()

    listing.ports_profile_id = profile.id
    await session.commit()
    await session.refresh(profile)
    return profile

async def update_listing_ports(
    session: AsyncSession,
    listing_id: int,
    ports_data: list[dict]
) -> PortsProfile:
    """Update ports for a listing.

    Args:
        session: Database session
        listing_id: Listing ID
        ports_data: List of dicts with 'port_type' and 'quantity' keys

    Returns:
        Updated PortsProfile with ports

    Example:
        ports_data = [
            {"port_type": "USB-A", "quantity": 4},
            {"port_type": "HDMI", "quantity": 1}
        ]
    """
    profile = await get_or_create_ports_profile(session, listing_id)

    # Clear existing ports
    await session.execute(
        sa.delete(Port).where(Port.port_profile_id == profile.id)
    )

    # Add new ports
    for port_data in ports_data:
        port = Port(
            port_profile_id=profile.id,
            port_type=port_data['port_type'],
            quantity=port_data['quantity']
        )
        session.add(port)

    await session.commit()
    await session.refresh(profile)
    return profile

async def get_listing_ports(
    session: AsyncSession,
    listing_id: int
) -> list[dict]:
    """Get ports for a listing as simple dict list.

    Returns:
        List of dicts with port_type and quantity, or empty list if none.
    """
    stmt = select(Listing).where(Listing.id == listing_id).options(
        joinedload(Listing.ports_profile).joinedload(PortsProfile.ports)
    )
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing or not listing.ports_profile:
        return []

    return [
        {"port_type": port.port_type, "quantity": port.quantity}
        for port in listing.ports_profile.ports
    ]
```

**Test Coverage:**

```python
# tests/test_ports_service.py

async def test_update_listing_ports(session):
    """Test creating and updating ports."""
    listing = Listing(title="Test PC", price_usd=500)
    session.add(listing)
    await session.commit()

    ports_data = [
        {"port_type": "USB-A", "quantity": 4},
        {"port_type": "HDMI", "quantity": 2}
    ]

    profile = await update_listing_ports(session, listing.id, ports_data)

    assert len(profile.ports) == 2
    assert profile.ports[0].port_type == "USB-A"
    assert profile.ports[0].quantity == 4

async def test_get_listing_ports_empty(session):
    """Test getting ports when none exist."""
    listing = Listing(title="Test", price_usd=500)
    session.add(listing)
    await session.commit()

    ports = await get_listing_ports(session, listing.id)
    assert ports == []
```

**Acceptance Criteria:**
- [ ] Ports service implemented
- [ ] Get/create/update methods working
- [ ] Profile reuse for existing listings
- [ ] Unit tests passing
- [ ] Cascade delete verified (deleting listing removes ports)

#### 2.3 Create API Endpoints

**File:** `apps/api/dealbrain_api/api/listings.py`

**Add recalculate endpoint:**

```python
@router.post("/{listing_id}/recalculate-metrics", response_model=ListingResponse)
async def recalculate_listing_metrics(
    listing_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Recalculate all performance metrics for a listing."""
    try:
        listing = await listing_service.update_listing_metrics(session, listing_id)
        return listing
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Add bulk recalculate endpoint:**

```python
from pydantic import BaseModel

class BulkRecalculateRequest(BaseModel):
    listing_ids: list[int] | None = None

class BulkRecalculateResponse(BaseModel):
    updated_count: int
    message: str

@router.post("/bulk-recalculate-metrics", response_model=BulkRecalculateResponse)
async def bulk_recalculate_metrics(
    request: BulkRecalculateRequest,
    session: AsyncSession = Depends(get_session)
):
    """Recalculate metrics for multiple listings.

    If listing_ids is None or empty, updates all listings.
    """
    count = await listing_service.bulk_update_listing_metrics(
        session,
        request.listing_ids
    )
    return BulkRecalculateResponse(
        updated_count=count,
        message=f"Updated {count} listing(s)"
    )
```

**Add ports endpoints:**

```python
# In apps/api/dealbrain_api/api/ports.py (new file)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from dealbrain_api.db import get_session
from dealbrain_api.services import ports as ports_service

router = APIRouter(prefix="/v1/listings", tags=["ports"])

class PortEntry(BaseModel):
    port_type: str
    quantity: int

class UpdatePortsRequest(BaseModel):
    ports: list[PortEntry]

class PortsResponse(BaseModel):
    ports: list[PortEntry]

@router.post("/{listing_id}/ports", response_model=PortsResponse)
async def update_listing_ports(
    listing_id: int,
    request: UpdatePortsRequest,
    session: AsyncSession = Depends(get_session)
):
    """Create or update ports for a listing."""
    try:
        ports_data = [p.dict() for p in request.ports]
        await ports_service.update_listing_ports(session, listing_id, ports_data)
        ports = await ports_service.get_listing_ports(session, listing_id)
        return PortsResponse(ports=ports)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{listing_id}/ports", response_model=PortsResponse)
async def get_listing_ports(
    listing_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get ports for a listing."""
    ports = await ports_service.get_listing_ports(session, listing_id)
    return PortsResponse(ports=ports)
```

**Register router in `apps/api/dealbrain_api/api/__init__.py`:**

```python
from dealbrain_api.api import ports

app.include_router(ports.router)
```

**Update ListingResponse schema:**

**File:** `apps/api/dealbrain_api/api/schemas/listings.py`

```python
class ListingResponse(BaseModel):
    id: int
    # ... existing fields ...

    # Performance metrics (NEW)
    dollar_per_cpu_mark_single: float | None = None
    dollar_per_cpu_mark_single_adjusted: float | None = None
    dollar_per_cpu_mark_multi: float | None = None
    dollar_per_cpu_mark_multi_adjusted: float | None = None

    # Product metadata (NEW)
    manufacturer: str | None = None
    series: str | None = None
    model_number: str | None = None
    form_factor: str | None = None

    # Enhanced CPU data (expand existing)
    cpu: CpuResponse | None = None

    class Config:
        from_attributes = True

class CpuResponse(BaseModel):
    id: int
    name: str
    manufacturer: str
    cpu_mark_single: int | None = None
    cpu_mark_multi: int | None = None
    igpu_mark: int | None = None
    tdp_w: int | None = None
    release_year: int | None = None
    igpu_model: str | None = None

    class Config:
        from_attributes = True
```

**Acceptance Criteria:**
- [ ] Recalculate endpoint implemented
- [ ] Bulk recalculate endpoint implemented
- [ ] Ports CRUD endpoints working
- [ ] API responses include new fields
- [ ] OpenAPI docs updated
- [ ] Integration tests passing

---

## Phase 3: Frontend Core Components

**Duration:** 3-4 days
**Dependencies:** Phase 2 complete

### Tasks

#### 3.1 Create DualMetricCell Component

**File:** `apps/web/components/listings/dual-metric-cell.tsx`

```typescript
import { cn } from "@/lib/utils";

interface DualMetricCellProps {
  raw: number | null | undefined;
  adjusted: number | null | undefined;
  prefix?: string;  // e.g., "$"
  suffix?: string;  // e.g., "W"
  decimals?: number;  // default 2
}

export function DualMetricCell({
  raw,
  adjusted,
  prefix = "$",
  suffix = "",
  decimals = 2,
}: DualMetricCellProps) {
  if (!raw && raw !== 0) {
    return <span className="text-muted-foreground text-sm">—</span>;
  }

  const formatValue = (val: number) =>
    `${prefix}${val.toFixed(decimals)}${suffix}`;

  // Calculate improvement percentage
  const improvement =
    adjusted !== null && adjusted !== undefined && raw > adjusted
      ? ((raw - adjusted) / raw * 100).toFixed(0)
      : null;

  const degradation =
    adjusted !== null && adjusted !== undefined && adjusted > raw
      ? ((adjusted - raw) / raw * 100).toFixed(0)
      : null;

  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-sm font-medium">{formatValue(raw)}</span>
      {adjusted !== null && adjusted !== undefined && (
        <span
          className={cn(
            "text-xs",
            improvement && "text-green-600 font-medium",
            degradation && "text-red-600 font-medium",
            !improvement && !degradation && "text-muted-foreground"
          )}
        >
          {formatValue(adjusted)}
          {improvement && (
            <span className="ml-1" title="Improvement after adjustments">
              ↓{improvement}%
            </span>
          )}
          {degradation && (
            <span className="ml-1" title="Higher after adjustments">
              ↑{degradation}%
            </span>
          )}
        </span>
      )}
    </div>
  );
}
```

**Memoization:**

```typescript
export const DualMetricCell = React.memo(DualMetricCellComponent);
```

**Acceptance Criteria:**
- [ ] Component renders raw value prominently
- [ ] Adjusted value shown below in smaller text
- [ ] Green for improvement, red for degradation, gray for neutral
- [ ] Percentage change displayed with arrow indicator
- [ ] Memoized for performance
- [ ] Handles null/undefined gracefully

#### 3.2 Create CPUInfoPanel Component

**File:** `apps/web/components/listings/cpu-info-panel.tsx`

```typescript
interface CpuInfoPanelProps {
  cpu: {
    name: string;
    cpu_mark_single?: number | null;
    cpu_mark_multi?: number | null;
    tdp_w?: number | null;
    release_year?: number | null;
    igpu_model?: string | null;
    igpu_mark?: number | null;
  } | null;
}

export function CpuInfoPanel({ cpu }: CpuInfoPanelProps) {
  if (!cpu) {
    return (
      <div className="rounded-lg border bg-muted/10 p-3 text-sm text-muted-foreground">
        No CPU selected
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-muted/20 p-3 space-y-2">
      <h4 className="text-sm font-semibold text-foreground">{cpu.name}</h4>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div>
          <span className="text-muted-foreground">Single-Thread:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.cpu_mark_single?.toLocaleString() || "—"}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">TDP:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.tdp_w ? `${cpu.tdp_w}W` : "—"}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">Multi-Thread:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.cpu_mark_multi?.toLocaleString() || "—"}
          </span>
        </div>
        <div>
          <span className="text-muted-foreground">Year:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.release_year || "—"}
          </span>
        </div>
        <div className="col-span-2 pt-1 border-t border-border">
          <span className="text-muted-foreground">iGPU:</span>{" "}
          <span className="font-medium text-foreground">
            {cpu.igpu_model
              ? `${cpu.igpu_model} ${cpu.igpu_mark ? `(G3D: ${cpu.igpu_mark.toLocaleString()})` : ""}`
              : "None"}
          </span>
        </div>
      </div>
    </div>
  );
}
```

**Usage in Listing Form:**

```typescript
// In apps/web/app/listings/[id]/page.tsx or new listing form

<FormField label="CPU" name="cpu_id">
  <ComboBox
    options={cpuOptions}
    value={cpuId}
    onChange={(id) => {
      setCpuId(id);
      // Fetch full CPU data
      fetchCpu(id).then(setCpuData);
    }}
  />
</FormField>

{cpuData && <CpuInfoPanel cpu={cpuData} />}
```

**Acceptance Criteria:**
- [ ] Panel displays all CPU metadata
- [ ] Grid layout for metrics (2 columns)
- [ ] iGPU section with model + G3D score
- [ ] Null values show "—"
- [ ] Updates when CPU selection changes
- [ ] Responsive on mobile (stacks to 1 column)

#### 3.3 Create PortsBuilder Component

**File:** `apps/web/components/listings/ports-builder.tsx`

```typescript
import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PortEntry {
  port_type: string;
  quantity: number;
}

interface PortsBuilderProps {
  value: PortEntry[];
  onChange: (ports: PortEntry[]) => void;
}

const PORT_TYPE_OPTIONS = [
  { value: "USB-A", label: "USB-A" },
  { value: "USB-C", label: "USB-C" },
  { value: "HDMI", label: "HDMI" },
  { value: "DisplayPort", label: "DisplayPort" },
  { value: "Ethernet", label: "Ethernet (RJ45)" },
  { value: "Thunderbolt", label: "Thunderbolt" },
  { value: "Audio", label: "3.5mm Audio" },
  { value: "SD Card", label: "SD Card Reader" },
  { value: "Other", label: "Other" },
];

export function PortsBuilder({ value, onChange }: PortsBuilderProps) {
  const addPort = () => {
    onChange([...value, { port_type: "", quantity: 1 }]);
  };

  const removePort = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const updatePort = (index: number, updates: Partial<PortEntry>) => {
    onChange(
      value.map((port, i) =>
        i === index ? { ...port, ...updates } : port
      )
    );
  };

  return (
    <div className="space-y-2">
      <div className="space-y-2">
        {value.map((port, index) => (
          <div key={index} className="flex gap-2 items-center">
            <select
              value={port.port_type}
              onChange={(e) => updatePort(index, { port_type: e.target.value })}
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Select type...</option>
              {PORT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="1"
              max="16"
              value={port.quantity}
              onChange={(e) =>
                updatePort(index, { quantity: parseInt(e.target.value) || 1 })
              }
              className="w-20 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => removePort(index)}
              aria-label="Remove port"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={addPort}
      >
        <Plus className="h-4 w-4 mr-2" /> Add Port
      </Button>
    </div>
  );
}
```

**Compact Display Component:**

**File:** `apps/web/components/listings/ports-display.tsx`

```typescript
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface PortsDisplayProps {
  ports: Array<{ port_type: string; quantity: number }>;
}

export function PortsDisplay({ ports }: PortsDisplayProps) {
  if (!ports || ports.length === 0) {
    return <span className="text-muted-foreground text-sm">—</span>;
  }

  const compactDisplay = ports
    .map((p) => `${p.quantity}× ${p.port_type}`)
    .join("  ");

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="text-left text-sm hover:underline cursor-pointer">
          {compactDisplay}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64">
        <div className="space-y-2">
          <h4 className="font-semibold text-sm">Ports</h4>
          <div className="space-y-1">
            {ports.map((port, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span>{port.port_type}</span>
                <span className="text-muted-foreground">× {port.quantity}</span>
              </div>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

**Acceptance Criteria:**
- [ ] Builder allows adding/removing port entries
- [ ] Port type dropdown with 9 options
- [ ] Quantity input (1-16 validation)
- [ ] Compact display in table (e.g., "3× USB-A  2× HDMI")
- [ ] Popover shows full port list
- [ ] Empty state handled gracefully

#### 3.4 Create ValuationModeToggle Component

**File:** `apps/web/components/listings/valuation-mode-toggle.tsx`

```typescript
"use client";

import { cn } from "@/lib/utils";
import { DollarSign, Calculator } from "lucide-react";

export type ValuationMode = "base" | "adjusted";

interface ValuationModeToggleProps {
  value: ValuationMode;
  onChange: (mode: ValuationMode) => void;
}

export function ValuationModeToggle({ value, onChange }: ValuationModeToggleProps) {
  return (
    <div
      className="inline-flex rounded-lg border bg-muted/20 p-1"
      role="tablist"
      aria-label="Valuation mode"
    >
      <button
        role="tab"
        aria-selected={value === "base"}
        aria-label="Show base prices"
        className={cn(
          "inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
          value === "base"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={() => onChange("base")}
      >
        <DollarSign className="h-4 w-4" />
        Base Price
      </button>
      <button
        role="tab"
        aria-selected={value === "adjusted"}
        aria-label="Show adjusted prices with component deductions"
        className={cn(
          "inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
          value === "adjusted"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
        onClick={() => onChange("adjusted")}
      >
        <Calculator className="h-4 w-4" />
        Adjusted Price
      </button>
    </div>
  );
}
```

**Integration in Listings Table:**

```typescript
// In apps/web/components/listings/listings-table.tsx

const [valuationMode, setValuationMode] = useState<ValuationMode>("adjusted");

// Persist to localStorage
useEffect(() => {
  localStorage.setItem("valuationMode", valuationMode);
}, [valuationMode]);

// Restore from localStorage
useEffect(() => {
  const saved = localStorage.getItem("valuationMode") as ValuationMode;
  if (saved) setValuationMode(saved);
}, []);

// In header section
<div className="flex items-center justify-between">
  <h2>Listings</h2>
  <ValuationModeToggle value={valuationMode} onChange={setValuationMode} />
</div>
```

**Acceptance Criteria:**
- [ ] Toggle switches between base/adjusted modes
- [ ] Active state shows background + shadow
- [ ] Icons (DollarSign, Calculator) aid recognition
- [ ] ARIA labels for accessibility
- [ ] Selection persists in localStorage
- [ ] Smooth transition animation

---

## Phase 4: Listings Table Integration

**Duration:** 2-3 days
**Dependencies:** Phase 3 complete

### Tasks

#### 4.1 Add Dual CPU Mark Columns

**File:** `apps/web/components/listings/listings-table.tsx`

**Import new components:**

```typescript
import { DualMetricCell } from "./dual-metric-cell";
import { ValuationModeToggle, type ValuationMode } from "./valuation-mode-toggle";
import { PortsDisplay } from "./ports-display";
```

**Add state for valuation mode:**

```typescript
const [valuationMode, setValuationMode] = useState<ValuationMode>(() => {
  const saved = localStorage.getItem("valuationMode");
  return (saved as ValuationMode) || "adjusted";
});

useEffect(() => {
  localStorage.setItem("valuationMode", valuationMode);
}, [valuationMode]);
```

**Add column definitions:**

```typescript
const columns = useMemo<ColumnDef<ListingRow>[]>(() => {
  // ... existing columns ...

  // Add after existing Valuation column
  {
    id: 'dollar_per_cpu_mark_single',
    header: '$/CPU Mark (Single)',
    accessorKey: 'dollar_per_cpu_mark_single',
    cell: ({ row }) => (
      <DualMetricCell
        raw={row.original.dollar_per_cpu_mark_single}
        adjusted={row.original.dollar_per_cpu_mark_single_adjusted}
        prefix="$"
        decimals={3}
      />
    ),
    meta: {
      tooltip: 'Single-thread price efficiency. Lower = better value.',
      description: 'Cost per PassMark single-thread point. Adjusted value uses price after RAM/storage deductions.',
      filterType: 'number',
      minWidth: 160,
    },
    enableSorting: true,
    enableResizing: true,
    enableColumnFilter: true,
    size: 160,
  },
  {
    id: 'dollar_per_cpu_mark_multi',
    header: '$/CPU Mark (Multi)',
    accessorKey: 'dollar_per_cpu_mark_multi',
    cell: ({ row }) => (
      <DualMetricCell
        raw={row.original.dollar_per_cpu_mark_multi}
        adjusted={row.original.dollar_per_cpu_mark_multi_adjusted}
        prefix="$"
        decimals={3}
      />
    ),
    meta: {
      tooltip: 'Multi-thread price efficiency. Lower = better value.',
      description: 'Cost per PassMark multi-thread point. Adjusted value uses price after RAM/storage deductions.',
      filterType: 'number',
      minWidth: 160,
    },
    enableSorting: true,
    enableResizing: true,
    enableColumnFilter: true,
    size: 160,
  },

  // ... rest of columns
}, [/* deps */]);
```

**Update TypeScript interface:**

```typescript
interface ListingRow extends ListingRecord {
  // ... existing fields ...

  // Performance metrics
  dollar_per_cpu_mark_single?: number | null;
  dollar_per_cpu_mark_single_adjusted?: number | null;
  dollar_per_cpu_mark_multi?: number | null;
  dollar_per_cpu_mark_multi_adjusted?: number | null;

  // Product metadata
  manufacturer?: string | null;
  series?: string | null;
  model_number?: string | null;
  form_factor?: string | null;

  // Ports
  ports_profile?: {
    id: number;
    ports: Array<{ port_type: string; quantity: number }>;
  } | null;
}
```

**Acceptance Criteria:**
- [ ] Two new columns added after Valuation
- [ ] DualMetricCell renders raw + adjusted values
- [ ] Columns sortable and filterable
- [ ] Tooltips explain metric meaning
- [ ] Responsive column widths (min 160px)

#### 4.2 Add Product Metadata Columns

**Add to column definitions:**

```typescript
{
  id: 'manufacturer',
  header: 'Manufacturer',
  accessorKey: 'manufacturer',
  cell: ({ getValue }) => {
    const val = getValue() as string | null;
    return <span className="text-sm">{val || "—"}</span>;
  },
  meta: {
    tooltip: 'PC manufacturer or builder',
    filterType: 'multi-select',
    options: [
      { label: 'Dell', value: 'Dell' },
      { label: 'HP', value: 'HP' },
      { label: 'Lenovo', value: 'Lenovo' },
      { label: 'Apple', value: 'Apple' },
      { label: 'ASUS', value: 'ASUS' },
      { label: 'Acer', value: 'Acer' },
      { label: 'MSI', value: 'MSI' },
      { label: 'Custom Build', value: 'Custom Build' },
      { label: 'Other', value: 'Other' },
    ],
  },
  enableSorting: true,
  enableResizing: true,
  size: 140,
},
{
  id: 'form_factor',
  header: 'Form Factor',
  accessorKey: 'form_factor',
  cell: ({ getValue }) => {
    const val = getValue() as string | null;
    return <span className="text-sm">{val || "—"}</span>;
  },
  meta: {
    tooltip: 'PC form factor classification',
    filterType: 'multi-select',
    options: [
      { label: 'Desktop', value: 'Desktop' },
      { label: 'Laptop', value: 'Laptop' },
      { label: 'Server', value: 'Server' },
      { label: 'Mini-PC', value: 'Mini-PC' },
      { label: 'All-in-One', value: 'All-in-One' },
      { label: 'Other', value: 'Other' },
    ],
  },
  enableSorting: true,
  enableResizing: true,
  size: 120,
},
{
  id: 'ports',
  header: 'Ports',
  accessorFn: (row) => row.ports_profile?.ports || [],
  cell: ({ row }) => (
    <PortsDisplay ports={row.original.ports_profile?.ports || []} />
  ),
  meta: {
    tooltip: 'Connectivity ports',
    description: 'Available ports and quantities',
  },
  enableSorting: false,
  enableResizing: true,
  size: 200,
},
```

**Acceptance Criteria:**
- [ ] Manufacturer column with multi-select filter
- [ ] Form factor column with multi-select filter
- [ ] Ports column with compact display + popover
- [ ] Null values display "—"
- [ ] Columns editable inline (use EditableCell pattern)

#### 4.3 Integrate Valuation Mode Toggle

**Update header section:**

```typescript
<CardHeader className="space-y-4">
  <div className="flex flex-wrap items-center justify-between gap-3">
    <div className="space-y-1">
      <h2 className="text-2xl font-semibold tracking-tight">Listings workspace</h2>
      <p className="text-sm text-muted-foreground">
        {valuationMode === 'base'
          ? 'Showing base prices (no deductions)'
          : 'Showing adjusted prices (after RAM/storage deductions)'
        }
      </p>
    </div>
    <div className="flex items-center gap-3">
      <ValuationModeToggle value={valuationMode} onChange={setValuationMode} />
      <Button asChild size="sm">
        <Link href="/listings/new">Add listing</Link>
      </Button>
    </div>
  </div>
  {/* ... rest of header ... */}
</CardHeader>
```

**Update Valuation column to respect mode:**

```typescript
{
  header: 'Valuation',
  accessorKey: valuationMode === 'base' ? 'price_usd' : 'adjusted_price_usd',
  cell: ({ row }) => {
    if (valuationMode === 'base') {
      return <span className="font-medium">{formatCurrency(row.original.price_usd)}</span>;
    }

    // Adjusted mode (existing ValuationCell)
    return (
      <ValuationCell
        adjustedPrice={row.original.adjusted_price_usd}
        listPrice={row.original.price_usd}
        thresholds={thresholds}
        onDetailsClick={() => {
          setSelectedListingForBreakdown({ /* ... */ });
          setBreakdownModalOpen(true);
        }}
      />
    );
  },
  // ... rest of config
}
```

**Acceptance Criteria:**
- [ ] Toggle controls which price displayed in Valuation column
- [ ] Base mode: Shows price_usd with neutral styling
- [ ] Adjusted mode: Shows adjusted_price_usd with delta badges
- [ ] Description updates based on mode
- [ ] Performance metrics use correct price (base vs adjusted)

---

## Phase 5: Form Enhancements

**Duration:** 2 days
**Dependencies:** Phase 4 complete

### Tasks

#### 5.1 Update Listing Form with New Fields

**File:** `apps/web/app/listings/new/page.tsx` (or edit form component)

**Add product metadata fields:**

```typescript
<FormField label="Manufacturer" name="manufacturer">
  <select
    value={manufacturer}
    onChange={(e) => setManufacturer(e.target.value)}
    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
  >
    <option value="">Select manufacturer...</option>
    <option value="Dell">Dell</option>
    <option value="HP">HP</option>
    <option value="Lenovo">Lenovo</option>
    <option value="Apple">Apple</option>
    <option value="ASUS">ASUS</option>
    <option value="Acer">Acer</option>
    <option value="MSI">MSI</option>
    <option value="Custom Build">Custom Build</option>
    <option value="Other">Other</option>
  </select>
</FormField>

<FormField label="Series" name="series">
  <Input
    value={series}
    onChange={(e) => setSeries(e.target.value)}
    placeholder="e.g., OptiPlex, ThinkCentre, Mac Studio"
  />
</FormField>

<FormField label="Model Number" name="model_number">
  <Input
    value={modelNumber}
    onChange={(e) => setModelNumber(e.target.value)}
    placeholder="e.g., 7090, M75q, A2615"
  />
</FormField>

<FormField label="Form Factor" name="form_factor">
  <select
    value={formFactor}
    onChange={(e) => setFormFactor(e.target.value)}
    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
  >
    <option value="">Select form factor...</option>
    <option value="Desktop">Desktop</option>
    <option value="Laptop">Laptop</option>
    <option value="Server">Server</option>
    <option value="Mini-PC">Mini-PC</option>
    <option value="All-in-One">All-in-One</option>
    <option value="Other">Other</option>
  </select>
</FormField>
```

**Integrate CPU Info Panel:**

```typescript
<FormField label="CPU" name="cpu_id">
  <ComboBox
    options={cpuOptions}
    value={cpuId}
    onChange={async (id) => {
      setCpuId(id);
      // Fetch full CPU data for info panel
      if (id) {
        const cpu = await apiFetch<CpuResponse>(`/v1/catalog/cpus/${id}`);
        setSelectedCpu(cpu);
      } else {
        setSelectedCpu(null);
      }
    }}
  />
</FormField>

{selectedCpu && <CpuInfoPanel cpu={selectedCpu} />}
```

**Integrate Ports Builder:**

```typescript
<FormField
  label="Ports"
  name="ports"
  description="Specify connectivity options"
>
  <PortsBuilder value={ports} onChange={setPorts} />
</FormField>
```

**Update submit handler:**

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  const payload = {
    // ... existing fields ...
    manufacturer,
    series,
    model_number: modelNumber,
    form_factor: formFactor,
  };

  // Create/update listing
  const listing = await apiFetch<ListingResponse>('/v1/listings', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  // Update ports if provided
  if (ports.length > 0) {
    await apiFetch(`/v1/listings/${listing.id}/ports`, {
      method: 'POST',
      body: JSON.stringify({ ports }),
    });
  }

  // Trigger metric calculation
  await apiFetch(`/v1/listings/${listing.id}/recalculate-metrics`, {
    method: 'POST',
  });

  router.push('/listings');
};
```

**Acceptance Criteria:**
- [ ] Form includes manufacturer, series, model, form factor fields
- [ ] CPU selection shows info panel below
- [ ] Ports builder integrated
- [ ] Submit handler saves all fields
- [ ] Metrics auto-calculated after save
- [ ] Validation prevents incomplete submissions

#### 5.2 Create API Client Methods

**File:** `apps/web/lib/api/listings.ts` (new or update existing)

```typescript
export interface CpuResponse {
  id: number;
  name: string;
  manufacturer: string;
  cpu_mark_single: number | null;
  cpu_mark_multi: number | null;
  igpu_mark: number | null;
  tdp_w: number | null;
  release_year: number | null;
  igpu_model: string | null;
}

export interface ListingResponse {
  id: number;
  // ... existing fields ...
  dollar_per_cpu_mark_single: number | null;
  dollar_per_cpu_mark_single_adjusted: number | null;
  dollar_per_cpu_mark_multi: number | null;
  dollar_per_cpu_mark_multi_adjusted: number | null;
  manufacturer: string | null;
  series: string | null;
  model_number: string | null;
  form_factor: string | null;
  cpu: CpuResponse | null;
  ports_profile: {
    id: number;
    ports: Array<{ port_type: string; quantity: number }>;
  } | null;
}

export async function getCpu(cpuId: number): Promise<CpuResponse> {
  return apiFetch<CpuResponse>(`/v1/catalog/cpus/${cpuId}`);
}

export async function recalculateListingMetrics(listingId: number): Promise<ListingResponse> {
  return apiFetch<ListingResponse>(`/v1/listings/${listingId}/recalculate-metrics`, {
    method: 'POST',
  });
}

export async function updateListingPorts(
  listingId: number,
  ports: Array<{ port_type: string; quantity: number }>
): Promise<void> {
  await apiFetch(`/v1/listings/${listingId}/ports`, {
    method: 'POST',
    body: JSON.stringify({ ports }),
  });
}
```

**Acceptance Criteria:**
- [ ] Type-safe API methods created
- [ ] Methods return properly typed responses
- [ ] Error handling included
- [ ] Used by form components

---

## Phase 6: Data Population & Migration

**Duration:** 2-3 days
**Dependencies:** Phase 5 complete

### Tasks

#### 6.1 Import PassMark Benchmark Data

**Strategy:** Manual CSV import (PassMark API is paid, CSV is free via web scraping or purchase)

**Data Sources:**
- PassMark Single-Thread: https://www.cpubenchmark.net/singleThread.html
- PassMark Multi-Thread: https://www.cpubenchmark.net/CPU_mega_page.html
- PassMark iGPU: https://www.videocardbenchmark.net/GPU_mega_page.html

**CSV Format:**
```csv
cpu_name,cpu_mark_single,cpu_mark_multi,igpu_model,igpu_mark,tdp_w,release_year
"Intel Core i7-12700K",3985,35864,"Intel UHD 770",1850,125,2021
"AMD Ryzen 7 5800X",3605,30862,"",0,105,2020
```

**Import Script:**

**File:** `scripts/import_passmark_data.py`

```python
import csv
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dealbrain_api.models.core import Cpu
from dealbrain_api.settings import get_settings

async def import_passmark_csv(csv_path: str):
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            updated_count = 0

            for row in reader:
                cpu_name = row['cpu_name'].strip()

                # Find CPU by name (case-insensitive)
                stmt = select(Cpu).where(func.lower(Cpu.name) == func.lower(cpu_name))
                result = await session.execute(stmt)
                cpu = result.scalar_one_or_none()

                if cpu:
                    cpu.cpu_mark_single = int(row['cpu_mark_single']) if row['cpu_mark_single'] else None
                    cpu.cpu_mark_multi = int(row['cpu_mark_multi']) if row['cpu_mark_multi'] else None
                    cpu.igpu_model = row['igpu_model'] if row['igpu_model'] else None
                    cpu.igpu_mark = int(row['igpu_mark']) if row['igpu_mark'] else None
                    cpu.tdp_w = int(row['tdp_w']) if row['tdp_w'] else None
                    cpu.release_year = int(row['release_year']) if row['release_year'] else None
                    updated_count += 1
                else:
                    print(f"CPU not found: {cpu_name}")

            await session.commit()
            print(f"Updated {updated_count} CPUs with PassMark data")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_passmark_data.py <csv_file>")
        sys.exit(1)

    asyncio.run(import_passmark_csv(sys.argv[1]))
```

**Commands:**
```bash
# Run import
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
```

**Acceptance Criteria:**
- [ ] CSV import script created
- [ ] PassMark data sourced (web scrape or purchase)
- [ ] Script matches CPUs by name (case-insensitive)
- [ ] 95%+ CPU coverage achieved
- [ ] Unmatched CPUs logged for manual review

#### 6.2 Bulk Recalculate Listing Metrics

**Script:**

**File:** `scripts/recalculate_all_metrics.py`

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dealbrain_api.settings import get_settings
from dealbrain_api.services.listings import bulk_update_listing_metrics

async def recalculate_all():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Recalculating metrics for all listings...")
        count = await bulk_update_listing_metrics(session, listing_ids=None)
        print(f"Updated {count} listings")

if __name__ == "__main__":
    asyncio.run(recalculate_all())
```

**Commands:**
```bash
poetry run python scripts/recalculate_all_metrics.py
```

**Alternative: Background Job (Celery)**

If listing count > 1000, use Celery task:

```python
# apps/api/dealbrain_api/tasks/metrics.py

@celery_app.task
def recalculate_all_metrics_task():
    asyncio.run(recalculate_all())
```

**Acceptance Criteria:**
- [ ] Script recalculates all listing metrics
- [ ] Handles large datasets (10k+ listings)
- [ ] Progress logging every 100 listings
- [ ] Completion summary logged

#### 6.3 Seed Sample Data

**File:** `apps/api/dealbrain_api/seeds.py`

**Add to seed script:**

```python
# Seed listings with new metadata fields
async def seed_listings_metadata(session: AsyncSession):
    listings = [
        {
            "title": "Dell OptiPlex 7090 SFF",
            "manufacturer": "Dell",
            "series": "OptiPlex",
            "model_number": "7090",
            "form_factor": "Desktop",
            "price_usd": 699.99,
            "cpu_id": 1,  # Intel i7-12700
        },
        {
            "title": "Lenovo ThinkCentre M75q Gen 2",
            "manufacturer": "Lenovo",
            "series": "ThinkCentre",
            "model_number": "M75q",
            "form_factor": "Mini-PC",
            "price_usd": 549.99,
            "cpu_id": 2,  # AMD Ryzen 7 5800
        },
        # ... more examples
    ]

    for data in listings:
        listing = Listing(**data)
        session.add(listing)

    await session.commit()

    # Recalculate metrics
    await bulk_update_listing_metrics(session, listing_ids=None)
```

**Commands:**
```bash
make seed
```

**Acceptance Criteria:**
- [ ] Seed script includes metadata fields
- [ ] Sample listings span all form factors
- [ ] Multiple manufacturers represented
- [ ] Metrics auto-calculated on seed

---

## Phase 7: Testing & Quality Assurance

**Duration:** 2-3 days
**Dependencies:** Phase 6 complete

### Tasks

#### 7.1 Unit Tests

**Backend Tests:**

```bash
# Test listing calculation service
poetry run pytest tests/test_listing_metrics.py -v

# Test ports service
poetry run pytest tests/test_ports_service.py -v

# Test API endpoints
poetry run pytest tests/api/test_listings.py -v
```

**Frontend Component Tests:**

```bash
# Test DualMetricCell
pnpm --filter web test dual-metric-cell.test.tsx

# Test CPUInfoPanel
pnpm --filter web test cpu-info-panel.test.tsx

# Test PortsBuilder
pnpm --filter web test ports-builder.test.tsx
```

**Acceptance Criteria:**
- [ ] Backend unit tests >90% coverage
- [ ] Frontend component tests passing
- [ ] Edge cases covered (null CPU, missing data)
- [ ] All async operations tested

#### 7.2 Integration Tests

**End-to-End Flows:**

1. **Create Listing with Full Metadata:**
   - Fill all fields (manufacturer, series, model, CPU, ports)
   - Submit form
   - Verify listing created with metrics calculated
   - Verify ports saved correctly

2. **Update Valuation → Metrics Recalculate:**
   - Create valuation rule (e.g., deduct $100 for RAM)
   - Apply to listing
   - Verify adjusted_price updated
   - Verify adjusted metrics recalculated

3. **Toggle Valuation Mode:**
   - Switch from adjusted → base
   - Verify Valuation column shows price_usd
   - Verify delta badges hidden
   - Switch back to adjusted
   - Verify ValuationCell restored

**Acceptance Criteria:**
- [ ] All critical flows tested end-to-end
- [ ] Data persistence verified
- [ ] UI state transitions smooth
- [ ] No console errors

#### 7.3 Performance Testing

**Load Tests:**

```bash
# Test bulk metric calculation (1000 listings)
time poetry run python scripts/recalculate_all_metrics.py

# Test listings table render (500 rows)
# Measure initial render + scroll performance
```

**Targets:**
- Bulk recalculation: <10 seconds for 1000 listings
- Table initial render: <2 seconds for 500 rows
- Scroll FPS: >30 FPS with 500+ rows

**Optimizations if needed:**
- Add database indexes
- Implement React.memo on table cells
- Use virtual scrolling (react-window)

**Acceptance Criteria:**
- [ ] Performance targets met
- [ ] No memory leaks detected
- [ ] Optimizations documented

#### 7.4 Accessibility Audit

**Tools:**
- Lighthouse (accessibility score >90)
- axe DevTools (0 violations)
- Manual keyboard navigation test

**Checklist:**
- [ ] All interactive elements keyboard-accessible
- [ ] ARIA labels on custom controls
- [ ] Color contrast WCAG AA compliant
- [ ] Screen reader announces changes (valuation mode toggle)
- [ ] Focus indicators visible

**Acceptance Criteria:**
- [ ] Lighthouse score ≥90
- [ ] axe DevTools: 0 critical violations
- [ ] Keyboard navigation complete
- [ ] Screen reader compatibility verified

---

## Phase 8: Documentation & Rollout

**Duration:** 1-2 days
**Dependencies:** Phase 7 complete

### Tasks

#### 8.1 Update Documentation

**Files to Update:**

1. **`CLAUDE.md`** — Add new features to Key Features section
2. **`docs/architecture.md`** — Update data model section
3. **`docs/user-guide/listings.md`** (new) — User guide for new fields
4. **`docs/api/README.md`** (new) — API endpoint documentation

**User Guide Content:**

```markdown
# Listings Guide

## Performance Metrics

### Dual CPU Mark Columns

The Listings table now shows **two** CPU performance efficiency metrics:

- **$/CPU Mark (Single):** Cost per PassMark single-thread point
  - Best for: Gaming, single-core workloads
  - Lower is better

- **$/CPU Mark (Multi):** Cost per PassMark multi-thread point
  - Best for: Video editing, 3D rendering, server workloads
  - Lower is better

Each metric displays **two values**:
- **Top (larger):** Raw value using list price
- **Bottom (smaller, colored):** Adjusted value using price after RAM/storage deductions

**Green text with ↓%** indicates improvement (better value after adjustments).

### Valuation Mode Toggle

Switch between **Base Price** and **Adjusted Price** views:

- **Base Price:** Shows original listing price with no deductions
- **Adjusted Price:** Shows price after component deductions (default)

Your selection persists across sessions.

## Product Metadata

### Manufacturer, Series, Model

Capture product lineage for better categorization:
- **Manufacturer:** Dell, HP, Lenovo, etc.
- **Series:** OptiPlex, ThinkCentre, etc.
- **Model Number:** 7090, M75q, etc.

All fields are optional but recommended for inventory management.

### Form Factor

Classify by hardware type:
- Desktop, Laptop, Server, Mini-PC, All-in-One, Other

Used for filtering and reporting.

### Ports

Specify connectivity options using the Ports builder:
1. Click "Add Port"
2. Select port type (USB-A, HDMI, etc.)
3. Enter quantity (1-16)
4. Repeat for additional ports

Ports display compactly in the table (e.g., "3× USB-A  2× HDMI").
Click to see full breakdown.

## CPU Information Panel

When you select a CPU, the info panel shows:
- PassMark single/multi-thread scores
- TDP (power consumption)
- Release year
- Integrated GPU (model + G3D score)

This data auto-populates from the CPU catalog.
```

**Acceptance Criteria:**
- [ ] CLAUDE.md updated
- [ ] Architecture docs updated
- [ ] User guide created
- [ ] API docs generated (OpenAPI)
- [ ] Migration guide for existing data

#### 8.2 Staged Rollout

**Week 1: Internal Testing**
- Deploy to staging environment
- Test with seed data
- Gather team feedback
- Fix critical bugs

**Week 2: Beta Release**
- Enable for 10% of users (feature flag)
- Monitor performance metrics
- Collect user feedback
- Address issues

**Week 3: Full Release**
- Enable for 100% of users
- Announce in changelog
- Monitor error rates
- Prepare hotfix plan

**Feature Flag Implementation:**

```typescript
// apps/web/lib/feature-flags.ts

export function useDualCpuMarks() {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    // Check feature flag from API or localStorage
    const isEnabled = localStorage.getItem('feature_dual_cpu_marks') === 'true';
    setEnabled(isEnabled);
  }, []);

  return enabled;
}
```

**Usage:**

```typescript
const dualCpuMarksEnabled = useDualCpuMarks();

{dualCpuMarksEnabled && (
  <>
    <Column id="dollar_per_cpu_mark_single" ... />
    <Column id="dollar_per_cpu_mark_multi" ... />
  </>
)}
```

**Acceptance Criteria:**
- [ ] Staging deployment successful
- [ ] Beta rollout at 10% completed
- [ ] User feedback collected (>20 responses)
- [ ] Full rollout at 100%
- [ ] Changelog published

#### 8.3 Monitoring & Alerts

**Metrics to Track:**

1. **Performance:**
   - Metric calculation time (P95 < 100ms)
   - Listings table render time (P95 < 3s)
   - API response times (P95 < 500ms)

2. **Usage:**
   - % listings with CPU assigned
   - % listings with manufacturer/form factor
   - Valuation mode distribution (base vs adjusted)

3. **Errors:**
   - Metric calculation failures
   - API 500 errors
   - Frontend JS errors

**Grafana Dashboards:**

```bash
# Import dashboard config
curl -X POST http://localhost:3021/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @infra/grafana/dashboards/listings-metrics.json
```

**Alerts:**

```yaml
# infra/prometheus/alerts.yml

- alert: HighMetricCalculationTime
  expr: histogram_quantile(0.95, rate(listing_metric_calculation_duration_seconds_bucket[5m])) > 0.5
  for: 5m
  annotations:
    summary: "Metric calculation taking >500ms (P95)"

- alert: HighAPIErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "API error rate >5%"
```

**Acceptance Criteria:**
- [ ] Grafana dashboards created
- [ ] Prometheus alerts configured
- [ ] Error tracking integrated (Sentry/Rollbar)
- [ ] On-call rotation notified

---

## Dependencies & Prerequisites

### External Dependencies

1. **PassMark Benchmark Data**
   - Source: Web scraping or CSV purchase
   - Format: CSV with cpu_name, scores, TDP, year
   - Update frequency: Monthly

2. **Database Capacity**
   - Additional columns: 8 per listing (4 metrics + 4 metadata)
   - Estimated size increase: ~5% for 10k listings
   - Index overhead: ~2% additional

### Internal Dependencies

1. **Existing Features:**
   - Valuation rules system (adjusted_price calculation)
   - CPU/GPU catalog (catalog endpoints)
   - Custom fields infrastructure (EntityField)

2. **Library Versions:**
   - SQLAlchemy ≥2.0 (for Mapped typing)
   - React ≥18 (for memo/hooks)
   - TanStack Table ≥8 (for column definitions)

### Team Dependencies

1. **Backend Developer:**
   - Implement calculation services
   - Create API endpoints
   - Write migration scripts

2. **Frontend Developer:**
   - Build UI components
   - Integrate with API
   - Implement state management

3. **Data Engineer:**
   - Source PassMark data
   - Create import scripts
   - Validate data quality

4. **QA Engineer:**
   - Write test plans
   - Execute manual tests
   - Validate accessibility

---

## Risk Assessment

### Technical Risks

1. **PassMark Data Availability**
   - **Risk:** Data source unavailable or incomplete
   - **Mitigation:** Multiple sources (web scrape + manual entry), graceful null handling
   - **Impact:** Medium | **Likelihood:** Low

2. **Performance Degradation**
   - **Risk:** Metric calculations slow down listing updates
   - **Mitigation:** Async background jobs, database indexing, caching
   - **Impact:** High | **Likelihood:** Medium

3. **Data Migration Complexity**
   - **Risk:** Bulk recalculation fails for large datasets
   - **Mitigation:** Chunked processing, retry logic, progress tracking
   - **Impact:** Medium | **Likelihood:** Low

### Product Risks

1. **User Confusion (Dual Metrics)**
   - **Risk:** Users don't understand single vs multi-thread
   - **Mitigation:** Clear tooltips, user guide, onboarding tooltips
   - **Impact:** Medium | **Likelihood:** Medium

2. **Feature Bloat**
   - **Risk:** Too many columns overwhelm table UI
   - **Mitigation:** Column visibility controls, default hidden columns, presets
   - **Impact:** Low | **Likelihood:** Low

3. **Low Adoption (Ports Field)**
   - **Risk:** Users skip optional ports field
   - **Mitigation:** Show value in reports, make filterable, auto-suggest common configs
   - **Impact:** Low | **Likelihood:** Medium

---

## Success Metrics (30 Days Post-Launch)

### Adoption Metrics

- [ ] **Data Completeness:**
  - 80%+ listings have CPU assigned (enables metrics)
  - 60%+ listings have manufacturer populated
  - 40%+ listings have form factor specified

- [ ] **Feature Usage:**
  - 70%+ users sort by dual CPU Mark metrics at least once
  - 50%+ users toggle valuation mode
  - 30%+ listings have ports data

### Performance Metrics

- [ ] **Backend:**
  - Metric calculation: P95 < 100ms
  - Bulk recalculation: <15s for 1000 listings
  - API response time: P95 < 500ms

- [ ] **Frontend:**
  - Listings table render: <2s for 500 rows
  - Column sorting: <200ms
  - Mode toggle: <100ms

### Quality Metrics

- [ ] **Stability:**
  - API error rate: <1%
  - Frontend JS errors: <0.1% of sessions
  - Zero P1 bugs in production

- [ ] **Accessibility:**
  - Lighthouse score: ≥90
  - axe violations: 0 critical
  - Keyboard nav complete

---

## Appendix

### A. Example API Flows

**Flow 1: Create Listing with Full Metadata**

```typescript
// Step 1: Create listing
const listing = await apiFetch('/v1/listings', {
  method: 'POST',
  body: JSON.stringify({
    title: "Dell OptiPlex 7090",
    price_usd: 699.99,
    cpu_id: 45,
    manufacturer: "Dell",
    series: "OptiPlex",
    model_number: "7090",
    form_factor: "Desktop",
  }),
});

// Step 2: Add ports
await apiFetch(`/v1/listings/${listing.id}/ports`, {
  method: 'POST',
  body: JSON.stringify({
    ports: [
      { port_type: "USB-A", quantity: 4 },
      { port_type: "HDMI", quantity: 1 },
    ],
  }),
});

// Step 3: Trigger metric calculation
const updated = await apiFetch(`/v1/listings/${listing.id}/recalculate-metrics`, {
  method: 'POST',
});

console.log(updated.dollar_per_cpu_mark_single); // 0.175
console.log(updated.dollar_per_cpu_mark_multi); // 0.0195
```

**Flow 2: Bulk Recalculate After Valuation Rule Update**

```typescript
// Step 1: Create valuation rule (deducts $150 for RAM)
const rule = await apiFetch('/v1/valuation-rules', {
  method: 'POST',
  body: JSON.stringify({
    name: "RAM Deduction",
    conditions: [{ field: "ram_gb", operator: "gte", value: 16 }],
    actions: [{ type: "deduct", value: 150 }],
  }),
});

// Step 2: Apply rule to listings (updates adjusted_price_usd)
await apiFetch(`/v1/valuation-rules/${rule.id}/apply`);

// Step 3: Bulk recalculate adjusted metrics
const result = await apiFetch('/v1/listings/bulk-recalculate-metrics', {
  method: 'POST',
  body: JSON.stringify({ listing_ids: null }), // null = all
});

console.log(result.message); // "Updated 1,234 listings"
```

### B. Database Query Examples

**Query 1: Find Best Single-Thread Value**

```sql
SELECT
  id,
  title,
  price_usd,
  dollar_per_cpu_mark_single,
  dollar_per_cpu_mark_single_adjusted
FROM listing
WHERE cpu_id IS NOT NULL
  AND dollar_per_cpu_mark_single_adjusted IS NOT NULL
ORDER BY dollar_per_cpu_mark_single_adjusted ASC
LIMIT 10;
```

**Query 2: Listings by Manufacturer + Form Factor**

```sql
SELECT
  manufacturer,
  form_factor,
  COUNT(*) as count,
  AVG(price_usd) as avg_price,
  AVG(dollar_per_cpu_mark_multi_adjusted) as avg_multi_value
FROM listing
WHERE manufacturer IS NOT NULL
  AND form_factor IS NOT NULL
GROUP BY manufacturer, form_factor
ORDER BY count DESC;
```

**Query 3: Port Coverage Analysis**

```sql
SELECT
  pp.id as profile_id,
  COUNT(DISTINCT l.id) as listing_count,
  json_agg(json_build_object('type', p.port_type, 'qty', p.quantity)) as ports
FROM listing l
JOIN ports_profile pp ON l.ports_profile_id = pp.id
JOIN port p ON p.port_profile_id = pp.id
GROUP BY pp.id
ORDER BY listing_count DESC;
```

---

**Implementation Plan Status:** Ready for Execution
**Next Steps:** Begin Phase 1 (Database Schema & Migrations)
