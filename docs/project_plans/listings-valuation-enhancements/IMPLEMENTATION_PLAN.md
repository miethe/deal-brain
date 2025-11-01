# Implementation Plan: Listing Valuation & Management Enhancements

## Overview

This document outlines the actionable implementation plan for the Listing Valuation & Management Enhancements PRD. See [PRD.md](./PRD.md) for full requirements and problem context.

**Approach**: Three independent phases enabling parallel work. Phase 1 (metrics fix) is backend-heavy but non-breaking. Phase 2 (delete) and Phase 3 (import) can proceed in parallel after Phase 1 validation.

**Timeline Estimate**: 2-3 weeks
- Phase 1: 4-5 days (backend + tests + audit)
- Phase 2: 3-4 days (endpoint + UI)
- Phase 3: 2-3 days (modal extraction + integration)

---

## Phase 1: Adjusted Valuation Calculation Fix

**Priority**: CRITICAL – Fixes data accuracy issue affecting user trust

### Task 1.1: Fix CPU Performance Metrics Calculation

**File**: `apps/api/dealbrain_api/services/listings.py` (lines 706-734)

**Current Code**:
```python
def calculate_cpu_performance_metrics(listing: Listing) -> dict[str, float]:
    if not listing.cpu:
        return {}

    cpu = listing.cpu
    base_price = float(listing.price_usd)
    adjusted_price = float(listing.adjusted_price_usd) if listing.adjusted_price_usd else base_price

    metrics = {}

    # Single-thread metrics
    if cpu.cpu_mark_single and cpu.cpu_mark_single > 0:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_price / cpu.cpu_mark_single  # WRONG

    # Multi-thread metrics
    if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_price / cpu.cpu_mark_multi  # WRONG

    return metrics
```

**Required Change**:
1. Extract `total_adjustment` from `listing.valuation_breakdown` JSON
   - Key path: `valuation_breakdown['summary']['total_adjustment']`
   - Default to 0.0 if missing or None
2. Calculate adjusted delta: `adjusted_base_price = base_price - total_adjustment`
3. Use delta in adjusted metrics: `adjusted_base_price / cpu_mark` (not adjusted_price)

**New Code Pattern**:
```python
def calculate_cpu_performance_metrics(listing: Listing) -> dict[str, float]:
    if not listing.cpu:
        return {}

    cpu = listing.cpu
    base_price = float(listing.price_usd)

    # Extract adjustment delta from valuation breakdown
    total_adjustment = 0.0
    if listing.valuation_breakdown:
        summary = listing.valuation_breakdown.get('summary', {})
        total_adjustment = float(summary.get('total_adjustment', 0.0))

    adjusted_base_price = base_price - total_adjustment

    metrics = {}

    # Single-thread metrics
    if cpu.cpu_mark_single and cpu.cpu_mark_single > 0:
        metrics['dollar_per_cpu_mark_single'] = base_price / cpu.cpu_mark_single
        metrics['dollar_per_cpu_mark_single_adjusted'] = adjusted_base_price / cpu.cpu_mark_single

    # Multi-thread metrics
    if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
        metrics['dollar_per_cpu_mark_multi'] = base_price / cpu.cpu_mark_multi
        metrics['dollar_per_cpu_mark_multi_adjusted'] = adjusted_base_price / cpu.cpu_mark_multi

    return metrics
```

**Acceptance Criteria**:
- Adjusted metrics use `(base_price - adjustment_delta)` formula
- All four metric keys updated (single + multi, base + adjusted)
- Handles missing/None valuation_breakdown gracefully
- No schema migration required

---

### Task 1.2: Audit All Usages of Adjusted Metrics Fields

**Scope**: Search entire codebase for references to adjusted metric fields

**Search Terms**:
- `dollar_per_cpu_mark_single_adjusted`
- `dollar_per_cpu_mark_multi_adjusted`

**Files to Check**:
1. Backend API response schemas: `apps/api/dealbrain_api/api/schemas/listings.py`
2. Frontend types: `apps/web/types/listings.ts`
3. Frontend components using metrics: `apps/web/app/listings/_components/`
4. Dashboard/export logic: `apps/web/app/dashboard/`
5. Comparison logic: `apps/web/app/listings/_components/master-detail-view/compare-drawer.tsx`

**Actions**:
- Verify each usage correctly interprets metric as "CPU value after component adjustments"
- Document any display transformations or comparisons
- Update comments if semantics changed
- No code changes typically needed – metric now means what code expected

**Acceptance Criteria**:
- All 5+ files reviewed
- No conflicting interpretations found
- Comments updated where needed
- Document: "Metric Audit Summary" (table of files checked)

---

### Task 1.3: Update Test Coverage

**Primary Test File**: `tests/test_listing_metrics.py`

**Test Cases to Add/Modify**:

| Test Name | Scenario | Assertions |
|-----------|----------|-----------|
| `test_cpu_metrics_delta_calculation` | Listing with $100 RAM deduction | `adjusted_base = 500 - 100 = 400`; metric = `400 / mark` |
| `test_cpu_metrics_no_adjustment` | Listing with zero adjustment | `adjusted_base = base_price`; both metrics equal |
| `test_cpu_metrics_missing_valuation_breakdown` | valuation_breakdown is None | Gracefully defaults adjustment to 0.0 |
| `test_cpu_metrics_multiple_adjustments` | $50 RAM + $30 storage deduction | `adjustment_delta = 80`; metric uses 80 |
| `test_cpu_metrics_integration_with_rules` | Full rule evaluation pipeline | Metrics recalculated after rules applied |

**Test Structure**:
```python
@pytest.mark.asyncio
async def test_cpu_metrics_delta_calculation(session: AsyncSession):
    """Verify adjusted metrics use delta formula: (base - adjustment) / mark"""
    # 1. Create CPU with known benchmarks
    # 2. Create listing with $500 base, valuation_breakdown with $100 adjustment
    # 3. Call calculate_cpu_performance_metrics()
    # 4. Assert adjusted_single = (500 - 100) / mark == 400 / mark
```

**Additional Tests**: `tests/test_ingestion_metrics_calculation.py`
- Add integration test: metrics recalculation after import with active rules

**Acceptance Criteria**:
- 5+ new test cases pass
- Integration test covers full pipeline
- Code coverage for metrics function ≥ 95%

---

### Task 1.4: Bulk Recalculation Script

**File**: Create `scripts/recalculate_adjusted_metrics.py`

**Purpose**: Recalculate all existing listings' metrics with new delta formula

**Implementation**:
1. Query all listings with assigned CPU
2. Call `update_listing_metrics(session, listing_id)` for each
3. Use `bulk_update_listing_metrics()` if available (check `apps/api/dealbrain_api/services/listings.py`)
4. Log progress every 100 listings
5. On completion, log summary: `"Recalculated metrics for {count} listings"`

**Script Template**:
```python
# scripts/recalculate_adjusted_metrics.py
import asyncio
from sqlalchemy import select
from apps.api.dealbrain_api.db import async_sessionmaker, engine
from apps.api.dealbrain_api.models import Listing
from apps.api.dealbrain_api.services.listings import update_listing_metrics

async def main():
    async_session = async_sessionmaker(engine)
    async with async_session() as session:
        # Query listings with CPU
        stmt = select(Listing).where(Listing.cpu_id.isnot(None))
        result = await session.execute(stmt)
        listings = result.scalars().all()

        for i, listing in enumerate(listings, 1):
            await update_listing_metrics(session, listing.id)
            if i % 100 == 0:
                print(f"Recalculated {i}/{len(listings)}")

        await session.commit()
        print(f"Done: Recalculated metrics for {len(listings)} listings")

if __name__ == '__main__':
    asyncio.run(main())
```

**Acceptance Criteria**:
- Script successfully recalculates all listings
- Progress logging works
- Summary output clear
- Can be run safely in staging/production

---

## Phase 2: Delete Listing Functionality

**Priority**: HIGH – Enables self-service data cleanup

### Task 2.1: Backend Delete Endpoint

**File**: `apps/api/dealbrain_api/api/listings.py`

**New Endpoint**:
```python
@router.delete('/listings/{listing_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> None:
    """Delete a listing and all related data.

    Cascade deletes:
    - ListingComponent records
    - ListingScoreSnapshot records
    - EntityFieldValue records for this listing

    Returns:
        204 No Content on success

    Raises:
        404: Listing not found
    """
    # Implementation in Task 2.1.1
```

**Service Layer**: Add to `apps/api/dealbrain_api/services/listings.py`

```python
async def delete_listing(
    session: AsyncSession,
    listing_id: int,
) -> None:
    """Delete listing and cascade related records.

    Args:
        session: Database session
        listing_id: ID of listing to delete

    Raises:
        ValueError: Listing not found
    """
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    # Cascade deletes handled by SQLAlchemy relationships
    await session.delete(listing)
    await session.commit()
```

**Database Cascade**: Verify in `apps/api/dealbrain_api/models/core.py` that:
- `Listing.components` has `cascade='all, delete-orphan'`
- `Listing.scores` has `cascade='all, delete-orphan'`
- `Listing.field_values` relationship exists with proper cascade

**Acceptance Criteria**:
- DELETE endpoint returns 204 on success
- Returns 404 if listing not found
- All related records deleted (components, scores, field values)
- Service handles errors gracefully
- Endpoint tested with valid and invalid IDs

---

### Task 2.2: Frontend Delete UI – Detail Modal

**File**: `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`

**UI Location**: Bottom action bar (near "View Full Page" button)

**Changes**:
1. Add red "Delete" button to action bar
2. Wire to delete confirmation dialog (reuse or create)
3. On confirmation, call mutation: `DELETE /api/v1/listings/{id}`
4. On success, invalidate `listings` cache and close modal
5. On error, show toast error

**Code Pattern**:
```typescript
// In detail-panel.tsx
const { mutate: deleteListing } = useMutation({
  mutationFn: async (id: number) => {
    const res = await fetch(`/api/v1/listings/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete listing');
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['listings'] });
    onClose?.();
    toast.success('Listing deleted');
  },
  onError: (error) => {
    toast.error(`Delete failed: ${error.message}`);
  }
});

<ConfirmationDialog
  title="Delete Listing?"
  description="This action cannot be undone."
  confirmText="Delete"
  onConfirm={() => deleteListing(listing.id)}
  open={deleteConfirmOpen}
  onOpenChange={setDeleteConfirmOpen}
>
  <Button variant="destructive" onClick={() => setDeleteConfirmOpen(true)}>
    Delete
  </Button>
</ConfirmationDialog>
```

**Acceptance Criteria**:
- Delete button visible and styled appropriately (red/destructive)
- Confirmation dialog shows before deletion
- Mutation calls correct endpoint
- Cache invalidates after success
- Error toast shown on failure

---

### Task 2.3: Frontend Delete UI – Detail Page

**File**: `apps/web/app/listings/[id]/page.tsx`

**UI Location**: Top right header (near metadata section)

**Changes**:
1. Add delete button (dropdown or direct button) in page header
2. Reuse same confirmation dialog and mutation as Task 2.2
3. On success, navigate to `/listings` (catalog)
4. Optional: Show loading state during deletion

**Code Pattern**:
```typescript
// In [id]/page.tsx
const router = useRouter();
const { mutate: deleteListing, isPending } = useMutation({
  mutationFn: async (id: number) => {
    const res = await fetch(`/api/v1/listings/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete');
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['listings'] });
    toast.success('Listing deleted');
    router.push('/listings');
  },
});

<Button
  variant="ghost"
  onClick={() => setDeleteConfirmOpen(true)}
  disabled={isPending}
>
  Delete
</Button>
```

**Acceptance Criteria**:
- Delete button visible in page header
- Confirmation dialog appears before deletion
- Navigation to `/listings` on success
- Loading state shown during deletion
- Error handled gracefully

---

### Task 2.4: Confirmation Dialog Component & Accessibility

**File**: `apps/web/components/ui/confirmation-dialog.tsx` (create if needed)

**Requirements**:
- Accessible: `role="alertdialog"`, focus trap, keyboard support (Esc to cancel, Enter to confirm)
- Props: `title`, `description`, `confirmText`, `cancelText`, `onConfirm`, `onCancel`, `open`, `onOpenChange`, `isDangerous` (for styling)
- Variants: Destructive (red) for delete, Default for others
- ARIA labels for accessibility

**Reuse Pattern**: Use shadcn/ui Dialog + AlertDialog if available, else implement custom

**Acceptance Criteria**:
- Component creates/exported and reusable
- Focus management works (trap + restore)
- Keyboard navigation works (Tab, Shift+Tab, Enter, Esc)
- ARIA attributes set correctly

---

## Phase 3: Import Button in Catalog View

**Priority**: MEDIUM – Improves workflow but not data critical

### Task 3.1: Extract Import Modal to Shared Component

**Source**: `apps/web/app/import/page.tsx` (extract form/modal logic)

**Target**: Create `apps/web/components/listings/import-modal.tsx`

**Changes**:
1. Extract import UI from page component (form, tabs for URL/file, upload handler)
2. Create new `ImportModal` component accepting props:
   - `open: boolean`
   - `onOpenChange: (open: boolean) => void`
   - `onSuccess?: () => void` (callback after import completes)
3. Keep all validation and import service logic (no changes needed)
4. Reuse existing import mutation/service

**Code Structure**:
```typescript
// apps/web/components/listings/import-modal.tsx
export interface ImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ImportModal({ open, onOpenChange, onSuccess }: ImportModalProps) {
  // Move import form logic here
  // Tabs: URL import, File upload
  // Call existing importListings mutation
  // onSuccess: close modal + call onSuccess callback
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Form content */}
    </Dialog>
  );
}
```

**Acceptance Criteria**:
- Component extracts cleanly from `/import` page
- Props documented
- Import logic unchanged
- Reusable in multiple contexts

---

### Task 3.2: Add Import Button to Catalog Header

**File**: `apps/web/app/listings/page.tsx`

**UI Location**: Top right, next to "Add Listing" button

**Changes**:
1. Add `<ImportModal />` component
2. State to control modal open/close
3. Add "Import" button triggering modal open
4. Style consistently with existing action buttons

**Code Pattern**:
```typescript
// In app/listings/page.tsx
const [importModalOpen, setImportModalOpen] = useState(false);

return (
  <>
    <div className="flex gap-2">
      <Button onClick={() => setImportModalOpen(true)}>
        <Upload className="w-4 h-4 mr-2" />
        Import
      </Button>
      <Button onClick={() => router.push('/listings/new')}>
        <Plus className="w-4 h-4 mr-2" />
        Add Listing
      </Button>
    </div>

    <ImportModal
      open={importModalOpen}
      onOpenChange={setImportModalOpen}
      onSuccess={() => queryClient.invalidateQueries({ queryKey: ['listings'] })}
    />
  </>
);
```

**Acceptance Criteria**:
- Button visible next to "Add Listing"
- Button styling matches design system
- Click opens modal
- Icon (Upload) is clear and intuitive

---

### Task 3.3: Wire Up Modal Trigger and Refresh

**File**: `apps/web/components/listings/import-modal.tsx` (update Task 3.1)

**Changes**:
1. Import mutation calls existing import service
2. On success, close modal (call `onOpenChange(false)`)
3. Call optional `onSuccess` callback to trigger cache refresh
4. Show success toast with count of imported listings
5. Show error toast if import fails

**Code Pattern**:
```typescript
export function ImportModal({ open, onOpenChange, onSuccess }: ImportModalProps) {
  const queryClient = useQueryClient();

  const { mutate: importListings, isPending } = useMutation({
    mutationFn: async (data: ImportRequest) => {
      return await importService.import(data);
    },
    onSuccess: (result) => {
      toast.success(`Imported ${result.count} listings`);
      onOpenChange(false);
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Import failed: ${error.message}`);
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Form with isPending state */}
    </Dialog>
  );
}
```

**Acceptance Criteria**:
- Modal closes after successful import
- Success toast shows count
- Error toast shown on failure
- Catalog table refreshes with new listings
- Loading state shown during import

---

## Technical Specifications

### Database Changes

**Phase 1**: No migrations needed. `valuation_breakdown` JSON already stores `summary.total_adjustment`.

**Phase 2**: No migrations needed. Cascade deletes via existing relationships.

**Phase 3**: No migrations needed. Pure UI/API integration.

### API Contract Changes

**New Endpoint** (Phase 2):
```
DELETE /api/v1/listings/{id}
Response: 204 No Content
Error: 404 Not Found
```

**No Changes** to:
- GET /api/v1/listings (metrics already present)
- POST /api/v1/listings/import (reused)
- Metrics response schema (same fields, new calculation)

### Performance Considerations

- Phase 1 recalculation: ~100 listings per 2 seconds (async)
- Phase 2 delete: O(1) per listing (cascade via DB relationships)
- Phase 3 import modal: Same as current `/import` page (no perf impact)

---

## Testing Strategy

### Unit Tests (Phase 1)
- Metrics calculation with delta formula
- Metrics with missing valuation_breakdown
- Metrics with zero adjustment

### Integration Tests (All Phases)
- Phase 1: Full rule evaluation → metrics recalculation pipeline
- Phase 2: Delete listing → verify cascade deletes components, scores, field values
- Phase 3: Import via modal → verify refresh and catalog updates

### E2E Tests (All Phases)
- Phase 1: UI displays correct adjusted metrics after rule application
- Phase 2: Delete from modal and page → catalog updates
- Phase 3: Import from catalog → new listings appear in table

### Accessibility Tests (Phase 2)
- Confirmation dialog: Tab navigation, focus trap, Esc to cancel
- Keyboard: Enter to confirm delete

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Adjusted metrics change breaks existing queries/dashboards | HIGH | Task 1.2 audit prevents missed usages. Metrics now match user expectations. |
| Cascade delete removes unintended records | HIGH | Verify SQLAlchemy relationships have correct cascade config before Phase 2. Test delete thoroughly. |
| Bulk recalculation script fails mid-run | MEDIUM | Add transaction handling and progress checkpoints. Can re-run safely. |
| Import modal latency impacts UX | LOW | Reuse existing import service (no performance regression). Test modal load time. |

---

## Validation Checklist

Before release, verify:

- [ ] Phase 1: Metrics calculation fix applied to `calculate_cpu_performance_metrics()`
- [ ] Phase 1: All code usages of adjusted metrics audited and documented
- [ ] Phase 1: Unit tests pass (5+ test cases for metrics)
- [ ] Phase 1: Integration test passes (full pipeline with rules)
- [ ] Phase 1: Bulk recalculation script runs successfully on test data
- [ ] Phase 2: DELETE `/api/v1/listings/{id}` endpoint implemented and returns 204
- [ ] Phase 2: Cascade deletes verified (components, scores, field values)
- [ ] Phase 2: Delete button present in detail modal and page
- [ ] Phase 2: Confirmation dialog shows before deletion
- [ ] Phase 2: Cache invalidates after successful delete
- [ ] Phase 2: Confirmation dialog is keyboard accessible (Tab, Esc, Enter)
- [ ] Phase 3: ImportModal component extracted and reusable
- [ ] Phase 3: Import button visible in catalog header
- [ ] Phase 3: Import modal opens/closes correctly
- [ ] Phase 3: Catalog refreshes after successful import
- [ ] Phase 3: Success/error toasts display correctly
- [ ] All phases: E2E tests pass
- [ ] All phases: No console errors or warnings
- [ ] Code review completed
- [ ] Documentation updated (if needed)
- [ ] Staging deployment tested
- [ ] Ready for production release

---

## Dependencies & Blockers

None identified. Phases are independent:
- Phase 1 can start immediately (backend only)
- Phase 2 can start after Phase 1 validation (delete endpoint doesn't depend on metrics fix)
- Phase 3 can start after Phase 1 validation (import doesn't depend on metrics or delete)

---

## Success Criteria

| Goal | Success Metric | Phase |
|------|---|---|
| Accurate CPU valuation | All adjusted metrics tests pass; audit shows no conflicts | 1 |
| Self-service deletion | Delete endpoint works; cascade deletes clean; UI accessible | 2 |
| Streamlined import workflow | Import button in catalog; modal works; refresh automatic | 3 |

