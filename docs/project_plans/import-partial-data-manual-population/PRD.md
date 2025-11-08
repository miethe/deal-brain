---
title: "URL Import Enhancement: Partial Data Extraction & Manual Field Population"
description: "Enable partial data extraction from URLs with user-driven manual field population, eliminating all-or-nothing import failures and supporting real-time UI updates"
audience: [developers, ai-agents, pm, design]
tags:
  - import
  - ingestion
  - partial-data
  - manual-population
  - real-time-updates
  - feature-enhancement
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: accepted
related:
  - /docs/project_plans/requests/completed/listings-enhancements-v3.md
---

# URL Import Enhancement: Partial Data Extraction & Manual Field Population

## Executive Summary

The current URL import system uses an all-or-nothing approach: if price extraction fails, the entire import fails and the user loses all extracted data (images, specs, descriptions). This results in approximately 30% import success rate for Amazon and other challenging sources.

This PRD enables **partial data extraction** and **real-time manual field population**, allowing users to successfully import listings with partial data and immediately fill gaps via a modal UI. This increases import success rates to 80%+ while maintaining data quality through validation.

**Key Improvements:**
- Partial imports succeed with minimum viable data (title only)
- Real-time modal UI for manual field completion
- Live progress updates without page refresh
- Improved data quality tracking and provenance
- 80%+ import success rate (up from ~30%)

---

## Problem Statement

### Current Behavior & Pain Points

The existing import pipeline enforces strict schema validation that creates an all-or-nothing user experience:

**Technical Limitations:**
1. `NormalizedListingSchema` already allows `price: Decimal | None` but validation rejects imports without price
2. `BaseAdapter._validate_response()` requires both title AND price (though current code already shows `price` is optional in schema)
3. Database `listings.price_usd` is NOT NULL, preventing storage of partial imports
4. No UI mechanism to capture missing fields after import
5. No real-time feedback - users must refresh to see results

**User Impact:**
- **Amazon Imports**: Price extraction fails 60-70% due to dynamic pricing and JavaScript rendering
- **Valuable Data Lost**: Title, images, CPU model, RAM, storage specs are extracted but discarded
- **Manual Workaround**: Users manually re-enter entire listing, duplicating extraction effort
- **Low Success Rate**: ~30% of attempted imports succeed, requiring fallback to manual entry
- **No Recovery Path**: Once import fails, extracted data is lost forever

**Business Impact:**
- Import adoption low due to lack of confidence
- Time waste: 5-10 minutes per listing (manual entry) vs. 30 seconds (URL import)
- Marketplace expansion limited: Amazon, Etsy, and non-native sources have low success
- Competitive disadvantage against tools supporting partial imports
- Support burden from import failure tickets

---

## Goals & Success Metrics

### Primary Goals

1. **Enable Partial Data Extraction**: Accept imports with title only (price optional)
2. **Support Real-Time Manual Population**: Modal UI for immediately filling missing price
3. **Improve Import Success Rate**: Increase from ~30% to 80%+ for all marketplaces
4. **Real-Time UI Feedback**: Update listings grid without page refresh
5. **Maintain Data Quality**: Validate manually entered fields before submission

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Import Success Rate** | ~30% | 80%+ | (Complete + Partial) / Total Attempts |
| **Partial Import Rate** | 0% | 15-25% | Partial Imports / Total Successful |
| **Manual Completion Rate** | N/A | 70%+ | Completed Modals / Partial Imports |
| **Time to Import** | 5-10 min | 30-60 sec | Extraction + Manual Entry Time |
| **Amazon Success Rate** | ~20% | 70%+ | Amazon Successful / Amazon Attempts |
| **Data Quality Score** | ~85% | 90%+ | Valid Data / Total Fields |
| **UI Page Refresh Needed** | 100% | 0% | Real-time updates implemented |

---

## User Stories

### Story 1: Partial Import with Manual Completion

**As a** user importing from Amazon
**I want** to import a listing even if price extraction fails
**So that** I can quickly add the price manually instead of losing all data

**Acceptance Criteria:**
- Import succeeds with title, images, and specs but no price
- Modal auto-opens showing extracted data (read-only) and price field (editable)
- User enters price: $299.99
- User clicks "Save" and listing appears in dashboard immediately
- Listing shows quality indicator: "Price manually entered"

**Example Flow:**
```
URL Submission: https://amazon.com/dp/B08N5WRWNW
  ↓
Adapter extraction → Title: "Dell OptiPlex 7090", Images: [3], CPU: i5-10500, Price: null
  ↓
Import succeeds with quality="partial", listing_id=123 created
  ↓
Modal opens: "Complete 1 missing field"
  ↓
User enters price: $299.99
  ↓
PATCH /api/v1/listings/123 → Update price, recalculate metrics
  ↓
Modal closes, listing appears in grid with "manually completed" badge
```

### Story 2: Real-Time Import Status

**As a** user importing multiple URLs
**I want** to see import results in real-time without refreshing
**So that** I can immediately view and act on imported listings

**Acceptance Criteria:**
- User uploads 5 URLs via bulk import
- Progress indicator shows: "Processing 2 of 5..."
- Each URL completion updates grid in real-time
- Toast notification appears for each successful import
- "Complete" button in toast opens modal for partial imports

**Example Flow:**
```
Bulk Upload (5 URLs)
  ↓
POST /api/v1/ingest/bulk → bulk_job_id=abc-123
  ↓
Frontend polls: GET /api/v1/ingest/bulk/abc-123/status every 2 seconds
  ↓
Import 1 completes (full) → Grid updates, toast: "Dell OptiPlex imported ✓"
  ↓
Import 2 completes (partial) → Toast: "HP Mini PC (price needed)" + [Complete] button
  ↓
User clicks [Complete] → PartialImportModal opens
  ↓
Imports 3-5 complete → Grid shows all results without refresh
```

### Story 3: Abandoned Partial Import Recovery

**As a** user with partial imports
**I want** to complete them later if I close the modal
**So that** I don't lose the extracted data

**Acceptance Criteria:**
- Partial import saves to database even if user closes modal
- Dashboard shows "Incomplete Imports" section with count badge
- User can click "Complete" to reopen modal with original data
- Partial listings can be filtered and managed

---

## Technical Requirements

### Phase 1: Backend - Partial Extraction Support

**Duration**: 2-3 days
**Agent Assignment**: `python-backend-engineer` + `data-layer-expert`

#### 1.1 Schema Changes

**Note**: `NormalizedListingSchema` already has `price: Decimal | None` - validation logic needs adjustment.

**File**: `packages/core/dealbrain_core/schemas/ingestion.py`

**Changes Required:**
1. Update validator `validate_minimum_data()` to only require title (price fully optional)
2. Add `quality` field: `"full"` (has price) vs. `"partial"` (missing price)
3. Add `extraction_metadata` field for tracking field sources
4. Add `missing_fields` list for UI guidance

```python
class NormalizedListingSchema(DealBrainModel):
    # Existing fields remain unchanged
    title: str = Field(...)  # REQUIRED
    price: Decimal | None = Field(None, ...)  # OPTIONAL

    # New fields
    quality: str = Field(
        default="full",
        pattern=r"^(full|partial)$",
        description="Data completeness: full (has price) or partial (missing price)"
    )
    extraction_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Field provenance: {field_name: 'extracted'|'manual'|'failed'}"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of expected but missing fields for UI"
    )

    @field_validator("price")
    @classmethod
    def validate_minimum_data(cls, price: Decimal | None, info) -> Decimal | None:
        """Only require title - price is fully optional for partial imports."""
        if price is None:
            # Just verify title exists (already required by Field(...))
            title = info.data.get("title")
            if not title or not str(title).strip():
                raise ValueError("Title is required for all imports")
        return price
```

#### 1.2 Adapter Updates

**Files**:
- `apps/api/dealbrain_api/adapters/base.py`
- `apps/api/dealbrain_api/adapters/jsonld.py`
- `apps/api/dealbrain_api/adapters/ebay.py`
- `apps/api/dealbrain_api/adapters/scraper.py`

**Changes**: Remove price requirement from adapter validation

```python
# BaseAdapter._validate_response() - REMOVE price from required fields
def _validate_response(self, data: dict[str, Any]) -> None:
    """Validate minimum viable data - only title required."""
    # BEFORE: required_fields = ["title", "price"]
    # AFTER:  required_fields = ["title"]

    required_fields = ["title"]
    missing = [f for f in required_fields if f not in data or not data[f]]

    if missing:
        raise AdapterException(
            AdapterError.INVALID_SCHEMA,
            f"Missing required fields: {', '.join(missing)}",
        )

    # Log warning if price missing but continue
    if not data.get("price"):
        logger.warning(f"[{self.name}] No price extracted - will create partial import")
        data["quality"] = "partial"
        data["missing_fields"] = ["price"]
        data["extraction_metadata"] = {
            k: "extracted" for k, v in data.items()
            if v and k not in ["quality", "missing_fields", "extraction_metadata"]
        }
        data["extraction_metadata"]["price"] = "extraction_failed"
```

#### 1.3 Database Schema Migration

**Agent**: `data-layer-expert`

**File**: `apps/api/alembic/versions/0022_partial_import_support.py`

**Critical Decision**: Make `listings.price_usd` nullable to support partial imports.

```python
"""Partial import support: nullable price and quality tracking

Revision ID: 0022
Revises: 0021
Create Date: 2025-11-08
"""

def upgrade():
    # Make price nullable to support partial imports
    op.alter_column(
        'listing',
        'price_usd',
        existing_type=sa.Float(),
        nullable=True  # CRITICAL: Allow NULL prices
    )

    # Add quality tracking to listings
    op.add_column(
        'listing',
        sa.Column('quality', sa.String(20), nullable=False, server_default='full')
    )

    # Add extraction metadata JSON for provenance
    op.add_column(
        'listing',
        sa.Column('extraction_metadata', sa.JSON(), nullable=False, server_default='{}')
    )

    # Add missing_fields list for UI
    op.add_column(
        'listing',
        sa.Column('missing_fields', sa.JSON(), nullable=False, server_default='[]')
    )

def downgrade():
    op.drop_column('listing', 'missing_fields')
    op.drop_column('listing', 'extraction_metadata')
    op.drop_column('listing', 'quality')

    # Cannot make price_usd NOT NULL if partial imports exist
    # This migration is IRREVERSIBLE if partial data exists
    op.execute("DELETE FROM listing WHERE price_usd IS NULL")
    op.alter_column('listing', 'price_usd', nullable=False)
```

**Migration Risk Assessment:**
- **Low Risk**: New columns added with defaults, no data loss
- **Irreversible Aspect**: If partial imports exist, downgrade will delete them
- **Strategy**: Feature flag to control rollout, allow migration in staging first

#### 1.4 Listings Service Updates

**Agent**: `python-backend-engineer`

**File**: `apps/api/dealbrain_api/services/listings.py`

**Changes**: Support creating listings without price, skip metrics calculation

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
    Metrics calculation deferred until price is provided.
    """
    listing = Listing(
        title=normalized_data.title,
        price_usd=normalized_data.price,  # May be None
        condition=normalized_data.condition,
        marketplace=normalized_data.marketplace,
        vendor_item_id=normalized_data.vendor_item_id,
        manufacturer=normalized_data.manufacturer,
        model_number=normalized_data.model_number,
        # ... other fields ...
        quality=normalized_data.quality or ("partial" if normalized_data.price is None else "full"),
        extraction_metadata=normalized_data.extraction_metadata or {},
        missing_fields=normalized_data.missing_fields or [],
    )

    # Only calculate metrics if price exists
    if listing.price_usd is not None:
        await self._apply_valuation_and_scoring(listing, session)
    else:
        logger.info(f"Listing {listing.id} created without price - metrics deferred")

    session.add(listing)
    await session.flush()
    return listing


async def complete_partial_import(
    self,
    listing_id: int,
    completion_data: dict[str, Any],
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """
    Complete a partial import by filling missing fields.

    Args:
        listing_id: Listing to complete
        completion_data: Dict with missing fields (e.g., {"price": 299.99})
        user_id: User completing the import
        session: Database session

    Returns:
        Updated listing with metrics calculated
    """
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    if listing.quality != "partial":
        raise ValueError(f"Listing {listing_id} is not partial - nothing to complete")

    # Update fields from completion data
    if "price" in completion_data:
        listing.price_usd = float(completion_data["price"])
        # Track manual entry
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

    # Calculate metrics now that price exists
    if listing.price_usd is not None:
        await self._apply_valuation_and_scoring(listing, session)

    await session.flush()
    return listing
```

#### 1.5 API Endpoint Updates

**Agent**: `python-backend-engineer`

**File**: `apps/api/dealbrain_api/api/ingestion.py`

**New Endpoint**: PATCH endpoint for completing partial imports

```python
@router.patch("/api/v1/listings/{listing_id}/complete")
async def complete_partial_import(
    listing_id: int,
    completion_data: dict[str, Any],
    session: AsyncSession = Depends(session_dependency),
    current_user: dict = Depends(get_current_user),
) -> ListingSchema:
    """
    Complete a partial import by providing missing fields.

    Request body example:
    {
        "price": 299.99,
        "condition": "refurb"  # optional
    }

    Validates data, updates listing, calculates metrics.
    """
    listings_service = ListingsService()
    updated_listing = await listings_service.complete_partial_import(
        listing_id=listing_id,
        completion_data=completion_data,
        user_id=current_user["id"],
        session=session,
    )
    await session.commit()
    return ListingSchema.model_validate(updated_listing)
```

---

### Phase 2: Backend - Real-Time Status Updates

**Duration**: 1-2 days
**Agent Assignment**: `python-backend-engineer`

#### 2.1 Bulk Import Status Endpoint

**File**: `apps/api/dealbrain_api/api/ingestion.py`

**Endpoint**: `GET /api/v1/ingest/bulk/{bulk_job_id}/status`

**Note**: Schema `BulkIngestionStatusResponse` already exists in `packages/core/dealbrain_core/schemas/ingestion.py`

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

    Returns per-URL status with quality indicators.
    Frontend polls this endpoint every 2 seconds during import.
    """
    # Query ImportSession records by bulk_job_id
    # Aggregate counts: queued, running, complete, partial, failed
    # Return paginated per_row_status

    # Implementation delegated to python-backend-engineer
```

#### 2.2 Job Tracking Enhancement

**Current State**: `ImportSession` model exists but doesn't track bulk jobs or detailed status.

**Required Changes**:
1. Add `bulk_job_id` field to link related imports
2. Add `quality` field to track partial vs. full
3. Add `listing_id` field to reference created listing

**Migration**: `apps/api/alembic/versions/0023_bulk_job_tracking.py`

```python
def upgrade():
    # Add bulk job tracking
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

    # Add completed_at timestamp
    op.add_column(
        'import_session',
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
```

---

### Phase 3: Frontend - Manual Population Modal

**Duration**: 2-3 days
**Agent Assignment**: `ui-engineer`

#### 3.1 Modal Component Structure

**File**: `apps/web/components/imports/PartialImportModal.tsx`

**Component Hierarchy**:
```
PartialImportModal (Dialog)
├── DialogHeader
│   ├── DialogTitle: "Complete Import"
│   └── DialogDescription: "Fill 1 missing field to complete"
├── DialogContent
│   ├── ExtractedFieldsSection (read-only display)
│   │   └── FieldRow[] (title, images, CPU, RAM, storage)
│   └── MissingFieldsForm (editable inputs)
│       └── PriceInput (validated, required)
└── DialogFooter
    ├── Button (variant="outline"): "Skip for Now"
    └── Button (primary): "Save Listing"
```

**Key Features**:
- Auto-opens when `quality="partial"` in ingestion response
- Read-only display of extracted fields with checkmarks
- Highlighted editable section for missing fields
- Real-time validation (price must be positive)
- Keyboard accessible (Tab, Enter to submit, Esc to close)
- Screen reader support (ARIA labels, live regions)

#### 3.2 State Management

**Hook**: `apps/web/hooks/usePartialImportCompletion.ts`

```typescript
interface UsePartialImportCompletionProps {
  listingId: number;
  extractedData: NormalizedListingSchema;
  missingFields: string[];
}

export function usePartialImportCompletion({
  listingId,
  extractedData,
  missingFields,
}: UsePartialImportCompletionProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { mutateAsync: completeImport, isLoading } = useMutation({
    mutationFn: async (data: Record<string, any>) => {
      const response = await fetch(`/api/v1/listings/${listingId}/complete`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to complete import');
      return response.json();
    },
    onSuccess: () => {
      // Invalidate listings query to refresh grid
      queryClient.invalidateQueries(['listings']);
      // Show success toast
      toast.success('Listing completed successfully');
    },
  });

  const validateAndSubmit = async () => {
    const newErrors: Record<string, string> = {};

    // Validate price if missing
    if (missingFields.includes('price')) {
      const price = parseFloat(formData.price);
      if (!price || price <= 0) {
        newErrors.price = 'Price must be a positive number';
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    await completeImport(formData);
  };

  return {
    formData,
    setFormData,
    errors,
    validateAndSubmit,
    isLoading,
  };
}
```

#### 3.3 Integration with Import Flow

**File**: `apps/web/components/imports/ImportResultsGrid.tsx`

```typescript
function ImportResultsGrid() {
  const [partialImportToComplete, setPartialImportToComplete] = useState<Listing | null>(null);

  // Subscribe to import completion events
  useEffect(() => {
    const handleImportComplete = (event: CustomEvent) => {
      const { listing, quality } = event.detail;

      if (quality === 'partial') {
        // Auto-open modal for partial imports
        setPartialImportToComplete(listing);
      } else {
        // Show success toast for complete imports
        toast.success(`${listing.title} imported successfully`);
      }
    };

    window.addEventListener('import-complete', handleImportComplete);
    return () => window.removeEventListener('import-complete', handleImportComplete);
  }, []);

  return (
    <>
      <ImportGrid />

      {partialImportToComplete && (
        <PartialImportModal
          listing={partialImportToComplete}
          onComplete={() => setPartialImportToComplete(null)}
          onSkip={() => setPartialImportToComplete(null)}
        />
      )}
    </>
  );
}
```

---

### Phase 4: Frontend - Real-Time UI Updates

**Duration**: 2-3 days
**Agent Assignment**: `ui-engineer`

#### 4.1 Import Status Polling Hook

**File**: `apps/web/hooks/useImportStatus.ts`

```typescript
export function useImportStatus(bulkJobId: string | null) {
  const [status, setStatus] = useState<BulkIngestionStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!bulkJobId) return;

    setIsPolling(true);

    // Poll every 2 seconds
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/ingest/bulk/${bulkJobId}/status`);
        const data = await response.json();
        setStatus(data);

        // Stop polling when all complete
        const allDone = data.queued === 0 && data.running === 0;
        if (allDone) {
          setIsPolling(false);
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling import status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [bulkJobId]);

  return { status, isPolling };
}
```

#### 4.2 Toast Notifications Component

**File**: `apps/web/components/imports/ImportToasts.tsx`

**Features**:
- Toast appears when import completes
- Different variants: success (full), warning (partial), error (failed)
- Action buttons: "View" (full), "Complete" (partial), "Retry" (failed)
- Auto-dismiss after 5 seconds
- Accessible announcements via `aria-live`

#### 4.3 Progress Indicator

**File**: `apps/web/components/imports/BulkImportProgress.tsx`

```typescript
interface BulkImportProgressProps {
  status: BulkIngestionStatusResponse;
}

export function BulkImportProgress({ status }: BulkImportProgressProps) {
  const completionPct = (status.completed / status.total_urls) * 100;

  return (
    <div className="mb-6">
      <div className="flex justify-between text-sm text-muted-foreground mb-2">
        <span>Import Progress</span>
        <span>
          {status.completed} of {status.total_urls}
          {' '}({status.success} successful, {status.partial} partial)
        </span>
      </div>

      <Progress value={completionPct} className="h-2" />

      <div className="flex gap-4 text-xs text-muted-foreground mt-2">
        <span className="flex items-center gap-1">
          <CheckCircle className="w-3 h-3 text-green-600" />
          {status.success} complete
        </span>
        <span className="flex items-center gap-1">
          <AlertCircle className="w-3 h-3 text-yellow-600" />
          {status.partial} partial
        </span>
        <span className="flex items-center gap-1">
          <XCircle className="w-3 h-3 text-red-600" />
          {status.failed} failed
        </span>
      </div>
    </div>
  );
}
```

---

## Edge Cases & Error Handling

### Edge Case 1: No Title Extracted

**Scenario**: Adapter extracts only images, no title or CPU model

**Behavior**:
- Validation fails: "Title is required"
- Import fails with error: `AdapterError.INVALID_SCHEMA`
- User sees error message: "Could not extract listing information"
- Suggestion: "Try a different URL or add listing manually"

**No partial import created** - title is absolute minimum requirement.

### Edge Case 2: Price Invalid Format

**Scenario**: Price extracted as "£299.99" or "299,99€"

**Behavior**:
- Adapter attempts to parse and convert to USD Decimal
- If parsing fails: Set `price=None`, `extraction_metadata["price"]="parse_failed"`
- Import succeeds as partial with quality="partial"
- User manually enters price in modal
- Complete import with manual price

### Edge Case 3: User Abandons Modal

**Scenario**: Partial import modal opens, user clicks "Skip for Now"

**Behavior**:
- Listing remains in database with `quality="partial"`, `price_usd=NULL`
- Dashboard shows "Incomplete Imports" section (future enhancement)
- Listing visible in grid with badge: "Missing price"
- User can click "Complete" button later to reopen modal
- Data persists - no loss of extracted information

### Edge Case 4: Duplicate Detection with Partial Import

**Scenario**: Similar listing exists (same title + manufacturer)

**Behavior**:
- Deduplication runs on `dedup_hash` (title + vendor_item_id)
- If duplicate found:
  - Log warning: "Potential duplicate detected"
  - Create import anyway (user may want multiple versions)
  - Show warning in UI (future enhancement)
- No automatic merging - requires explicit user action

### Edge Case 5: Network Error During Completion

**Scenario**: User fills modal, submits, network fails

**Behavior**:
- Mutation fails, React Query retries (3 attempts)
- Error toast shown: "Could not save listing"
- Form data preserved in modal (not cleared)
- User can click "Save Listing" again to retry
- No partial listing created in limbo state

---

## Testing Strategy

### Unit Tests (Backend)

**File**: `tests/test_partial_imports.py`

```python
class TestPartialImportSupport:
    async def test_schema_allows_null_price(self):
        """Verify NormalizedListingSchema accepts None price"""
        schema = NormalizedListingSchema(
            title="Dell OptiPlex 7090",
            price=None,
            condition="refurb",
            marketplace="amazon",
        )
        assert schema.price is None
        assert schema.quality == "full"  # Default value

    async def test_create_listing_without_price(self, session):
        """Verify listings can be created with null price"""
        listing = Listing(
            title="Test PC",
            price_usd=None,
            condition="used",
            marketplace="other",
            quality="partial",
        )
        session.add(listing)
        await session.commit()

        assert listing.id is not None
        assert listing.price_usd is None
        assert listing.quality == "partial"

    async def test_complete_partial_import(self, session):
        """Verify partial import completion flow"""
        # Create partial listing
        listing = Listing(
            title="Test PC",
            price_usd=None,
            quality="partial",
            missing_fields=["price"],
        )
        session.add(listing)
        await session.flush()

        # Complete it
        service = ListingsService()
        updated = await service.complete_partial_import(
            listing_id=listing.id,
            completion_data={"price": 299.99},
            user_id="user123",
            session=session,
        )

        assert updated.price_usd == 299.99
        assert updated.quality == "full"
        assert updated.missing_fields == []
        assert updated.extraction_metadata["price"] == "manual"
```

### Integration Tests (Backend)

**File**: `tests/test_ingestion_partial.py`

```python
class TestPartialImportIntegration:
    async def test_import_without_price_succeeds(self, client, session):
        """Full flow: URL → adapter → null price → listing created"""
        # Mock adapter response without price
        with patch('adapters.scraper.extract') as mock_extract:
            mock_extract.return_value = {
                "title": "Dell OptiPlex 7090",
                "price": None,
                "condition": "refurb",
                "marketplace": "amazon",
            }

            response = await client.post(
                "/api/v1/ingest",
                json={"url": "https://amazon.com/test"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "complete"
            assert data["quality"] == "partial"
            assert data["listing_id"] is not None

            # Verify listing created
            listing = await session.get(Listing, data["listing_id"])
            assert listing.price_usd is None
            assert listing.quality == "partial"
```

### Component Tests (Frontend)

**File**: `apps/web/components/imports/__tests__/PartialImportModal.test.tsx`

```typescript
describe('PartialImportModal', () => {
  it('renders extracted fields as read-only', () => {
    const extractedData = {
      title: 'Dell OptiPlex',
      images: ['img1.jpg'],
      cpu_model: 'Intel i5',
      price: null,
    };

    render(
      <PartialImportModal
        listing={{ ...mockListing, ...extractedData }}
        onComplete={vi.fn()}
        onSkip={vi.fn()}
      />
    );

    expect(screen.getByText('Dell OptiPlex')).toBeInTheDocument();
    expect(screen.getByText(/extracted/i)).toBeInTheDocument();
  });

  it('validates price before submission', async () => {
    render(<PartialImportModal {...defaultProps} />);

    const input = screen.getByLabelText('Price');
    await userEvent.type(input, '-100');
    await userEvent.click(screen.getByText('Save Listing'));

    expect(screen.getByText(/must be positive/i)).toBeInTheDocument();
  });
});
```

### E2E Tests

**File**: `tests/e2e/partial_import.spec.ts`

```typescript
describe('Partial Import E2E', () => {
  it('completes full flow: URL → partial → modal → complete', async ({ page }) => {
    await page.goto('/dashboard/import');

    // Submit URL without price
    await page.fill('input[placeholder="Paste URL"]', 'https://amazon.com/no-price');
    await page.click('button:has-text("Import")');

    // Wait for modal to auto-open
    await expect(page.locator('text=Complete Import')).toBeVisible();

    // View extracted data
    await expect(page.locator('text=Dell OptiPlex')).toBeVisible();

    // Fill price
    await page.fill('input[label="Price"]', '299.99');
    await page.click('button:has-text("Save Listing")');

    // Verify listing appears in grid
    await expect(page.locator('text=Dell OptiPlex')).toBeVisible();
    await expect(page.locator('text=299.99')).toBeVisible();
  });
});
```

---

## Rollout Plan

### Phase 1: Feature Flag Setup

**Duration**: 1 day

- Add `FEATURE_PARTIAL_IMPORTS` to ApplicationSettings
- Default: `false` (disabled)
- Backend checks flag before allowing partial imports
- Frontend hides modal if flag disabled

### Phase 2: Internal Testing

**Duration**: 2-3 days

- Enable in dev/staging environments
- Internal team tests all scenarios
- Performance test: 100+ URL bulk import
- Validate data quality metrics

### Phase 3: Beta Users

**Duration**: 3-5 days

- Enable for 5-10 selected beta users
- Monitor metrics:
  - Partial import rate (expect 15-25%)
  - Manual completion rate (expect 70%+)
  - Data quality (validation errors <5%)
- Collect feedback via in-app survey

### Phase 4: Controlled Rollout

**Duration**: 1 week

- Enable for 25% of users
- Monitor error rates and performance
- Adjust modal UX based on feedback
- Fix any critical bugs

### Phase 5: Full Rollout

**Duration**: 1 week

- Enable for 100% of users
- Remove feature flag (make default behavior)
- Update documentation
- Celebrate improved import success rate!

---

## Monitoring & Observability

### Dashboard Metrics

**Prometheus Metrics** (to be added):
- `import_attempts_total{marketplace, quality}` - Counter
- `import_success_rate{marketplace}` - Gauge
- `partial_import_completion_rate` - Gauge
- `import_duration_seconds{marketplace, quality}` - Histogram

**Grafana Dashboard** (to be created):
- Import success rate trend (7-day rolling)
- Partial import rate by marketplace
- Manual completion funnel (partial → completed)
- Time to completion distribution

### Error Tracking

**Sentry Events** (to be added):
- Adapter extraction failures by type
- Modal validation errors by field
- API completion endpoint errors

### User Behavior Analytics

**Events to Track**:
- `partial_import_created` - When partial listing saved
- `partial_import_modal_opened` - When modal displayed
- `partial_import_completed` - When user completes modal
- `partial_import_skipped` - When user closes modal
- `partial_import_abandoned` - Partial listing never completed (7+ days)

---

## Future Enhancements (Post-MVP)

### Phase 5+: Bulk Manual Population

**Goal**: Complete multiple partial imports at once

**Features**:
- "Complete All Partial" button in dashboard
- Table view showing all partial imports
- Inline editing for prices
- Bulk submit all at once

**Estimated Effort**: 3-4 days

### Phase 6+: ML-Based Price Estimation

**Goal**: Suggest prices for partial imports

**Features**:
- Analyze similar listings (same CPU + RAM + storage)
- Calculate price range: low, median, high
- Pre-fill price input with median suggestion
- User can accept or override

**Estimated Effort**: 1-2 weeks (requires ML pipeline)

### Phase 7+: Marketplace Native APIs

**Goal**: Eliminate scraping failures with official APIs

**Features**:
- Amazon Product Advertising API integration
- eBay Browse API (already using Finding API)
- Etsy Open API integration
- 100% extraction success for supported marketplaces

**Estimated Effort**: 2-3 weeks per marketplace

---

## Success Criteria

### Quantitative Metrics

- **Import Success Rate**: 80%+ (up from ~30%)
- **Partial Import Rate**: 15-25% of all successful imports
- **Manual Completion Rate**: 70%+ of partial imports completed
- **Data Quality Score**: 90%+ (validation errors <10%)
- **Time to Import**: <60 seconds average (extraction + manual entry)
- **Page Refresh Needed**: 0% (100% real-time updates)

### Qualitative Goals

- Users report improved import experience in surveys
- Support tickets for import failures reduced by 50%
- Feature adoption: 80%+ of users successfully use partial imports
- Code quality: All tests passing, <5% bug rate in first 2 weeks

---

## Appendix: Related Documentation

- **Current Ingestion System**: Architecture already supports partial data (schemas allow `price=None`)
- **Adapter Implementation Guide**: `/docs/development/adapter-implementation.md`
- **API Schemas**: `packages/core/dealbrain_core/schemas/ingestion.py`
- **Database Models**: `apps/api/dealbrain_api/models/core.py` (Listing, ImportSession)
- **Frontend Components**: `apps/web/components/imports/`
