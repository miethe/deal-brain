# Quick Reference: Execution Commands

**For:** Execution orchestrator (general-purpose agent or human developer)
**Date:** 2025-11-01

---

## Phase 1: Adjusted Valuation Calculation Fix

### Task 1.1: Fix Metrics Calculation
```bash
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

CONSTRAINTS:
- NO schema migration required
- NO changes to packages/core
- Follow async SQLAlchemy patterns

VALIDATION:
- All four metric keys present in output
- Graceful handling of None valuation_breakdown")
```

**Commit:** `feat(api): fix CPU adjusted metrics calculation formula`

---

### Task 1.2: Audit Metrics Usage
```bash
Task("codebase-explorer", "Find all usages of CPU adjusted metrics fields:

SEARCH TERMS:
- dollar_per_cpu_mark_single_adjusted
- dollar_per_cpu_mark_multi_adjusted

OUTPUT FORMAT:
Create table with columns:
| File | Line | Usage Context | Interpretation | Action Needed |

DELIVERABLE:
- Comprehensive audit table in progress tracker
- Summary: 'All usages reviewed, no conflicts found' or list of conflicts")
```

**Commit:** No commit (document in progress tracker)

---

### Task 1.3: Test Coverage
```bash
Task("python-backend-engineer", "Create comprehensive test suite for CPU metrics calculation:

FILE: Create tests/test_listing_metrics.py

TEST CASES (5 minimum):
1. test_cpu_metrics_delta_calculation - $500 base, $100 deduction
2. test_cpu_metrics_no_adjustment - zero adjustment
3. test_cpu_metrics_missing_valuation_breakdown - None breakdown
4. test_cpu_metrics_multiple_adjustments - $50 + $30 deductions
5. test_cpu_metrics_integration_with_rules - full pipeline

REQUIREMENTS:
- Use pytest.mark.asyncio for async tests
- Target ≥95% code coverage")
```

**Commit:** `test(api): add comprehensive CPU metrics test coverage`

---

### Task 1.4: Recalculation Script
```bash
Task("python-backend-engineer", "Create bulk recalculation script for existing listings:

FILE: Create scripts/recalculate_adjusted_metrics.py

REQUIREMENTS:
1. Query all listings with CPU (cpu_id is not None)
2. Use async SQLAlchemy with proper session management
3. Call update_listing_metrics(session, listing_id) for each
4. Progress logging every 100 listings
5. Transaction batching (commit every 100)

VALIDATION:
- Test on development data (10+ listings)")
```

**Commit:** `chore(scripts): add bulk metrics recalculation script`

---

### Phase 1 Validation
```bash
poetry run pytest tests/test_listing_metrics.py -v
poetry run pytest tests/ --cov=dealbrain_api.services.listings --cov-report=term
poetry run python scripts/recalculate_adjusted_metrics.py
make test
```

---

## Phase 2: Delete Listing Functionality

### Task 2.1: Backend Delete Endpoint
```bash
Task("python-backend-engineer", "Implement DELETE endpoint for listings:

ENDPOINT: DELETE /api/v1/listings/{listing_id}
FILE: apps/api/dealbrain_api/api/listings.py

IMPLEMENTATION:
1. Add DELETE route handler (204 on success, 404 on not found)
2. Add service method to apps/api/dealbrain_api/services/listings.py
3. Verify cascade deletes in models/core.py

VALIDATION:
- Test with valid listing ID → 204
- Test with invalid listing ID → 404
- Verify all related records deleted")
```

**Commit:** `feat(api): add DELETE endpoint for listings`

---

### Task 2.4: Confirmation Dialog (Parallel with 2.1)
```bash
Task("ui-engineer", "Create accessible confirmation dialog component:

FILE: Create apps/web/components/ui/confirmation-dialog.tsx

REQUIREMENTS:
- Accessible: role='alertdialog', focus trap, keyboard support
- Keyboard: Tab/Shift+Tab, Enter to confirm, Esc to cancel
- Variants: Destructive (red) for delete
- Use Radix UI Dialog or AlertDialog primitives

VALIDATION:
- Focus management works
- Keyboard navigation works
- ARIA attributes correct")
```

**Commit:** `feat(web): add accessible confirmation dialog component`

---

### Task 2.2: Detail Modal Delete (After 2.1 + 2.4)
```bash
Task("ui-engineer", "Add delete functionality to listing detail modal:

FILE: apps/web/app/listings/_components/master-detail-view/detail-panel.tsx

IMPLEMENTATION:
1. Add delete button to action bar (variant: destructive)
2. Create delete mutation with useMutation
3. Wire to ConfirmationDialog
4. Invalidate cache on success
5. Close modal on success

VALIDATION:
- Confirmation dialog shows before deletion
- Cache invalidates after success")
```

**Commit:** Wait for Task 2.3

---

### Task 2.3: Detail Page Delete (Parallel with 2.2)
```bash
Task("ui-engineer", "Add delete functionality to listing detail page:

FILE: apps/web/app/listings/[id]/page.tsx

IMPLEMENTATION:
1. Add delete button to page header
2. Create delete mutation (similar to 2.2)
3. Navigate to /listings on success
4. Show loading state (isPending)

VALIDATION:
- Navigation to /listings works
- Loading state during deletion")
```

**Commit:** `feat(web): add delete functionality to listing detail views` (combine with 2.2)

---

### Phase 2 Validation
```bash
poetry run pytest -k delete
pnpm --filter "./apps/web" typecheck
pnpm --filter "./apps/web" build
```

---

## Phase 3: Import Button in Catalog

### Task 3.1: Extract Import Modal
```bash
Task("ui-engineer", "Extract import modal from /import page to shared component:

SOURCE FILE: apps/web/app/import/page.tsx
TARGET FILE: Create apps/web/components/listings/import-modal.tsx

REQUIREMENTS:
1. Extract import UI (form, tabs, upload handler)
2. Props: open, onOpenChange, onSuccess
3. Keep existing import service logic
4. On success: close modal, call onSuccess, show toast

VALIDATION:
- Component extracts cleanly
- Props documented
- Reusable across contexts")
```

**Commit:** `refactor(web): extract import modal to shared component`

---

### Task 3.2: Add Import Button (After 3.1)
```bash
Task("ui-engineer", "Add import button to catalog header:

FILE: apps/web/app/listings/page.tsx

IMPLEMENTATION:
1. Import ImportModal component
2. Add state for modal open/close
3. Add import button (Upload icon, next to 'Add Listing')
4. Add ImportModal component with onSuccess callback

VALIDATION:
- Button visible and styled consistently
- Click opens modal")
```

**Commit:** Wait for Task 3.3

---

### Task 3.3: Wire Modal Trigger (After 3.1 + 3.2)
```bash
Task("ui-engineer", "Wire up import modal trigger and refresh logic:

FILE: apps/web/components/listings/import-modal.tsx

IMPLEMENTATION:
1. Import mutation calls existing service
2. On success: close modal, show toast with count, invalidate cache
3. On error: show error toast, keep modal open
4. Show loading state (isPending)

VALIDATION:
- Modal closes after success
- Catalog refreshes with new listings
- Success/error toasts display")
```

**Commit:** `feat(web): add import button to catalog header` (combine with 3.2)

---

### Phase 3 Validation
```bash
pnpm --filter "./apps/web" typecheck
pnpm --filter "./apps/web" build
pnpm --filter "./apps/web" dev  # Manual testing
```

---

## Parallel Execution Opportunities

### Phase 2 Parallelism
```bash
# Start in parallel:
- Task 2.1 (Backend Delete Endpoint)
- Task 2.4 (Confirmation Dialog)

# Then start in parallel:
- Task 2.2 (Detail Modal Delete)
- Task 2.3 (Detail Page Delete)
```

### Phases 2 & 3 Parallelism
After Phase 1 validation, start both Phase 2 and Phase 3 in parallel.

---

## Final Validation

### All Phases
```bash
# Backend tests
make test

# Frontend build
pnpm --filter "./apps/web" build

# No errors/warnings
pnpm --filter "./apps/web" typecheck

# Run bulk recalculation (staging)
poetry run python scripts/recalculate_adjusted_metrics.py
```

---

## Commit Summary

**Total Commits:** 8

1. `feat(api): fix CPU adjusted metrics calculation formula`
2. `test(api): add comprehensive CPU metrics test coverage`
3. `chore(scripts): add bulk metrics recalculation script`
4. `feat(api): add DELETE endpoint for listings`
5. `feat(web): add accessible confirmation dialog component`
6. `feat(web): add delete functionality to listing detail views`
7. `refactor(web): extract import modal to shared component`
8. `feat(web): add import button to catalog header`

---

## Key Files

### Phase 1
- `apps/api/dealbrain_api/services/listings.py` (lines 706-734)
- `tests/test_listing_metrics.py` (create)
- `scripts/recalculate_adjusted_metrics.py` (create)

### Phase 2
- `apps/api/dealbrain_api/api/listings.py`
- `apps/api/dealbrain_api/services/listings.py`
- `apps/web/components/ui/confirmation-dialog.tsx` (create)
- `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`
- `apps/web/app/listings/[id]/page.tsx`

### Phase 3
- `apps/web/components/listings/import-modal.tsx` (create)
- `apps/web/app/listings/page.tsx`

---

## Success Metrics

- [ ] Phase 1: All tests pass, coverage ≥95%
- [ ] Phase 2: Delete works, cascade clean, UI accessible
- [ ] Phase 3: Import button works, catalog refreshes
- [ ] All: No console errors, builds succeed, staging tested
