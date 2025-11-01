# Listing Valuation & Management Enhancements Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** feat/listings-enhancements-v3
**Last Commit:** 1021bc5 docs: create comprehensive user guide for adding product images (IMG-005)
**Current Task:** Phase 1-3 initialization complete, ready to begin Phase 1 Task 1.1
**Progress Tracker:** docs/project_plans/listings-valuation-enhancements/progress/phase-1-3-progress.md

---

## Key Decisions

**Architecture:**
- Follow Deal Brain layered architecture: API Routes → Services → Domain Logic (core) → Database
- All database operations use async SQLAlchemy with `session_scope()` context manager
- Domain logic lives in `packages/core/dealbrain_core/`, not `apps/api/`

**Patterns:**
- Pydantic validation for all API inputs/outputs
- React Query for server state management, Zustand for client state
- Radix UI primitives for accessible components (shadcn/ui)
- Code style: Black (line length 100), isort, ruff for Python; Prettier for TypeScript

**Technology Stack:**
- Backend: FastAPI + async SQLAlchemy + Alembic migrations
- Frontend: Next.js 14 App Router + React Query + Tailwind CSS
- Testing: pytest (backend), Jest/React Testing Library (frontend)

---

## Important Learnings

**Metrics Calculation Bug (Phase 1):**
- Current adjusted metrics incorrectly use `adjusted_price` instead of `(base_price - adjustment_delta)`
- Adjusted CPU metrics should use: `(base_price - total_adjustment) / cpu_mark`
- `total_adjustment` comes from `valuation_breakdown.summary.total_adjustment` JSON field
- Must handle missing/None `valuation_breakdown` gracefully (default to 0.0)

**Cascade Deletes (Phase 2):**
- Verify SQLAlchemy relationships have proper `cascade='all, delete-orphan'` configuration
- Affected relationships: `Listing.components`, `Listing.scores`, `Listing.field_values`
- Delete endpoint must clean up all related records (ListingComponent, ListingScoreSnapshot, EntityFieldValue)

**Domain Logic Location:**
- Valuation calculations belong in `packages/core/dealbrain_core/valuation.py`
- Services orchestrate persistence + domain logic, don't implement domain rules
- Keep services layer in `apps/api/dealbrain_api/services/` focused on orchestration

---

## Quick Reference

### Environment Setup

```bash
# Backend API
export PYTHONPATH="$PWD/apps/api"
poetry install
make migrate

# Frontend Web
pnpm install --frozen-lockfile=false
pnpm --filter "./apps/web" dev

# Database
make up  # Start Docker Compose stack (Postgres on 5442, API on 8020, web on 3020)

# Full stack
make up
```

### Key Files

**Phase 1 (Metrics Fix):**
- Metrics calculation: `apps/api/dealbrain_api/services/listings.py:706-734`
- Test file: `tests/test_listing_metrics.py` (to be created)
- Recalculation script: `scripts/recalculate_adjusted_metrics.py` (to be created)
- Listing model: `apps/api/dealbrain_api/models/core.py` (Listing class)

**Phase 2 (Delete):**
- API endpoint: `apps/api/dealbrain_api/api/listings.py`
- Service: `apps/api/dealbrain_api/services/listings.py`
- Models: `apps/api/dealbrain_api/models/core.py` (Listing relationships)
- Detail modal: `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`
- Detail page: `apps/web/app/listings/[id]/page.tsx`
- Confirmation dialog: `apps/web/components/ui/confirmation-dialog.tsx` (to be created)

**Phase 3 (Import Button):**
- Import page (source): `apps/web/app/import/page.tsx`
- Import modal: `apps/web/components/listings/import-modal.tsx` (to be created)
- Catalog page: `apps/web/app/listings/page.tsx`

---

## Phase Scope Summary

**Phase 1: Fix Adjusted CPU Metrics (4-5 days)**
- Fix `calculate_cpu_performance_metrics()` to use `(base_price - adjustment_delta) / cpu_mark`
- Extract `total_adjustment` from `valuation_breakdown.summary.total_adjustment` JSON
- Update both single-thread and multi-thread adjusted metrics
- Handle missing `valuation_breakdown` gracefully
- Add 5+ test cases with ≥95% code coverage
- Create bulk recalculation script for existing listings

**Phase 2: Delete Listing Functionality (3-4 days)**
- Add `DELETE /api/v1/listings/{id}` endpoint (204 on success, 404 if not found)
- Implement `delete_listing()` service method with cascade deletes
- Verify cascade deletes for components, scores, field values
- Add delete button to detail modal and detail page
- Create accessible confirmation dialog (keyboard navigation, focus trap)
- Invalidate cache after successful delete

**Phase 3: Import Button in Catalog (2-3 days)**
- Extract import modal from `/import` page to reusable component
- Add import button to catalog header (next to "Add Listing")
- Wire modal trigger and refresh logic
- Show success/error toasts
- Invalidate listings cache after successful import

**Success Metric:** All three phases complete with tests passing, coverage ≥80% backend, ≥70% frontend

---

## Testing Commands

```bash
# Backend tests
poetry run pytest tests/test_listing_metrics.py -v
poetry run pytest tests/ --cov=dealbrain_api --cov-report=html

# Frontend tests
pnpm --filter "./apps/web" test
pnpm --filter "./apps/web" typecheck
pnpm --filter "./apps/web" build

# Database migrations
poetry run alembic revision --autogenerate -m "description"
make migrate

# Linting and formatting
make lint    # Lint Python (ruff) and TypeScript (eslint)
make format  # Format code (black, isort, prettier)
```

---

## API Contract Changes

**New Endpoints (Phase 2):**
```
DELETE /api/v1/listings/{id}
Response: 204 No Content
Error: 404 Not Found
```

**Unchanged Endpoints:**
- `GET /api/v1/listings` - Metrics already present, calculation changes internally
- `POST /api/v1/listings/import` - Reused in Phase 3
- Metrics response schema - Same fields, new calculation logic

---

## Database Changes

- **Phase 1:** No migrations needed. `valuation_breakdown` JSON already stores `summary.total_adjustment`
- **Phase 2:** No migrations needed. Cascade deletes via existing relationships
- **Phase 3:** No migrations needed. Pure UI/API integration

---

## Next Steps

1. **Phase 1 Task 1.1:** Fix CPU Performance Metrics Calculation
   - Read current implementation at `apps/api/dealbrain_api/services/listings.py:706-734`
   - Update to use `(base_price - total_adjustment) / cpu_mark` formula
   - Handle missing `valuation_breakdown` (default to 0.0)

2. **Phase 1 Task 1.2:** Audit all usages of adjusted metrics fields
   - Search for `dollar_per_cpu_mark_single_adjusted` references
   - Search for `dollar_per_cpu_mark_multi_adjusted` references
   - Document findings in "Metric Audit Summary" table

3. **Phase 1 Task 1.3:** Create comprehensive test suite
   - Create `tests/test_listing_metrics.py` with 5+ test cases
   - Target ≥95% code coverage for metrics function

4. **Phase 1 Task 1.4:** Create bulk recalculation script
   - Create `scripts/recalculate_adjusted_metrics.py`
   - Test on development data before production use

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Adjusted metrics change breaks existing queries/dashboards | HIGH | Task 1.2 audit prevents missed usages |
| Cascade delete removes unintended records | HIGH | Verify SQLAlchemy relationships before Phase 2 |
| Bulk recalculation script fails mid-run | MEDIUM | Add transaction handling and progress checkpoints |
| Import modal latency impacts UX | LOW | Reuse existing import service |

---

## Related Documentation

- **PRD:** docs/project_plans/listings-valuation-enhancements/PRD.md
- **Implementation Plan:** docs/project_plans/listings-valuation-enhancements/IMPLEMENTATION_PLAN.md
- **Progress Tracker:** docs/project_plans/listings-valuation-enhancements/progress/phase-1-3-progress.md
- **Symbols Best Practices:** docs/development/symbols-best-practices.md (for code exploration)
