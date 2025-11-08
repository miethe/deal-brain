---
title: "Implementation Plan: Partial Data Extraction & Manual Field Population"
description: "Detailed phased implementation plan with agent assignments, dependencies, and acceptance criteria"
audience: [developers, ai-agents]
tags:
  - implementation
  - planning
  - agent-assignments
  - partial-imports
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: accepted
related:
  - /docs/project_plans/import-partial-data-manual-population/PRD.md
---

# Implementation Plan: Partial Data Extraction & Manual Field Population

## Overview

This document provides a detailed phased implementation plan for enabling partial data extraction and manual field population in the Deal Brain URL import system. Each phase includes specific tasks, agent assignments, dependencies, acceptance criteria, and estimated durations.

**Total Estimated Duration**: 8-11 days (excluding rollout)

**Phases**:
1. Backend - Schema & Database (2-3 days)
2. Backend - API & Services (2-3 days)
3. Frontend - Manual Population Modal (2-3 days)
4. Frontend - Real-Time UI Updates (2-3 days)
5. Integration & Testing (1-2 days)
6. Rollout & Monitoring (ongoing)

---

## Phase 1: Backend - Schema & Database Changes

**Duration**: 2-3 days
**Dependencies**: None (can start immediately)
**Risk Level**: Medium (database migration requires careful testing)

### Task 1.1: Update NormalizedListingSchema

**Agent**: `python-backend-engineer`
**File**: `packages/core/dealbrain_core/schemas/ingestion.py`
**Duration**: 2-3 hours

**Objective**: Update schema validation to support partial imports

**Changes Required**:
1. Update `validate_minimum_data()` validator to only require title
2. Add `quality` field (full/partial)
3. Add `extraction_metadata` field (dict tracking field sources)
4. Add `missing_fields` field (list of fields needing manual entry)

**Implementation**:
```python
class NormalizedListingSchema(DealBrainModel):
    # Existing fields unchanged
    title: str = Field(...)  # REQUIRED
    price: Decimal | None = Field(None, ...)  # OPTIONAL (already set)

    # NEW FIELDS
    quality: str = Field(
        default="full",
        pattern=r"^(full|partial)$",
        description="Data completeness indicator"
    )
    extraction_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Field provenance tracking"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of fields requiring manual entry"
    )

    @field_validator("price")
    @classmethod
    def validate_minimum_data(cls, price: Decimal | None, info) -> Decimal | None:
        """Only require title - price is fully optional."""
        if price is None:
            title = info.data.get("title")
            if not title or not str(title).strip():
                raise ValueError("Title is required for all imports")
        return price
```

**Acceptance Criteria**:
- [ ] Schema validates with `price=None` and `title="Test"`
- [ ] Schema rejects with `price=None` and `title=None`
- [ ] `quality` defaults to "full"
- [ ] `extraction_metadata` defaults to empty dict
- [ ] `missing_fields` defaults to empty list
- [ ] All existing tests pass

**Testing**:
```python
# tests/test_schemas.py
def test_normalized_listing_schema_optional_price():
    schema = NormalizedListingSchema(
        title="Test Listing",
        price=None,
        condition="used",
        marketplace="other"
    )
    assert schema.price is None
    assert schema.quality == "full"
```

---

### Task 1.2: Database Migration - Nullable Price

**Agent**: `data-layer-expert`
**File**: `apps/api/alembic/versions/0022_partial_import_support.py`
**Duration**: 3-4 hours

**Objective**: Make `listings.price_usd` nullable and add quality tracking

**Critical Decision**: This is an **irreversible migration** if partial imports exist in production. Plan for downgrade strategy.

**Migration Script**:
```python
"""Partial import support: nullable price and quality tracking

Revision ID: 0022
Revises: 0021
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 1. Make price_usd nullable
    op.alter_column(
        'listing',
        'price_usd',
        existing_type=sa.Float(),
        nullable=True
    )

    # 2. Add quality column
    op.add_column(
        'listing',
        sa.Column('quality', sa.String(20), nullable=False, server_default='full')
    )

    # 3. Add extraction_metadata JSON
    op.add_column(
        'listing',
        sa.Column('extraction_metadata', sa.JSON(), nullable=False, server_default='{}')
    )

    # 4. Add missing_fields JSON array
    op.add_column(
        'listing',
        sa.Column('missing_fields', sa.JSON(), nullable=False, server_default='[]')
    )


def downgrade():
    # WARNING: This will DELETE partial imports if they exist
    op.execute("DELETE FROM listing WHERE price_usd IS NULL")

    op.drop_column('listing', 'missing_fields')
    op.drop_column('listing', 'extraction_metadata')
    op.drop_column('listing', 'quality')

    op.alter_column(
        'listing',
        'price_usd',
        existing_type=sa.Float(),
        nullable=False
    )
```

**Acceptance Criteria**:
- [ ] Migration runs successfully in dev environment
- [ ] Migration runs successfully in staging environment
- [ ] Can create listing with `price_usd=NULL`
- [ ] Existing listings have `quality='full'` after migration
- [ ] Downgrade deletes partial imports and restores NOT NULL constraint
- [ ] No data loss for listings with prices

**Testing**:
```bash
# Apply migration
make migrate

# Test in Python shell
poetry run python
>>> from apps.api.dealbrain_api.models.core import Listing
>>> from apps.api.dealbrain_api.db import session_scope
>>> async with session_scope() as session:
...     listing = Listing(title="Test", price_usd=None, condition="used", marketplace="other", quality="partial")
...     session.add(listing)
...     await session.commit()
```

---

### Task 1.3: Update Adapter Base Class

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/adapters/base.py`
**Duration**: 2-3 hours

**Objective**: Remove price requirement from adapter validation

**Changes**:
```python
class BaseAdapter(ABC):
    def _validate_response(self, data: dict[str, Any]) -> None:
        """Validate minimum viable data - only title required."""

        # BEFORE: required_fields = ["title", "price"]
        # AFTER:
        required_fields = ["title"]

        missing = [f for f in required_fields if f not in data or not data[f]]

        if missing:
            raise AdapterException(
                AdapterError.INVALID_SCHEMA,
                f"Missing required fields: {', '.join(missing)}",
            )

        # Track extraction quality
        has_price = bool(data.get("price"))

        if not has_price:
            logger.warning(f"[{self.name}] No price extracted - will create partial import")
            data["quality"] = "partial"
            data["missing_fields"] = ["price"]

            # Track what WAS extracted
            data["extraction_metadata"] = {
                k: "extracted"
                for k, v in data.items()
                if v and k not in ["quality", "missing_fields", "extraction_metadata"]
            }
            data["extraction_metadata"]["price"] = "extraction_failed"
        else:
            data["quality"] = "full"
            data["missing_fields"] = []
            data["extraction_metadata"] = {
                k: "extracted"
                for k, v in data.items()
                if v and k not in ["quality", "missing_fields", "extraction_metadata"]
            }
```

**Acceptance Criteria**:
- [ ] Adapter accepts response with title only
- [ ] Adapter sets `quality="partial"` when price missing
- [ ] Adapter sets `missing_fields=["price"]` when price missing
- [ ] Adapter tracks extraction_metadata correctly
- [ ] All existing adapter tests pass

**Testing**:
```python
# tests/test_adapters.py
async def test_adapter_accepts_partial_data():
    adapter = JsonLdAdapter()
    data = {
        "title": "Dell OptiPlex 7090",
        "condition": "refurb",
        "marketplace": "amazon",
        "price": None
    }

    adapter._validate_response(data)  # Should not raise

    assert data["quality"] == "partial"
    assert "price" in data["missing_fields"]
    assert data["extraction_metadata"]["title"] == "extracted"
    assert data["extraction_metadata"]["price"] == "extraction_failed"
```

---

### Task 1.4: Update ImportSession Model

**Agent**: `data-layer-expert`
**File**: `apps/api/dealbrain_api/models/core.py`
**Duration**: 2 hours

**Objective**: Add bulk job tracking to ImportSession model

**Migration**: `apps/api/alembic/versions/0023_bulk_job_tracking.py`

```python
def upgrade():
    # Add bulk job ID for linking related imports
    op.add_column(
        'import_session',
        sa.Column('bulk_job_id', sa.String(36), nullable=True, index=True)
    )

    # Add quality tracking
    op.add_column(
        'import_session',
        sa.Column('quality', sa.String(20), nullable=True)
    )

    # Add listing reference
    op.add_column(
        'import_session',
        sa.Column('listing_id', sa.Integer, sa.ForeignKey('listing.id'), nullable=True)
    )

    # Add completion timestamp
    op.add_column(
        'import_session',
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Add index for bulk job queries
    op.create_index('ix_import_session_bulk_job_id', 'import_session', ['bulk_job_id'])
```

**Model Changes**:
```python
class ImportSession(Base, TimestampMixin):
    # ... existing fields ...

    # NEW FIELDS
    bulk_job_id: Mapped[str | None] = mapped_column(String(36), index=True)
    quality: Mapped[str | None] = mapped_column(String(20))
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listing.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

**Acceptance Criteria**:
- [ ] Migration runs successfully
- [ ] Can query ImportSession by bulk_job_id efficiently
- [ ] Can link ImportSession to created Listing
- [ ] All existing tests pass

---

## Phase 2: Backend - API & Services

**Duration**: 2-3 days
**Dependencies**: Phase 1 complete (migrations applied)
**Risk Level**: Low (pure business logic)

### Task 2.1: Update ListingsService for Partial Imports

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/services/listings.py`
**Duration**: 4-5 hours

**Objective**: Support creating listings without price, skip metrics when price missing

**Method 1: Create from Ingestion**
```python
async def create_from_ingestion(
    self,
    normalized_data: NormalizedListingSchema,
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """
    Create listing from normalized ingestion data.
    Supports partial imports - price may be None.
    """
    listing = Listing(
        title=normalized_data.title,
        price_usd=normalized_data.price,  # May be None
        condition=normalized_data.condition,
        marketplace=normalized_data.marketplace,
        vendor_item_id=normalized_data.vendor_item_id,
        manufacturer=normalized_data.manufacturer,
        model_number=normalized_data.model_number,
        quality=normalized_data.quality or ("partial" if normalized_data.price is None else "full"),
        extraction_metadata=normalized_data.extraction_metadata or {},
        missing_fields=normalized_data.missing_fields or [],
        # ... other fields ...
    )

    # Only calculate metrics if price exists
    if listing.price_usd is not None:
        await self._apply_valuation_and_scoring(listing, session)
    else:
        logger.info(f"Listing '{listing.title}' created without price - metrics deferred")

    session.add(listing)
    await session.flush()
    return listing
```

**Method 2: Complete Partial Import** (NEW)
```python
async def complete_partial_import(
    self,
    listing_id: int,
    completion_data: dict[str, Any],
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """
    Complete a partial import by providing missing fields.

    Args:
        listing_id: Listing to complete
        completion_data: Dict with missing fields (e.g., {"price": 299.99})
        user_id: User completing the import
        session: Database session

    Returns:
        Updated listing with metrics calculated

    Raises:
        ValueError: If listing not found or not partial
    """
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    if listing.quality != "partial":
        raise ValueError(f"Listing {listing_id} is not partial")

    # Update fields from completion data
    if "price" in completion_data:
        listing.price_usd = float(completion_data["price"])
        if not listing.extraction_metadata:
            listing.extraction_metadata = {}
        listing.extraction_metadata["price"] = "manual"

    # Remove from missing_fields
    listing.missing_fields = [
        f for f in (listing.missing_fields or [])
        if f not in completion_data
    ]

    # Update quality if all required fields present
    if not listing.missing_fields and listing.price_usd is not None:
        listing.quality = "full"

    # Calculate metrics now
    if listing.price_usd is not None:
        await self._apply_valuation_and_scoring(listing, session)

    await session.flush()
    return listing
```

**Acceptance Criteria**:
- [ ] Can create listing with price=None
- [ ] Metrics not calculated when price=None
- [ ] Can complete partial listing with price
- [ ] Metrics calculated after completion
- [ ] extraction_metadata tracks "manual" for user-entered fields
- [ ] quality updated to "full" after completion
- [ ] All existing tests pass

**Testing**:
```python
# tests/test_listings_service.py
async def test_create_partial_listing(session):
    service = ListingsService()
    normalized = NormalizedListingSchema(
        title="Dell OptiPlex",
        price=None,
        condition="refurb",
        marketplace="amazon",
        quality="partial",
        missing_fields=["price"]
    )

    listing = await service.create_from_ingestion(
        normalized_data=normalized,
        user_id="user123",
        session=session
    )

    assert listing.price_usd is None
    assert listing.quality == "partial"
    assert listing.adjusted_price_usd is None  # No metrics

async def test_complete_partial_import(session):
    # Create partial listing
    listing = Listing(
        title="Test PC",
        price_usd=None,
        quality="partial",
        missing_fields=["price"]
    )
    session.add(listing)
    await session.flush()

    # Complete it
    service = ListingsService()
    updated = await service.complete_partial_import(
        listing_id=listing.id,
        completion_data={"price": 299.99},
        user_id="user123",
        session=session
    )

    assert updated.price_usd == 299.99
    assert updated.quality == "full"
    assert updated.extraction_metadata["price"] == "manual"
    assert updated.adjusted_price_usd is not None  # Metrics calculated
```

---

### Task 2.2: Create Completion API Endpoint

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/api/listings.py`
**Duration**: 2-3 hours

**Objective**: Add PATCH endpoint for completing partial imports

**Endpoint**: `PATCH /api/v1/listings/{listing_id}/complete`

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.listings import ListingsService
from dealbrain_core.schemas.listings import ListingSchema

router = APIRouter()


class CompletePartialImportRequest(BaseModel):
    """Request schema for completing a partial import."""
    price: float = Field(..., gt=0, description="Listing price in USD")
    # Future: support other fields like condition, etc.


@router.patch("/api/v1/listings/{listing_id}/complete")
async def complete_partial_import(
    listing_id: int,
    request: CompletePartialImportRequest,
    session: AsyncSession = Depends(session_dependency),
    # current_user: dict = Depends(get_current_user),  # TODO: Add auth
) -> ListingSchema:
    """
    Complete a partial import by providing missing fields.

    This endpoint allows users to fill in missing data (typically price)
    for listings that were partially imported. After completion, the
    listing's quality is updated to "full" and metrics are calculated.

    Args:
        listing_id: ID of the partial listing to complete
        request: Completion data (price, etc.)
        session: Database session
        current_user: Authenticated user (TODO)

    Returns:
        Updated listing with metrics calculated

    Raises:
        404: Listing not found
        400: Listing is not partial or validation failed
    """
    service = ListingsService()

    try:
        updated_listing = await service.complete_partial_import(
            listing_id=listing_id,
            completion_data=request.model_dump(),
            user_id="system",  # TODO: Use current_user["id"]
            session=session,
        )
        await session.commit()
        return ListingSchema.model_validate(updated_listing)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Acceptance Criteria**:
- [ ] Endpoint validates price is positive
- [ ] Endpoint returns 400 if listing not partial
- [ ] Endpoint returns 404 if listing not found
- [ ] Endpoint returns 200 with updated listing on success
- [ ] Metrics calculated after completion
- [ ] Integration test passes

**Testing**:
```python
# tests/test_api_listings.py
async def test_complete_partial_import_endpoint(client, session):
    # Create partial listing
    listing = Listing(
        title="Test PC",
        price_usd=None,
        quality="partial",
        condition="used",
        marketplace="other"
    )
    session.add(listing)
    await session.commit()

    # Complete via API
    response = await client.patch(
        f"/api/v1/listings/{listing.id}/complete",
        json={"price": 299.99}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["price_usd"] == 299.99
    assert data["quality"] == "full"
```

---

### Task 2.3: Create Bulk Import Status Endpoint

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/api/ingestion.py`
**Duration**: 4-5 hours

**Objective**: Add status polling endpoint for bulk imports

**Endpoint**: `GET /api/v1/ingest/bulk/{bulk_job_id}/status`

```python
@router.get("/api/v1/ingest/bulk/{bulk_job_id}/status")
async def get_bulk_import_status(
    bulk_job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(session_dependency),
) -> BulkIngestionStatusResponse:
    """
    Poll bulk import job status with pagination.

    Returns overall job status and per-URL details including
    quality indicators (full/partial) and listing references.

    Args:
        bulk_job_id: Unique bulk job identifier
        offset: Pagination offset (default 0)
        limit: Pagination limit (default 20, max 100)
        session: Database session

    Returns:
        Bulk job status with per-row details
    """
    # Query all ImportSession records for this bulk_job_id
    stmt = (
        select(ImportSession)
        .where(ImportSession.bulk_job_id == bulk_job_id)
        .offset(offset)
        .limit(limit)
        .order_by(ImportSession.created_at)
    )
    result = await session.execute(stmt)
    sessions = result.scalars().all()

    # Count by status
    count_stmt = (
        select(
            ImportSession.status,
            ImportSession.quality,
            func.count()
        )
        .where(ImportSession.bulk_job_id == bulk_job_id)
        .group_by(ImportSession.status, ImportSession.quality)
    )
    count_result = await session.execute(count_stmt)
    counts = count_result.all()

    # Aggregate counts
    total_urls = sum(c[2] for c in counts)
    queued = sum(c[2] for c in counts if c[0] == "queued")
    running = sum(c[2] for c in counts if c[0] == "running")
    complete = sum(c[2] for c in counts if c[0] == "complete")
    partial = sum(c[2] for c in counts if c[1] == "partial")
    failed = sum(c[2] for c in counts if c[0] == "failed")

    # Determine overall status
    if queued + running > 0:
        overall_status = "running"
    elif failed == total_urls:
        overall_status = "failed"
    elif partial > 0:
        overall_status = "partial"
    else:
        overall_status = "complete"

    # Build per-row status
    per_row_status = [
        PerRowStatus(
            url=s.url or "",
            status=s.status,
            listing_id=s.listing_id,
            error=s.conflicts_json.get("error") if s.conflicts_json else None
        )
        for s in sessions
    ]

    return BulkIngestionStatusResponse(
        bulk_job_id=bulk_job_id,
        status=overall_status,
        total_urls=total_urls,
        completed=complete + partial + failed,
        success=complete,
        partial=partial,
        failed=failed,
        running=running,
        queued=queued,
        per_row_status=per_row_status,
        offset=offset,
        limit=limit,
        has_more=len(sessions) == limit
    )
```

**Acceptance Criteria**:
- [ ] Endpoint returns correct aggregated counts
- [ ] Endpoint paginates per_row_status correctly
- [ ] Endpoint identifies partial imports via quality field
- [ ] Endpoint returns listing_id for completed imports
- [ ] Integration test with 50+ URLs passes

**Testing**:
```python
async def test_bulk_import_status_endpoint(client, session):
    bulk_job_id = "test-bulk-123"

    # Create import sessions
    for i in range(5):
        s = ImportSession(
            filename=f"url_{i}",
            upload_path=f"https://example.com/{i}",
            url=f"https://example.com/{i}",
            bulk_job_id=bulk_job_id,
            status="complete" if i < 3 else "running",
            quality="partial" if i == 1 else "full",
            listing_id=100 + i if i < 3 else None
        )
        session.add(s)
    await session.commit()

    # Query status
    response = await client.get(f"/api/v1/ingest/bulk/{bulk_job_id}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["total_urls"] == 5
    assert data["success"] == 2  # i=0, i=2 (full)
    assert data["partial"] == 1  # i=1
    assert data["running"] == 2  # i=3, i=4
```

---

## Phase 3: Frontend - Manual Population Modal

**Duration**: 2-3 days
**Dependencies**: Phase 2 complete (API endpoints ready)
**Risk Level**: Low (UI implementation)

### Task 3.1: Create PartialImportModal Component

**Agent**: `ui-engineer`
**File**: `apps/web/components/imports/PartialImportModal.tsx`
**Duration**: 4-6 hours

**Objective**: Build accessible modal for completing partial imports

**Component Structure**:
```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle, AlertCircle } from "lucide-react";
import { useState } from "react";

interface PartialImportModalProps {
  listing: Listing;
  onComplete: () => void;
  onSkip: () => void;
}

export function PartialImportModal({ listing, onComplete, onSkip }: PartialImportModalProps) {
  const [price, setPrice] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    // Validate price
    const priceNum = parseFloat(price);
    if (!priceNum || priceNum <= 0) {
      setError("Price must be a positive number");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/listings/${listing.id}/complete`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: priceNum }),
      });

      if (!response.ok) throw new Error('Failed to complete import');

      onComplete();
    } catch (err) {
      setError('Failed to save listing. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={true} onOpenChange={onSkip}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Complete Import</DialogTitle>
          <DialogDescription>
            We extracted most data, but need your help with 1 field to complete this listing
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Extracted Data (Read-Only) */}
          <div className="border-l-4 border-green-500 pl-4 space-y-2">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              Extracted Data
            </h3>
            <div className="text-sm space-y-1">
              <p><strong>Title:</strong> {listing.title}</p>
              {listing.cpu?.name && <p><strong>CPU:</strong> {listing.cpu.name}</p>}
              {listing.ram_gb && <p><strong>RAM:</strong> {listing.ram_gb}GB</p>}
              {listing.primary_storage_gb && (
                <p><strong>Storage:</strong> {listing.primary_storage_gb}GB {listing.primary_storage_type}</p>
              )}
            </div>
          </div>

          {/* Missing Fields (Editable) */}
          <div className="border-l-4 border-yellow-400 pl-4 space-y-2">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600" />
              Complete These Fields
            </h3>

            <div className="space-y-2">
              <Label htmlFor="price">Price (USD) *</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                min="0"
                placeholder="299.99"
                value={price}
                onChange={(e) => {
                  setPrice(e.target.value);
                  setError("");
                }}
                className={error ? "border-red-500" : ""}
                autoFocus
              />
              {error && <p className="text-xs text-red-500">{error}</p>}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onSkip} disabled={isLoading}>
            Skip for Now
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? "Saving..." : "Save Listing"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

**Acceptance Criteria**:
- [ ] Modal renders with extracted data displayed read-only
- [ ] Price input auto-focuses on open
- [ ] Validates price is positive number
- [ ] Shows error message for invalid price
- [ ] Calls completion API on submit
- [ ] Shows loading state during submission
- [ ] Closes on successful completion
- [ ] Keyboard accessible (Tab, Enter, Esc)
- [ ] Screen reader announces sections correctly

**Testing**:
```typescript
// apps/web/components/imports/__tests__/PartialImportModal.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PartialImportModal } from '../PartialImportModal';

describe('PartialImportModal', () => {
  const mockListing = {
    id: 1,
    title: 'Dell OptiPlex 7090',
    cpu: { name: 'Intel Core i5-10500' },
    ram_gb: 8,
    quality: 'partial',
  };

  it('renders extracted data as read-only', () => {
    render(
      <PartialImportModal
        listing={mockListing}
        onComplete={vi.fn()}
        onSkip={vi.fn()}
      />
    );

    expect(screen.getByText('Dell OptiPlex 7090')).toBeInTheDocument();
    expect(screen.getByText(/Intel Core i5-10500/)).toBeInTheDocument();
  });

  it('validates price is positive', async () => {
    render(<PartialImportModal {...props} />);

    const input = screen.getByLabelText(/Price/);
    await userEvent.type(input, '-100');
    await userEvent.click(screen.getByText('Save Listing'));

    expect(screen.getByText(/must be a positive number/i)).toBeInTheDocument();
  });

  it('submits valid price', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );

    const onComplete = vi.fn();
    render(<PartialImportModal {...props} onComplete={onComplete} />);

    await userEvent.type(screen.getByLabelText(/Price/), '299.99');
    await userEvent.click(screen.getByText('Save Listing'));

    await waitFor(() => expect(onComplete).toHaveBeenCalled());
  });
});
```

---

### Task 3.2: Integrate Modal with Import Flow

**Agent**: `ui-engineer`
**File**: `apps/web/app/dashboard/import/page.tsx`
**Duration**: 2-3 hours

**Objective**: Auto-open modal when partial import completes

**Implementation**:
```typescript
'use client';

import { useState, useEffect } from 'react';
import { PartialImportModal } from '@/components/imports/PartialImportModal';
import { Listing } from '@/types/listings';

export default function ImportPage() {
  const [partialListing, setPartialListing] = useState<Listing | null>(null);

  // Listen for import completion events
  useEffect(() => {
    const handleImportComplete = (event: CustomEvent) => {
      const { listing, quality } = event.detail;

      if (quality === 'partial') {
        setPartialListing(listing);
      } else {
        // Show success toast for complete imports
        toast.success(`${listing.title} imported successfully`);
      }
    };

    window.addEventListener('import-complete', handleImportComplete as EventListener);
    return () => window.removeEventListener('import-complete', handleImportComplete as EventListener);
  }, []);

  return (
    <div>
      {/* Import form */}

      {partialListing && (
        <PartialImportModal
          listing={partialListing}
          onComplete={() => {
            setPartialListing(null);
            // Refresh listings grid
            queryClient.invalidateQueries(['listings']);
          }}
          onSkip={() => setPartialListing(null)}
        />
      )}
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Modal auto-opens when partial import completes
- [ ] Modal does not open for complete imports
- [ ] Closing modal preserves partial listing in database
- [ ] Completing modal refreshes listings grid
- [ ] Toast shown for complete imports

---

## Phase 4: Frontend - Real-Time UI Updates

**Duration**: 2-3 days
**Dependencies**: Phase 2 complete (status endpoint ready)
**Risk Level**: Low

### Task 4.1: Create Import Status Polling Hook

**Agent**: `ui-engineer`
**File**: `apps/web/hooks/useImportStatus.ts`
**Duration**: 3-4 hours

**Implementation**:
```typescript
import { useState, useEffect } from 'react';

interface BulkIngestionStatusResponse {
  bulk_job_id: string;
  status: string;
  total_urls: number;
  completed: number;
  success: number;
  partial: number;
  failed: number;
  running: number;
  queued: number;
  per_row_status: Array<{
    url: string;
    status: string;
    listing_id?: number;
    error?: string;
  }>;
}

export function useImportStatus(bulkJobId: string | null) {
  const [status, setStatus] = useState<BulkIngestionStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bulkJobId) return;

    setIsPolling(true);
    let pollInterval: NodeJS.Timeout;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/ingest/bulk/${bulkJobId}/status`);
        if (!response.ok) throw new Error('Failed to fetch status');

        const data = await response.json();
        setStatus(data);

        // Stop polling when all done
        if (data.queued === 0 && data.running === 0) {
          setIsPolling(false);
          clearInterval(pollInterval);
        }
      } catch (err) {
        setError(err.message);
        setIsPolling(false);
        clearInterval(pollInterval);
      }
    };

    // Initial poll
    poll();

    // Poll every 2 seconds
    pollInterval = setInterval(poll, 2000);

    return () => clearInterval(pollInterval);
  }, [bulkJobId]);

  return { status, isPolling, error };
}
```

**Acceptance Criteria**:
- [ ] Hook polls every 2 seconds when bulkJobId provided
- [ ] Hook stops polling when all jobs complete
- [ ] Hook handles errors gracefully
- [ ] Hook returns loading state
- [ ] Hook returns aggregated counts

---

### Task 4.2: Create Progress Indicator Component

**Agent**: `ui-engineer`
**File**: `apps/web/components/imports/BulkImportProgress.tsx`
**Duration**: 2-3 hours

**Implementation**:
```typescript
import { Progress } from "@/components/ui/progress";
import { CheckCircle, AlertCircle, XCircle } from "lucide-react";

interface BulkImportProgressProps {
  status: BulkIngestionStatusResponse;
}

export function BulkImportProgress({ status }: BulkImportProgressProps) {
  const completionPct = (status.completed / status.total_urls) * 100;

  return (
    <div className="mb-6 space-y-3">
      <div className="flex justify-between text-sm text-muted-foreground">
        <span className="font-medium">Import Progress</span>
        <span>
          {status.completed} of {status.total_urls} completed
        </span>
      </div>

      <Progress value={completionPct} className="h-2" />

      <div className="flex gap-6 text-xs">
        <span className="flex items-center gap-1.5">
          <CheckCircle className="w-3.5 h-3.5 text-green-600" />
          <span className="text-muted-foreground">
            {status.success} successful
          </span>
        </span>

        {status.partial > 0 && (
          <span className="flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-yellow-600" />
            <span className="text-muted-foreground">
              {status.partial} need completion
            </span>
          </span>
        )}

        {status.failed > 0 && (
          <span className="flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            <span className="text-muted-foreground">
              {status.failed} failed
            </span>
          </span>
        )}
      </div>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Shows completion percentage
- [ ] Shows breakdown: successful, partial, failed
- [ ] Updates in real-time as imports complete
- [ ] Accessible labels for screen readers

---

### Task 4.3: Create Toast Notifications

**Agent**: `ui-engineer`
**File**: `apps/web/components/imports/ImportToasts.tsx`
**Duration**: 2-3 hours

**Implementation**: Use existing toast system with import-specific messages

**Acceptance Criteria**:
- [ ] Toast appears when import completes
- [ ] Success variant for complete imports
- [ ] Warning variant for partial imports
- [ ] Error variant for failed imports
- [ ] Action button: "View" (complete), "Complete" (partial), "Retry" (failed)
- [ ] Auto-dismiss after 5 seconds
- [ ] Accessible announcements

---

## Phase 5: Integration & Testing

**Duration**: 1-2 days
**Dependencies**: Phases 1-4 complete
**Risk Level**: Low

### Task 5.1: End-to-End Testing

**Agent**: `python-backend-engineer` + `ui-engineer`
**Duration**: 1 day

**Test Scenarios**:
1. Single URL import with price → Complete import
2. Single URL import without price → Partial import → Modal opens → Complete
3. Bulk import (5 URLs, 2 partial) → Real-time updates → Complete partials
4. Abandoned partial import → Skip modal → Listing persists
5. Invalid price entry → Validation error → Retry

**E2E Test**:
```typescript
// tests/e2e/partial_import.spec.ts
test('partial import flow', async ({ page }) => {
  await page.goto('/dashboard/import');

  // Submit URL
  await page.fill('input[placeholder="Paste URL"]', 'https://amazon.com/no-price');
  await page.click('button:has-text("Import")');

  // Wait for modal
  await expect(page.locator('text=Complete Import')).toBeVisible({ timeout: 10000 });

  // View extracted data
  await expect(page.locator('text=Dell OptiPlex')).toBeVisible();

  // Fill price
  await page.fill('input[label*="Price"]', '299.99');
  await page.click('button:has-text("Save Listing")');

  // Verify listing in grid
  await expect(page.locator('text=Dell OptiPlex')).toBeVisible();
  await expect(page.locator('text=$299.99')).toBeVisible();
});
```

**Acceptance Criteria**:
- [ ] All E2E tests pass
- [ ] Performance acceptable (<3s for import)
- [ ] No console errors
- [ ] Accessibility audit passes

---

### Task 5.2: Migration Testing

**Agent**: `data-layer-expert`
**Duration**: 4 hours

**Objective**: Validate migrations in staging environment

**Steps**:
1. Backup staging database
2. Apply migrations 0022 and 0023
3. Create test partial import
4. Complete partial import via API
5. Verify data integrity
6. Test downgrade (in isolated environment)

**Acceptance Criteria**:
- [ ] Migrations apply cleanly
- [ ] No data loss
- [ ] Downgrade tested (in isolated env)
- [ ] Performance impact minimal (<10ms query overhead)

---

## Phase 6: Rollout & Monitoring

**Duration**: 2 weeks (phased rollout)
**Dependencies**: Phase 5 complete
**Risk Level**: Medium (production rollout)

### Task 6.1: Feature Flag Implementation

**Agent**: `python-backend-engineer`
**Duration**: 2-3 hours

**Implementation**:
```python
# apps/api/dealbrain_api/models/core.py
class ApplicationSettings(Base):
    # ... existing fields ...
    enable_partial_imports: Mapped[bool] = mapped_column(default=False)
```

**Guard Logic**:
```python
# Check feature flag before allowing partial imports
settings = await get_application_settings(session)
if not settings.enable_partial_imports:
    # Reject partial imports, require price
    if not data.get("price"):
        raise AdapterException(
            AdapterError.INVALID_SCHEMA,
            "Price required (partial imports disabled)"
        )
```

**Acceptance Criteria**:
- [ ] Feature flag stored in database
- [ ] Backend enforces flag
- [ ] Frontend hides modal if disabled
- [ ] Default value is False

---

### Task 6.2: Monitoring Setup

**Agent**: `python-backend-engineer`
**Duration**: 4-5 hours

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram

import_attempts = Counter(
    'import_attempts_total',
    'Total import attempts',
    ['marketplace', 'quality']
)

import_duration = Histogram(
    'import_duration_seconds',
    'Import duration',
    ['marketplace', 'quality']
)

partial_completions = Counter(
    'partial_import_completions_total',
    'Partial imports completed manually'
)
```

**Acceptance Criteria**:
- [ ] Metrics exported to Prometheus
- [ ] Grafana dashboard created
- [ ] Alerts configured for high failure rate
- [ ] Success rate dashboard shows partial + complete

---

### Task 6.3: Phased Rollout

**Duration**: 2 weeks

**Week 1: Internal + Beta (10% users)**
- Day 1-2: Enable for dev/staging
- Day 3-4: Enable for 5 beta users
- Day 5-7: Monitor metrics, collect feedback

**Week 2: Gradual Rollout**
- Day 8-10: Enable for 25% of users
- Day 11-13: Enable for 50% of users
- Day 14: Enable for 100% of users

**Acceptance Criteria**:
- [ ] No critical bugs reported
- [ ] Import success rate >70%
- [ ] Partial completion rate >60%
- [ ] Performance within acceptable range

---

## Dependencies & Sequencing

### Critical Path

```
Phase 1 (Schema & DB) → Phase 2 (API) → Phase 3 (Modal) → Phase 5 (Testing) → Phase 6 (Rollout)
                                     ↘ Phase 4 (Real-time) ↗
```

**Phases 3 and 4 can run in parallel** once Phase 2 is complete.

### Agent Coordination

**python-backend-engineer**:
- Phase 1: Tasks 1.1, 1.3
- Phase 2: All tasks
- Phase 5: Task 5.1
- Phase 6: Tasks 6.1, 6.2

**data-layer-expert**:
- Phase 1: Tasks 1.2, 1.4
- Phase 5: Task 5.2

**ui-engineer**:
- Phase 3: All tasks
- Phase 4: All tasks
- Phase 5: Task 5.1

---

## Risk Mitigation

### Database Migration Risks

**Risk**: Making `price_usd` nullable breaks existing queries

**Mitigation**:
- Add NULL checks to all queries that reference price
- Test in staging with production-like data
- Feature flag allows rollback without migration downgrade

### Performance Risks

**Risk**: Polling every 2 seconds creates load

**Mitigation**:
- Use connection pooling
- Limit poll frequency (2s is acceptable)
- Consider WebSocket for high-volume scenarios (future)

### Data Quality Risks

**Risk**: Users enter invalid prices

**Mitigation**:
- Frontend validation (positive number)
- Backend validation (Pydantic schema)
- Manual review dashboard (future enhancement)

---

## Success Criteria Summary

**Phase 1**: Migrations applied, schema updated, tests pass
**Phase 2**: API endpoints functional, services updated, tests pass
**Phase 3**: Modal renders, completes imports, accessible
**Phase 4**: Real-time updates working, toasts appearing
**Phase 5**: E2E tests pass, migrations validated
**Phase 6**: 80%+ import success rate, 70%+ completion rate

---

## Appendix: Agent Task Assignment Matrix

| Task | Primary Agent | Supporting Agent | Duration |
|------|---------------|------------------|----------|
| 1.1 Schema Updates | python-backend-engineer | - | 2-3h |
| 1.2 DB Migration | data-layer-expert | - | 3-4h |
| 1.3 Adapter Updates | python-backend-engineer | - | 2-3h |
| 1.4 ImportSession Model | data-layer-expert | - | 2h |
| 2.1 ListingsService | python-backend-engineer | - | 4-5h |
| 2.2 Completion Endpoint | python-backend-engineer | - | 2-3h |
| 2.3 Status Endpoint | python-backend-engineer | - | 4-5h |
| 3.1 PartialImportModal | ui-engineer | - | 4-6h |
| 3.2 Modal Integration | ui-engineer | - | 2-3h |
| 4.1 Polling Hook | ui-engineer | - | 3-4h |
| 4.2 Progress Component | ui-engineer | - | 2-3h |
| 4.3 Toast Notifications | ui-engineer | - | 2-3h |
| 5.1 E2E Testing | python-backend-engineer | ui-engineer | 1 day |
| 5.2 Migration Testing | data-layer-expert | - | 4h |
| 6.1 Feature Flag | python-backend-engineer | - | 2-3h |
| 6.2 Monitoring | python-backend-engineer | - | 4-5h |
| 6.3 Rollout | - | All agents | 2 weeks |

**Total Engineering Time**: ~8-11 days
**Calendar Time** (with parallelization): ~6-8 days + 2 weeks rollout
