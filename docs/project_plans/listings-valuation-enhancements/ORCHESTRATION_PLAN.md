# Orchestration Plan: Listing Valuation & Management Enhancements

**Lead Architect:** lead-architect agent
**Date:** 2025-11-01
**Status:** Ready for Execution
**ADR:** [ADR-007](/mnt/containers/deal-brain/docs/architecture/decisions/ADR-007-listings-valuation-enhancements-orchestration.md)

---

## Executive Summary

This document provides the comprehensive orchestration strategy for executing Phases 1-3 of the Listing Valuation & Management Enhancements. It defines:

1. Architectural decisions and constraints
2. Subagent delegation mapping
3. Execution order and parallelism opportunities
4. Commit strategy and validation checkpoints
5. Risk mitigation approaches

**Timeline:** 2-3 weeks (4-5 days Phase 1, 3-4 days Phase 2, 2-3 days Phase 3)

**Parallelism:** Phases 2 and 3 can run in parallel after Phase 1 validation.

---

## Phase 1: Adjusted Valuation Calculation Fix (CRITICAL)

**Priority:** CRITICAL – Fixes data accuracy bug affecting user trust
**Timeline:** 4-5 days
**Dependencies:** None (can start immediately)

### Architectural Constraints

1. **Location:** Keep calculation in `apps/api/dealbrain_api/services/listings.py`
   - **NOT** in `packages/core` (this is orchestration logic, not pure domain logic)

2. **Formula:**
   ```python
   # Extract from valuation_breakdown JSON
   total_adjustment = listing.valuation_breakdown.get('summary', {}).get('total_adjustment', 0.0)

   # Calculate adjusted base price
   adjusted_base_price = base_price - total_adjustment

   # Compute metrics
   metric_single_adjusted = adjusted_base_price / cpu.cpu_mark_single
   metric_multi_adjusted = adjusted_base_price / cpu.cpu_mark_multi
   ```

3. **Error Handling:**
   - Default `total_adjustment` to `0.0` if `valuation_breakdown` is None
   - Default `total_adjustment` to `0.0` if `summary` key missing
   - Return empty dict if CPU or benchmarks missing

### Task Delegation Map

#### Task 1.1: Fix CPU Performance Metrics Calculation

**Subagent:** `python-backend-engineer`

**Delegation Command:**
```markdown
Task("python-backend-engineer", "Fix CPU performance metrics calculation in apps/api/dealbrain_api/services/listings.py:

CURRENT BUG (lines 706-734):
- Incorrectly uses adjusted_price instead of (base_price - adjustment_delta)
- Affects both single-thread and multi-thread adjusted metrics

REQUIRED FIX:
1. Extract total_adjustment from listing.valuation_breakdown['summary']['total_adjustment']
2. Default to 0.0 if valuation_breakdown is None or missing keys
3. Calculate: adjusted_base_price = base_price - total_adjustment
4. Update metrics:
   - dollar_per_cpu_mark_single_adjusted = adjusted_base_price / cpu.cpu_mark_single
   - dollar_per_cpu_mark_multi_adjusted = adjusted_base_price / cpu.cpu_mark_multi
5. Keep base metrics unchanged (already correct)
6. Handle missing CPU or benchmark data gracefully

CONSTRAINTS:
- NO schema migration required
- NO changes to packages/core (this is service layer orchestration)
- Follow async SQLAlchemy patterns
- Maintain existing function signature

VALIDATION:
- All four metric keys present in output
- Graceful handling of None valuation_breakdown
- No breaking changes to response schema")
```

**Files to Modify:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/listings.py` (lines 706-734)

**Validation Criteria:**
- [ ] Adjusted metrics use `(base_price - adjustment_delta)` formula
- [ ] All four metric keys updated
- [ ] Handles missing `valuation_breakdown` gracefully
- [ ] No schema migration required

**Commit After:** Yes
**Commit Message:** `feat(api): fix CPU adjusted metrics calculation formula`

---

#### Task 1.2: Audit All Usages of Adjusted Metrics Fields

**Subagent:** `codebase-explorer`

**Delegation Command:**
```markdown
Task("codebase-explorer", "Find all usages of CPU adjusted metrics fields:

SEARCH TERMS:
- dollar_per_cpu_mark_single_adjusted
- dollar_per_cpu_mark_multi_adjusted

SCOPE:
- Backend: apps/api/dealbrain_api/api/schemas/
- Frontend: apps/web/types/, apps/web/app/, apps/web/components/
- Tests: tests/

OUTPUT FORMAT:
Create table with columns:
| File | Line | Usage Context | Interpretation | Action Needed |

ANALYSIS:
- Verify each usage correctly interprets metric as 'CPU value after component adjustments'
- Identify any conflicting interpretations
- Note any display transformations or comparisons
- Flag any usage that might break with new calculation

DELIVERABLE:
- Comprehensive audit table in progress tracker
- Summary: 'All usages reviewed, no conflicts found' or list of conflicts")
```

**Known Files from grep (starting point):**
- `apps/web/app/listings/_components/grid-view/index.tsx` (sorting)
- `apps/web/app/listings/_components/grid-view/listing-card.tsx` (display)
- `apps/web/app/listings/_components/dense-list-view/index.tsx` (sorting)
- `apps/web/app/listings/_components/dense-list-view/dense-table.tsx` (display)
- `apps/web/app/listings/_components/master-detail-view/compare-drawer.tsx` (comparison)
- `apps/web/app/listings/_components/master-detail-view/index.tsx` (sorting)
- `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx` (display)
- `apps/web/components/listings/listing-details-dialog.tsx` (display)
- `apps/web/components/listings/listing-overview-modal.tsx` (display)
- `apps/web/components/listings/listings-table.tsx` (display)

**Validation Criteria:**
- [ ] All 10+ files reviewed
- [ ] No conflicting interpretations found
- [ ] Comments updated where needed
- [ ] Audit table documented in progress tracker

**Commit After:** No (documentation tracked in progress.md)

---

#### Task 1.3: Update Test Coverage

**Subagent:** `python-backend-engineer`

**Delegation Command:**
```markdown
Task("python-backend-engineer", "Create comprehensive test suite for CPU metrics calculation:

FILE: Create tests/test_listing_metrics.py

TEST CASES (5 minimum):

1. test_cpu_metrics_delta_calculation:
   - Listing with $500 base price, $100 RAM deduction
   - Assert: adjusted_base = 500 - 100 = 400
   - Assert: metric = 400 / cpu_mark

2. test_cpu_metrics_no_adjustment:
   - Listing with zero adjustment
   - Assert: adjusted_base = base_price
   - Assert: base and adjusted metrics equal

3. test_cpu_metrics_missing_valuation_breakdown:
   - Listing with valuation_breakdown = None
   - Assert: Gracefully defaults adjustment to 0.0
   - Assert: Metrics calculated with base_price

4. test_cpu_metrics_multiple_adjustments:
   - Listing with $50 RAM + $30 storage deduction
   - Assert: adjustment_delta = 80
   - Assert: Metric uses (base - 80)

5. test_cpu_metrics_integration_with_rules:
   - Full rule evaluation pipeline
   - Assert: Metrics recalculated after rules applied
   - Assert: Breakdown contains expected adjustments

ADDITIONAL TEST: tests/test_ingestion_metrics_calculation.py
- Integration test: metrics recalculation after import with active rules

REQUIREMENTS:
- Use pytest.mark.asyncio for async tests
- Use AsyncSession fixtures from conftest.py
- Target ≥95% code coverage for calculate_cpu_performance_metrics()
- Follow existing test patterns in tests/

VALIDATION:
- All 5+ test cases pass
- Code coverage report shows ≥95%
- Integration test covers full pipeline")
```

**Files to Create/Modify:**
- `/mnt/containers/deal-brain/tests/test_listing_metrics.py` (create)
- `/mnt/containers/deal-brain/tests/test_ingestion_metrics_calculation.py` (add test)

**Validation Criteria:**
- [ ] 5+ new test cases pass
- [ ] Integration test covers full pipeline
- [ ] Code coverage for metrics function ≥95%

**Commit After:** Yes
**Commit Message:** `test(api): add comprehensive CPU metrics test coverage`

---

#### Task 1.4: Bulk Recalculation Script

**Subagent:** `python-backend-engineer`

**Delegation Command:**
```markdown
Task("python-backend-engineer", "Create bulk recalculation script for existing listings:

FILE: Create scripts/recalculate_adjusted_metrics.py

REQUIREMENTS:
1. Query all listings with assigned CPU (cpu_id is not None)
2. Use async SQLAlchemy with proper session management
3. Call update_listing_metrics(session, listing_id) for each
4. Add progress logging every 100 listings
5. Add completion summary: 'Recalculated metrics for {count} listings'
6. Handle errors gracefully (log and continue)
7. Use transaction batching (commit every 100)

IMPLEMENTATION PATTERN:
```python
import asyncio
from sqlalchemy import select
from apps.api.dealbrain_api.db import async_sessionmaker, engine
from apps.api.dealbrain_api.models.core import Listing
from apps.api.dealbrain_api.services.listings import update_listing_metrics

async def main():
    async_session = async_sessionmaker(engine)
    async with async_session() as session:
        stmt = select(Listing).where(Listing.cpu_id.isnot(None))
        result = await session.execute(stmt)
        listings = result.scalars().all()

        for i, listing in enumerate(listings, 1):
            try:
                await update_listing_metrics(session, listing.id)
                if i % 100 == 0:
                    await session.commit()
                    print(f'Recalculated {i}/{len(listings)}')
            except Exception as e:
                print(f'Error recalculating listing {listing.id}: {e}')
                continue

        await session.commit()
        print(f'Done: Recalculated metrics for {len(listings)} listings')

if __name__ == '__main__':
    asyncio.run(main())
```

VALIDATION:
- Test on development data (10+ listings)
- Verify progress logging works
- Verify summary output clear
- Safe for staging/production")
```

**Files to Create:**
- `/mnt/containers/deal-brain/scripts/recalculate_adjusted_metrics.py`

**Validation Criteria:**
- [ ] Script successfully recalculates all listings
- [ ] Progress logging works (every 100)
- [ ] Summary output clear
- [ ] Tested on development data
- [ ] Safe for staging/production

**Commit After:** Yes
**Commit Message:** `chore(scripts): add bulk metrics recalculation script`

---

### Phase 1 Validation Checkpoint

**BEFORE proceeding to Phases 2 & 3, verify:**

- [ ] All 4 metrics fields use new formula
- [ ] Unit tests pass (≥95% coverage)
- [ ] Integration test passes
- [ ] Audit documented (10+ files reviewed, no conflicts)
- [ ] Recalculation script tested on development data
- [ ] No regressions in existing metrics display (manual testing)
- [ ] All Phase 1 commits merged to branch

**Validation Command:**
```bash
# Run tests
poetry run pytest tests/test_listing_metrics.py -v
poetry run pytest tests/test_ingestion_metrics_calculation.py -v

# Check coverage
poetry run pytest tests/ --cov=dealbrain_api.services.listings --cov-report=term

# Test recalculation script
poetry run python scripts/recalculate_adjusted_metrics.py

# Verify no breaking changes
make test
```

---

## Phase 2: Delete Listing Functionality (HIGH)

**Priority:** HIGH – Enables self-service data cleanup
**Timeline:** 3-4 days
**Dependencies:** Phase 1 validation complete
**Parallelism:** Can run in parallel with Phase 3

### Architectural Constraints

1. **Cascade Strategy:** SQLAlchemy ORM-level cascades (NOT database FK cascades)
   - `Listing.components` → `cascade='all, delete-orphan'` (already configured)
   - `Listing.score_history` → `cascade='all, delete-orphan'` (already configured)
   - **Verify:** EntityFieldValue cascade configuration

2. **Delete Endpoint Pattern:**
   ```python
   @router.delete('/listings/{listing_id}', status_code=204)
   async def delete_listing(listing_id: int, session: AsyncSession = Depends(session_dependency)):
       listing = await session.get(Listing, listing_id)
       if not listing:
           raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")
       await session.delete(listing)
       await session.commit()
   ```

3. **Cache Invalidation Pattern:**
   ```typescript
   queryClient.invalidateQueries({ queryKey: ['listings'] });
   ```

4. **Confirmation Dialog Requirements:**
   - `role="alertdialog"` for accessibility
   - Focus trap and keyboard navigation (Tab, Shift+Tab, Enter, Esc)
   - Destructive styling variant
   - Proper ARIA labels

### Task Delegation Map

#### Task 2.1: Backend Delete Endpoint

**Subagent:** `python-backend-engineer`

**Delegation Command:**
```markdown
Task("python-backend-engineer", "Implement DELETE endpoint for listings:

ENDPOINT: DELETE /api/v1/listings/{listing_id}

FILE: apps/api/dealbrain_api/api/listings.py

IMPLEMENTATION:
1. Add DELETE route handler:
   - Path: /listings/{listing_id}
   - Status code: 204 No Content on success
   - Response: None

2. Add service method to apps/api/dealbrain_api/services/listings.py:
   ```python
   async def delete_listing(session: AsyncSession, listing_id: int) -> None:
       listing = await session.get(Listing, listing_id)
       if not listing:
           raise ValueError(f'Listing {listing_id} not found')
       await session.delete(listing)
       await session.commit()
   ```

3. Verify cascade deletes in apps/api/dealbrain_api/models/core.py:
   - Listing.components has cascade='all, delete-orphan' ✓
   - Listing.score_history has cascade='all, delete-orphan' ✓
   - Check EntityFieldValue cascade (custom fields)

4. Route handler:
   - Call delete_listing service method
   - Return 204 on success
   - Catch ValueError and return 404

CONSTRAINTS:
- Use async SQLAlchemy patterns
- Follow Deal Brain layered architecture
- Proper error handling with HTTP status codes
- No database migration required

VALIDATION:
- Test with valid listing ID → 204
- Test with invalid listing ID → 404
- Verify all related records deleted (components, scores, field values)")
```

**Files to Modify:**
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/listings.py`
- `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/listings.py`

**Validation Criteria:**
- [ ] DELETE endpoint returns 204 on success
- [ ] Returns 404 if listing not found
- [ ] All related records deleted
- [ ] Service handles errors gracefully
- [ ] Endpoint tested with valid and invalid IDs

**Commit After:** Yes
**Commit Message:** `feat(api): add DELETE endpoint for listings`

---

#### Task 2.4: Confirmation Dialog Component (Start in Parallel with 2.1)

**Subagent:** `ui-engineer`

**Delegation Command:**
```markdown
Task("ui-engineer", "Create accessible confirmation dialog component:

FILE: Create apps/web/components/ui/confirmation-dialog.tsx

REQUIREMENTS:
- Accessible: role='alertdialog', focus trap, keyboard support
- Keyboard navigation:
  - Tab/Shift+Tab for focus movement
  - Enter to confirm
  - Esc to cancel
- Props interface:
  ```typescript
  interface ConfirmationDialogProps {
    title: string;
    description: string;
    confirmText: string;
    cancelText?: string;
    onConfirm: () => void;
    onCancel?: () => void;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    isDangerous?: boolean; // For destructive styling
  }
  ```

IMPLEMENTATION:
- Use Radix UI Dialog or AlertDialog primitives
- Variants: Destructive (red) for delete, Default for others
- Proper ARIA attributes (aria-labelledby, aria-describedby)
- Focus management (trap + restore)
- Export component for reuse

CONSTRAINTS:
- Radix UI primitives only (headless components)
- Tailwind CSS for styling
- WCAG 2.1 AA compliance
- Reusable across multiple contexts

VALIDATION:
- Component creates and exports successfully
- Focus management works (trap + restore)
- Keyboard navigation works (Tab, Shift+Tab, Enter, Esc)
- ARIA attributes set correctly
- Destructive variant styled appropriately")
```

**Files to Create:**
- `/mnt/containers/deal-brain/apps/web/components/ui/confirmation-dialog.tsx`

**Validation Criteria:**
- [ ] Component created and exported
- [ ] Focus management works
- [ ] Keyboard navigation works
- [ ] ARIA attributes correct
- [ ] Destructive variant styled

**Commit After:** Yes
**Commit Message:** `feat(web): add accessible confirmation dialog component`

---

#### Task 2.2: Frontend Delete UI – Detail Modal (After 2.1 + 2.4)

**Subagent:** `ui-engineer`

**Delegation Command:**
```markdown
Task("ui-engineer", "Add delete functionality to listing detail modal:

FILE: apps/web/app/listings/_components/master-detail-view/detail-panel.tsx

UI LOCATION: Bottom action bar (near 'View Full Page' button)

IMPLEMENTATION:
1. Import ConfirmationDialog from components/ui/confirmation-dialog
2. Add state: const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
3. Create delete mutation:
   ```typescript
   const { mutate: deleteListing, isPending } = useMutation({
     mutationFn: async (id: number) => {
       const res = await fetch(\`\${API_URL}/listings/\${id}\`, { method: 'DELETE' });
       if (!res.ok) throw new Error('Failed to delete listing');
     },
     onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ['listings'] });
       onClose?.(); // Close modal
       toast.success('Listing deleted');
     },
     onError: (error) => {
       toast.error(\`Delete failed: \${error.message}\`);
     }
   });
   ```
4. Add delete button to action bar:
   - Variant: destructive (red)
   - Icon: Trash or similar
   - Click opens confirmation dialog
5. Add ConfirmationDialog:
   - title: 'Delete Listing?'
   - description: 'This action cannot be undone. All data will be permanently removed.'
   - confirmText: 'Delete'
   - isDangerous: true
   - onConfirm: () => deleteListing(listing.id)

CONSTRAINTS:
- React Query for mutations
- Cache invalidation after success
- Toast notifications for feedback
- Close modal after successful delete
- Loading state during deletion

VALIDATION:
- Delete button visible and styled (red/destructive)
- Confirmation dialog shows before deletion
- Mutation calls correct endpoint
- Cache invalidates after success
- Error toast shown on failure
- Modal closes after successful delete")
```

**Files to Modify:**
- `/mnt/containers/deal-brain/apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`

**Validation Criteria:**
- [ ] Delete button visible and styled
- [ ] Confirmation dialog shows
- [ ] Mutation calls correct endpoint
- [ ] Cache invalidates
- [ ] Error toast on failure
- [ ] Modal closes on success

**Commit After:** Wait for Task 2.3

---

#### Task 2.3: Frontend Delete UI – Detail Page (After 2.1 + 2.4, Parallel with 2.2)

**Subagent:** `ui-engineer`

**Delegation Command:**
```markdown
Task("ui-engineer", "Add delete functionality to listing detail page:

FILE: apps/web/app/listings/[id]/page.tsx

UI LOCATION: Top right header (near metadata section)

IMPLEMENTATION:
1. Import ConfirmationDialog from components/ui/confirmation-dialog
2. Import useRouter from next/navigation
3. Add state: const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
4. Create delete mutation (similar to Task 2.2):
   ```typescript
   const router = useRouter();
   const { mutate: deleteListing, isPending } = useMutation({
     mutationFn: async (id: number) => {
       const res = await fetch(\`\${API_URL}/listings/\${id}\`, { method: 'DELETE' });
       if (!res.ok) throw new Error('Failed to delete');
     },
     onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ['listings'] });
       toast.success('Listing deleted');
       router.push('/listings'); // Navigate to catalog
     },
     onError: (error) => {
       toast.error(\`Delete failed: \${error.message}\`);
     }
   });
   ```
5. Add delete button to page header:
   - Variant: ghost or destructive
   - Icon: Trash
   - disabled: isPending
6. Reuse ConfirmationDialog (same props as Task 2.2)

CONSTRAINTS:
- Navigate to /listings on success
- Show loading state during deletion (isPending)
- React Query cache invalidation
- Toast notifications for feedback

VALIDATION:
- Delete button visible in page header
- Confirmation dialog appears before deletion
- Navigation to /listings on success
- Loading state shown during deletion
- Error handled gracefully")
```

**Files to Modify:**
- `/mnt/containers/deal-brain/apps/web/app/listings/[id]/page.tsx`

**Validation Criteria:**
- [ ] Delete button in header
- [ ] Confirmation dialog shows
- [ ] Navigation to /listings works
- [ ] Loading state during deletion
- [ ] Error handled gracefully

**Commit After:** Yes (combine with Task 2.2)
**Commit Message:** `feat(web): add delete functionality to listing detail views`

---

### Phase 2 Validation Checkpoint

**BEFORE marking Phase 2 complete, verify:**

- [ ] DELETE endpoint returns 204 for valid ID
- [ ] DELETE endpoint returns 404 for invalid ID
- [ ] Cascade deletes verified (components, scores, field values)
- [ ] Delete button visible in both detail views
- [ ] Confirmation dialog is keyboard accessible (Tab, Esc, Enter)
- [ ] Cache invalidation works correctly
- [ ] Navigation to /listings works from detail page
- [ ] No console errors or warnings
- [ ] All Phase 2 commits merged to branch

**Validation Commands:**
```bash
# Backend tests
poetry run pytest -k delete

# Frontend type checking
pnpm --filter "./apps/web" typecheck

# Frontend build
pnpm --filter "./apps/web" build
```

---

## Phase 3: Import Button in Catalog View (MEDIUM)

**Priority:** MEDIUM – Improves workflow but not data critical
**Timeline:** 2-3 days
**Dependencies:** Phase 1 validation complete
**Parallelism:** Can run in parallel with Phase 2

### Architectural Constraints

1. **Component Location:** `apps/web/components/listings/import-modal.tsx`
   - Domain-specific component (NOT generic UI)
   - Reusable across multiple contexts

2. **Props Interface:**
   ```typescript
   interface ImportModalProps {
     open: boolean;
     onOpenChange: (open: boolean) => void;
     onSuccess?: () => void;
   }
   ```

3. **Cache Invalidation:**
   ```typescript
   queryClient.invalidateQueries({ queryKey: ['listings'] });
   ```

4. **No Performance Regression:** Reuse existing import service

### Task Delegation Map

#### Task 3.1: Extract Import Modal to Shared Component

**Subagent:** `ui-engineer`

**Delegation Command:**
```markdown
Task("ui-engineer", "Extract import modal from /import page to shared component:

SOURCE FILE: apps/web/app/import/page.tsx
TARGET FILE: Create apps/web/components/listings/import-modal.tsx

REQUIREMENTS:
1. Extract import UI (form, tabs for URL/file, upload handler)
2. Create ImportModal component with props:
   ```typescript
   interface ImportModalProps {
     open: boolean;
     onOpenChange: (open: boolean) => void;
     onSuccess?: () => void;
   }
   ```
3. Keep all validation and import service logic (no changes)
4. Reuse existing import mutation
5. On success:
   - Close modal: onOpenChange(false)
   - Call optional onSuccess callback
   - Show success toast with import count
6. On error:
   - Keep modal open
   - Show error toast

IMPLEMENTATION:
- Use Radix Dialog for modal
- Tabs for URL/file import methods
- Keep existing form validation
- Maintain loading states
- Export component

CONSTRAINTS:
- No changes to import service logic
- Reusable in multiple contexts
- Props documented with JSDoc
- Maintain existing UX patterns

VALIDATION:
- Component extracts cleanly
- Props documented
- Import logic unchanged
- Reusable in multiple contexts")
```

**Files to Create:**
- `/mnt/containers/deal-brain/apps/web/components/listings/import-modal.tsx`

**Files to Reference:**
- `/mnt/containers/deal-brain/apps/web/app/import/page.tsx` (source)

**Validation Criteria:**
- [ ] Component extracts cleanly
- [ ] Props documented
- [ ] Import logic unchanged
- [ ] Reusable across contexts

**Commit After:** Yes
**Commit Message:** `refactor(web): extract import modal to shared component`

---

#### Task 3.2: Add Import Button to Catalog Header (After 3.1)

**Subagent:** `ui-engineer`

**Delegation Command:**
```markdown
Task("ui-engineer", "Add import button to catalog header:

FILE: apps/web/app/listings/page.tsx

UI LOCATION: Top right, next to 'Add Listing' button

IMPLEMENTATION:
1. Import ImportModal from components/listings/import-modal
2. Import Upload icon from lucide-react
3. Add state: const [importModalOpen, setImportModalOpen] = useState(false)
4. Add import button in header:
   ```typescript
   <Button onClick={() => setImportModalOpen(true)}>
     <Upload className='w-4 h-4 mr-2' />
     Import
   </Button>
   ```
5. Add ImportModal component:
   ```typescript
   <ImportModal
     open={importModalOpen}
     onOpenChange={setImportModalOpen}
     onSuccess={() => queryClient.invalidateQueries({ queryKey: ['listings'] })}
   />
   ```

CONSTRAINTS:
- Button styled consistently with existing action buttons
- Icon clear and intuitive (Upload)
- Position next to 'Add Listing' button
- Cache invalidation on successful import

VALIDATION:
- Button visible next to 'Add Listing'
- Button styling matches design system
- Click opens modal
- Icon clear and intuitive")
```

**Files to Modify:**
- `/mnt/containers/deal-brain/apps/web/app/listings/page.tsx`

**Validation Criteria:**
- [ ] Button visible next to "Add Listing"
- [ ] Styling matches design system
- [ ] Click opens modal
- [ ] Icon clear

**Commit After:** Wait for Task 3.3

---

#### Task 3.3: Wire Up Modal Trigger and Refresh (After 3.1 + 3.2)

**Subagent:** `ui-engineer`

**Delegation Command:**
```markdown
Task("ui-engineer", "Wire up import modal trigger and refresh logic:

FILE: apps/web/components/listings/import-modal.tsx (update from Task 3.1)

REQUIREMENTS:
1. Import mutation calls existing import service
2. On success:
   - Close modal: onOpenChange(false)
   - Call optional onSuccess callback
   - Show success toast with count: toast.success(\`Imported \${result.count} listings\`)
   - Invalidate cache: queryClient.invalidateQueries({ queryKey: ['listings'] })
3. On error:
   - Show error toast: toast.error(\`Import failed: \${error.message}\`)
   - Keep modal open
4. Show loading state during import (isPending)

IMPLEMENTATION:
```typescript
const { mutate: importListings, isPending } = useMutation({
  mutationFn: async (data: ImportRequest) => {
    return await importService.import(data);
  },
  onSuccess: (result) => {
    toast.success(\`Imported \${result.count} listings\`);
    onOpenChange(false);
    queryClient.invalidateQueries({ queryKey: ['listings'] });
    onSuccess?.();
  },
  onError: (error) => {
    toast.error(\`Import failed: \${error.message}\`);
  }
});
```

CONSTRAINTS:
- Reuse existing import service (no new implementation)
- Cache invalidation after success
- Toast notifications for feedback
- Loading state during import

VALIDATION:
- Modal closes after successful import
- Success toast shows count
- Error toast on failure
- Catalog table refreshes with new listings
- Loading state shown during import")
```

**Files to Modify:**
- `/mnt/containers/deal-brain/apps/web/components/listings/import-modal.tsx`

**Validation Criteria:**
- [ ] Modal closes after success
- [ ] Success toast shows count
- [ ] Error toast on failure
- [ ] Catalog refreshes
- [ ] Loading state shown

**Commit After:** Yes (combine with Task 3.2)
**Commit Message:** `feat(web): add import button to catalog header`

---

### Phase 3 Validation Checkpoint

**BEFORE marking Phase 3 complete, verify:**

- [ ] ImportModal component extracted and reusable
- [ ] Import button visible in catalog header
- [ ] Import modal opens/closes correctly
- [ ] Catalog refreshes after successful import
- [ ] Success/error toasts display correctly
- [ ] No performance regression vs. current /import page
- [ ] No console errors or warnings
- [ ] All Phase 3 commits merged to branch

**Validation Commands:**
```bash
# Frontend type checking
pnpm --filter "./apps/web" typecheck

# Frontend build
pnpm --filter "./apps/web" build

# Test import flow manually
pnpm --filter "./apps/web" dev
```

---

## Execution Timeline

### Week 1: Phase 1 (Days 1-5)

| Day | Tasks | Commits |
|-----|-------|---------|
| 1 | Task 1.1: Fix metrics calculation | ✓ Commit after 1.1 |
| 2 | Task 1.2: Audit usages | (No commit - doc in progress.md) |
| 3-4 | Task 1.3: Test coverage | ✓ Commit after 1.3 |
| 5 | Task 1.4: Recalculation script + validation | ✓ Commit after 1.4 |

**Milestone:** Phase 1 validation checkpoint complete

### Week 2: Phases 2 & 3 (Parallel) (Days 6-12)

**Phase 2 Track:**

| Day | Tasks | Commits |
|-----|-------|---------|
| 6 | Task 2.1: Backend endpoint | ✓ Commit after 2.1 |
| 6 | Task 2.4: Confirmation dialog (parallel) | ✓ Commit after 2.4 |
| 7-8 | Task 2.2: Detail modal UI | (Wait for 2.3) |
| 7-8 | Task 2.3: Detail page UI (parallel) | ✓ Commit after 2.2+2.3 |
| 9 | Phase 2 validation | - |

**Phase 3 Track:**

| Day | Tasks | Commits |
|-----|-------|---------|
| 10 | Task 3.1: Extract modal | ✓ Commit after 3.1 |
| 11 | Task 3.2: Add button | (Wait for 3.3) |
| 11 | Task 3.3: Wire trigger (parallel) | ✓ Commit after 3.2+3.3 |
| 12 | Phase 3 validation | - |

**Milestone:** All phases complete

### Week 3: Integration & Release (Days 13-15)

| Day | Activities |
|-----|-----------|
| 13 | E2E testing, manual QA |
| 14 | Staging deployment, bulk recalculation |
| 15 | Production release |

---

## Risk Mitigation Summary

| Risk | Impact | Mitigation | Owner |
|------|--------|-----------|-------|
| Metrics change breaks dashboards | HIGH | Task 1.2 audit + manual testing | lead-architect |
| Cascade delete removes unintended records | HIGH | Verify relationships before Phase 2 | python-backend-engineer |
| Bulk recalculation fails mid-run | MEDIUM | Transaction batching + error handling | python-backend-engineer |
| Import modal latency | LOW | Reuse existing service | ui-engineer |

---

## Success Criteria

### Phase 1
- [ ] All adjusted metrics tests pass
- [ ] Audit shows no conflicts (10+ files reviewed)
- [ ] Code coverage ≥95%
- [ ] Recalculation script tested successfully

### Phase 2
- [ ] Delete endpoint works (204/404)
- [ ] Cascade deletes clean
- [ ] UI accessible (WCAG 2.1 AA)
- [ ] Cache invalidation works

### Phase 3
- [ ] Import button in catalog
- [ ] Modal works and refreshes catalog
- [ ] No performance regression

### Overall
- [ ] All E2E tests pass
- [ ] No console errors/warnings
- [ ] Code review completed
- [ ] Staging deployment successful
- [ ] Ready for production release

---

## Delegation Summary

**Total Subagents:** 2
- `python-backend-engineer`: 5 tasks (Phase 1: 3, Phase 2: 1)
- `ui-engineer`: 5 tasks (Phase 2: 3, Phase 3: 3)
- `codebase-explorer`: 1 task (Phase 1: 1)

**Total Commits:** 8
- Phase 1: 3 commits
- Phase 2: 3 commits
- Phase 3: 2 commits

**Total Timeline:** 2-3 weeks (4-5 + 3-4 + 2-3 days)

---

## Next Steps

1. **Start Phase 1, Task 1.1:** Delegate to `python-backend-engineer`
2. **Monitor Progress:** Update progress tracker after each task
3. **Phase 1 Validation:** Run validation checkpoint before Phase 2/3
4. **Parallel Execution:** Start Phases 2 & 3 in parallel
5. **Final Integration:** E2E testing and staging deployment

**Ready to begin execution.** 🚀
