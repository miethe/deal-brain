# Listings Valuation Enhancements - Progress Tracker

**Project**: Deal Brain Listings Valuation & UX Improvements
**PRD**: [docs/project_plans/listings-valuation-enhancements/PRD.md](../../docs/project_plans/listings-valuation-enhancements/PRD.md)
**Implementation Plan**: [docs/project_plans/listings-valuation-enhancements/IMPLEMENTATION_PLAN.md](../../docs/project_plans/listings-valuation-enhancements/IMPLEMENTATION_PLAN.md)
**Start Date**: 2025-11-01
**Target Completion**: TBD
**Status**: Planning Complete

---

## Phase Overview

| Phase | Status | Start Date | Completion Date | Duration |
|-------|--------|------------|-----------------|----------|
| Phase 1: Adjusted Valuation Fix | Not Started | - | - | 4-5 days (est) |
| Phase 2: Delete Functionality | Not Started | - | - | 3-4 days (est) |
| Phase 3: Import Button | Not Started | - | - | 2-3 days (est) |

**Estimated Total Duration**: 9-12 days

---

## Phase 1: Adjusted Valuation Calculation Fix

**Objective**: Fix adjusted CPU performance metrics to use delta method: `(base_price - adjustment_delta) / cpu_mark`

### Tasks

| Task ID | Description | Status | Assignee | Notes |
|---------|-------------|--------|----------|-------|
| 1.1 | Update `calculate_cpu_performance_metrics()` | ⬜ Not Started | - | Core fix in listings.py:706-734 |
| 1.2 | Audit adjusted field usages | ⬜ Not Started | - | Search & verify semantics |
| 1.3 | Update & expand test coverage | ⬜ Not Started | - | 5+ new test cases |
| 1.4 | Bulk recalculation script | ⬜ Not Started | - | Migrate existing listings |

### Acceptance Criteria
- [ ] Adjusted metrics use delta formula: `(base_price - total_adjustment) / cpu_mark`
- [ ] All existing tests pass with updated calculations
- [ ] New tests validate delta method with various adjustment scenarios
- [ ] Bulk recalculation script successfully updates all existing listings
- [ ] No regressions in valuation breakdown display

---

## Phase 2: Delete Listing Functionality

**Objective**: Add delete buttons with confirmation in modal and detail page

### Tasks

| Task ID | Description | Status | Assignee | Notes |
|---------|-------------|--------|----------|-------|
| 2.1 | Backend DELETE endpoint | ⬜ Not Started | - | `/api/listings/{id}` with cascade |
| 2.2 | Delete UI - Detail Modal | ⬜ Not Started | - | Bottom bar, next to "View Full Page" |
| 2.3 | Delete UI - Detail Page | ⬜ Not Started | - | Top right corner with navigation |
| 2.4 | Confirmation dialog component | ⬜ Not Started | - | Accessible, reusable |

### Acceptance Criteria
- [ ] DELETE endpoint returns 204 and cascades to related records
- [ ] Modal delete button appears in bottom bar
- [ ] Detail page delete button appears in top right
- [ ] Confirmation dialog prevents accidental deletions
- [ ] Successful deletion refreshes catalog and shows toast
- [ ] Error handling displays user-friendly messages

---

## Phase 3: Import Button in Catalog View

**Objective**: Make import functionality accessible directly from listings catalog

### Tasks

| Task ID | Description | Status | Assignee | Notes |
|---------|-------------|--------|----------|-------|
| 3.1 | Extract import modal to shared component | ⬜ Not Started | - | Reusable across pages |
| 3.2 | Add import button to catalog header | ⬜ Not Started | - | Next to "Add listing" |
| 3.3 | Wire up modal trigger & refresh | ⬜ Not Started | - | Cache invalidation on success |

### Acceptance Criteria
- [ ] Import modal component is reusable
- [ ] Import button appears in catalog header
- [ ] Modal opens on button click
- [ ] Successful import refreshes catalog table
- [ ] Toast notifications for success/error

---

## Blockers & Risks

| Risk | Impact | Probability | Mitigation | Status |
|------|--------|-------------|------------|--------|
| Adjusted metrics change affects existing dashboards | High | Low | Communicate change, update docs | ⬜ Open |
| Delete cascade may miss related records | Medium | Medium | Thorough testing of relationships | ⬜ Open |
| Import modal extraction breaks existing page | Low | Low | Careful refactor with tests | ⬜ Open |

---

## Deployment Checklist

- [ ] All Phase 1 tasks complete
- [ ] All Phase 2 tasks complete
- [ ] All Phase 3 tasks complete
- [ ] Database migration (if needed) tested
- [ ] Bulk recalculation script executed in staging
- [ ] End-to-end tests pass
- [ ] Documentation updated (PRD, architecture.md if needed)
- [ ] Stakeholder sign-off
- [ ] Release notes prepared
- [ ] Production deployment scheduled

---

## Notes

### 2025-11-01 - Planning Complete
- Created PRD and Implementation Plan
- Analyzed existing valuation calculation logic
- Identified key files and functions for modification
- Estimated phase durations based on task complexity
- No database schema changes required (all fields exist)

---

## Resources

- **PRD**: [docs/project_plans/listings-valuation-enhancements/PRD.md](../../docs/project_plans/listings-valuation-enhancements/PRD.md)
- **Implementation Plan**: [docs/project_plans/listings-valuation-enhancements/IMPLEMENTATION_PLAN.md](../../docs/project_plans/listings-valuation-enhancements/IMPLEMENTATION_PLAN.md)
- **Key Files**:
  - Backend: `apps/api/dealbrain_api/services/listings.py` (metrics calculation)
  - Models: `apps/api/dealbrain_api/models/core.py`
  - API: `apps/api/dealbrain_api/api/listings.py`
  - Frontend: `apps/web/app/listings/` (catalog views)
  - Tests: `tests/test_listing_metrics.py`
