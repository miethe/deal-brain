# Phase 1-3 Progress Tracker: Listing Valuation & Management Enhancements

**Plan:** docs/project_plans/listings-valuation-enhancements/IMPLEMENTATION_PLAN.md
**PRD:** docs/project_plans/listings-valuation-enhancements/PRD.md
**Started:** 2025-11-01
**Last Updated:** 2025-11-01
**Status:** In Progress

---

## Completion Status

### Phase 1: Adjusted Valuation Calculation Fix

**Priority:** CRITICAL – Fixes data accuracy issue affecting user trust
**Timeline:** 4-5 days

#### Success Criteria
- [ ] Adjusted metrics use (base_price - adjustment_delta) formula
- [ ] All four metric keys updated (single + multi, base + adjusted)
- [ ] Handles missing/None valuation_breakdown gracefully
- [ ] All code usages of adjusted metrics audited
- [ ] 5+ new test cases pass for metrics calculation
- [ ] Code coverage for metrics function ≥ 95%
- [ ] Bulk recalculation script runs successfully

#### Development Checklist

**Task 1.1: Fix CPU Performance Metrics Calculation**
- [ ] Extract total_adjustment from valuation_breakdown JSON
- [ ] Calculate adjusted_base_price = base_price - total_adjustment
- [ ] Update single-thread adjusted metric calculation
- [ ] Update multi-thread adjusted metric calculation
- [ ] Handle missing/None valuation_breakdown gracefully (default to 0.0)
- [ ] Verify no schema migration required

**File:** `apps/api/dealbrain_api/services/listings.py` (lines 706-734)

**Task 1.2: Audit All Usages of Adjusted Metrics Fields**
- [ ] Search for `dollar_per_cpu_mark_single_adjusted` references
- [ ] Search for `dollar_per_cpu_mark_multi_adjusted` references
- [ ] Review `apps/api/dealbrain_api/api/schemas/listings.py`
- [ ] Review `apps/web/types/listings.ts`
- [ ] Review `apps/web/app/listings/_components/` metrics usage
- [ ] Review `apps/web/app/dashboard/` export logic
- [ ] Review `apps/web/app/listings/_components/master-detail-view/compare-drawer.tsx`
- [ ] Update comments where semantics changed
- [ ] Document "Metric Audit Summary" table

**Task 1.3: Update Test Coverage**
- [ ] Test: `test_cpu_metrics_delta_calculation` - Listing with $100 RAM deduction
- [ ] Test: `test_cpu_metrics_no_adjustment` - Listing with zero adjustment
- [ ] Test: `test_cpu_metrics_missing_valuation_breakdown` - valuation_breakdown is None
- [ ] Test: `test_cpu_metrics_multiple_adjustments` - $50 RAM + $30 storage deduction
- [ ] Test: `test_cpu_metrics_integration_with_rules` - Full rule evaluation pipeline
- [ ] Integration test in `tests/test_ingestion_metrics_calculation.py`
- [ ] Verify code coverage ≥ 95% for metrics function

**File:** `tests/test_listing_metrics.py`

**Task 1.4: Bulk Recalculation Script**
- [ ] Create `scripts/recalculate_adjusted_metrics.py`
- [ ] Query all listings with assigned CPU
- [ ] Call update_listing_metrics for each listing
- [ ] Add progress logging (every 100 listings)
- [ ] Add completion summary logging
- [ ] Test script on test data
- [ ] Verify safe for staging/production

---

### Phase 2: Delete Listing Functionality

**Priority:** HIGH – Enables self-service data cleanup
**Timeline:** 3-4 days

#### Success Criteria
- [ ] DELETE endpoint returns 204 on success
- [ ] Returns 404 if listing not found
- [ ] All related records deleted (components, scores, field values)
- [ ] Delete button visible in detail modal and page
- [ ] Confirmation dialog shows before deletion
- [ ] Cache invalidates after successful delete
- [ ] Confirmation dialog is keyboard accessible

#### Development Checklist

**Task 2.1: Backend Delete Endpoint**
- [ ] Add DELETE endpoint to `apps/api/dealbrain_api/api/listings.py`
- [ ] Add `delete_listing()` to `apps/api/dealbrain_api/services/listings.py`
- [ ] Verify cascade deletes in `apps/api/dealbrain_api/models/core.py`:
  - [ ] `Listing.components` has `cascade='all, delete-orphan'`
  - [ ] `Listing.scores` has `cascade='all, delete-orphan'`
  - [ ] `Listing.field_values` has proper cascade
- [ ] Return 204 No Content on success
- [ ] Return 404 if listing not found
- [ ] Test with valid listing ID
- [ ] Test with invalid listing ID
- [ ] Verify all related records deleted

**Task 2.2: Frontend Delete UI – Detail Modal**
- [ ] Add delete button to action bar in `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`
- [ ] Style button with destructive variant (red)
- [ ] Create delete mutation with `useMutation`
- [ ] Wire button to confirmation dialog
- [ ] Invalidate listings cache on success
- [ ] Close modal on success
- [ ] Show success toast after deletion
- [ ] Show error toast on failure

**Task 2.3: Frontend Delete UI – Detail Page**
- [ ] Add delete button to page header in `apps/web/app/listings/[id]/page.tsx`
- [ ] Create delete mutation with loading state
- [ ] Wire to confirmation dialog (reuse from Task 2.2)
- [ ] Navigate to `/listings` on success
- [ ] Show loading state during deletion
- [ ] Invalidate cache on success
- [ ] Handle errors gracefully

**Task 2.4: Confirmation Dialog Component & Accessibility**
- [ ] Create/verify `apps/web/components/ui/confirmation-dialog.tsx`
- [ ] Implement props: title, description, confirmText, cancelText, onConfirm, onCancel, open, onOpenChange, isDangerous
- [ ] Add `role="alertdialog"` ARIA attribute
- [ ] Implement focus trap
- [ ] Support keyboard navigation:
  - [ ] Tab/Shift+Tab for focus movement
  - [ ] Enter to confirm
  - [ ] Esc to cancel
- [ ] Add destructive styling variant
- [ ] Set proper ARIA labels
- [ ] Test keyboard accessibility

---

### Phase 3: Import Button in Catalog View

**Priority:** MEDIUM – Improves workflow but not data critical
**Timeline:** 2-3 days

#### Success Criteria
- [ ] ImportModal component extracted and reusable
- [ ] Import button visible in catalog header
- [ ] Import modal opens/closes correctly
- [ ] Catalog refreshes after successful import
- [ ] Success/error toasts display correctly

#### Development Checklist

**Task 3.1: Extract Import Modal to Shared Component**
- [ ] Create `apps/web/components/listings/import-modal.tsx`
- [ ] Extract import UI from `apps/web/app/import/page.tsx`
- [ ] Define ImportModalProps interface (open, onOpenChange, onSuccess)
- [ ] Move form logic (tabs for URL/file, upload handler)
- [ ] Keep validation and import service logic
- [ ] Reuse existing import mutation
- [ ] Test component independently
- [ ] Document props

**Task 3.2: Add Import Button to Catalog Header**
- [ ] Add import button to `apps/web/app/listings/page.tsx`
- [ ] Position next to "Add Listing" button
- [ ] Add Upload icon to button
- [ ] Style consistently with design system
- [ ] Add state to control modal open/close
- [ ] Wire button click to open modal
- [ ] Add ImportModal component to page

**Task 3.3: Wire Up Modal Trigger and Refresh**
- [ ] Connect import mutation in ImportModal
- [ ] Close modal on success (call onOpenChange(false))
- [ ] Call onSuccess callback to trigger cache refresh
- [ ] Show success toast with count of imported listings
- [ ] Show error toast on failure
- [ ] Invalidate listings query cache
- [ ] Display loading state during import
- [ ] Verify catalog table refreshes with new listings

---

## Validation Checklist

Before marking phase complete, verify:

### Phase 1 Validation
- [ ] Metrics calculation fix applied to `calculate_cpu_performance_metrics()`
- [ ] All code usages of adjusted metrics audited and documented
- [ ] Unit tests pass (5+ test cases for metrics)
- [ ] Integration test passes (full pipeline with rules)
- [ ] Bulk recalculation script runs successfully on test data

### Phase 2 Validation
- [ ] DELETE `/api/v1/listings/{id}` endpoint implemented and returns 204
- [ ] Cascade deletes verified (components, scores, field values)
- [ ] Delete button present in detail modal
- [ ] Delete button present in detail page
- [ ] Confirmation dialog shows before deletion
- [ ] Cache invalidates after successful delete
- [ ] Confirmation dialog is keyboard accessible (Tab, Esc, Enter)

### Phase 3 Validation
- [ ] ImportModal component extracted and reusable
- [ ] Import button visible in catalog header
- [ ] Import modal opens/closes correctly
- [ ] Catalog refreshes after successful import
- [ ] Success/error toasts display correctly

### All Phases
- [ ] E2E tests pass
- [ ] No console errors or warnings
- [ ] Code review completed
- [ ] Documentation updated (if needed)
- [ ] Staging deployment tested
- [ ] Ready for production release

---

## Work Log

### 2025-11-01 - Session 1

**Completed:**
- Progress tracker initialized with all tasks from implementation plan
- Structured tracking for all 3 phases (11 tasks total)
- Success criteria and validation checklists defined

**Subagents Used:**
- @documentation-writer - Progress tracker creation

**Commits:**
- [Pending]

**Blockers/Issues:**
- None

**Next Steps:**
- Begin Phase 1: Task 1.1 (Fix CPU Performance Metrics Calculation)
- Consult lead-architect for orchestration strategy if needed

---

## Decisions Log

- **2025-11-01 10:00** - Executing Phases 1-3 sequentially with continuous validation
- **2025-11-01 10:00** - Using documentation-writer for ALL documentation tasks
- **2025-11-01 10:00** - Progress tracker will be updated after each task completion

---

## Files Changed

### Created
- `/mnt/containers/deal-brain/docs/project_plans/listings-valuation-enhancements/progress/phase-1-3-progress.md`

### Modified
- [To be updated as work progresses]

### Deleted
- [None]

---

## Testing Strategy Summary

### Unit Tests (Phase 1)
- Metrics calculation with delta formula
- Metrics with missing valuation_breakdown
- Metrics with zero adjustment
- Metrics with multiple adjustments
- Integration with full rule evaluation pipeline

### Integration Tests (All Phases)
- **Phase 1:** Full rule evaluation → metrics recalculation pipeline
- **Phase 2:** Delete listing → verify cascade deletes components, scores, field values
- **Phase 3:** Import via modal → verify refresh and catalog updates

### E2E Tests (All Phases)
- **Phase 1:** UI displays correct adjusted metrics after rule application
- **Phase 2:** Delete from modal and page → catalog updates
- **Phase 3:** Import from catalog → new listings appear in table

### Accessibility Tests (Phase 2)
- Confirmation dialog: Tab navigation, focus trap, Esc to cancel
- Keyboard: Enter to confirm delete

---

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|-----------|--------|
| Adjusted metrics change breaks existing queries/dashboards | HIGH | Task 1.2 audit prevents missed usages | Not Started |
| Cascade delete removes unintended records | HIGH | Verify SQLAlchemy relationships before Phase 2 | Not Started |
| Bulk recalculation script fails mid-run | MEDIUM | Add transaction handling and progress checkpoints | Not Started |
| Import modal latency impacts UX | LOW | Reuse existing import service | Not Started |

---

## Dependencies & Blockers

**Current Status:** No blockers identified

**Phase Dependencies:**
- Phase 1 can start immediately (backend only)
- Phase 2 can start after Phase 1 validation (delete endpoint doesn't depend on metrics fix)
- Phase 3 can start after Phase 1 validation (import doesn't depend on metrics or delete)

**Note:** Phases 2 and 3 can run in parallel after Phase 1 completion.

---

## Success Metrics

| Goal | Success Metric | Phase | Status |
|------|---|---|---|
| Accurate CPU valuation | All adjusted metrics tests pass; audit shows no conflicts | 1 | Not Started |
| Self-service deletion | Delete endpoint works; cascade deletes clean; UI accessible | 2 | Not Started |
| Streamlined import workflow | Import button in catalog; modal works; refresh automatic | 3 | Not Started |

---

## Performance Considerations

- **Phase 1 recalculation:** ~100 listings per 2 seconds (async)
- **Phase 2 delete:** O(1) per listing (cascade via DB relationships)
- **Phase 3 import modal:** Same as current `/import` page (no perf impact)

---

## API Contract Changes

### New Endpoints

**Phase 2:**
```
DELETE /api/v1/listings/{id}
Response: 204 No Content
Error: 404 Not Found
```

### Unchanged Endpoints
- GET /api/v1/listings (metrics already present)
- POST /api/v1/listings/import (reused)
- Metrics response schema (same fields, new calculation)

---

## Database Changes

- **Phase 1:** No migrations needed. `valuation_breakdown` JSON already stores `summary.total_adjustment`
- **Phase 2:** No migrations needed. Cascade deletes via existing relationships
- **Phase 3:** No migrations needed. Pure UI/API integration

---

## Notes

- All tasks extracted from IMPLEMENTATION_PLAN.md
- Timeline estimates: Phase 1 (4-5 days), Phase 2 (3-4 days), Phase 3 (2-3 days)
- Total estimated timeline: 2-3 weeks
- Progress tracker to be updated after each completed task
- Use this document for daily standup updates and progress tracking
