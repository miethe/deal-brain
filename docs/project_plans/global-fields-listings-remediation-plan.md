# Global Fields & Listings Remediation Plan

## Purpose
Close the remaining gaps between the PRD and the current implementation across Global Fields management, Listings workspace, and manual entry flows while resolving blockers discovered post-launch.

## Current Gaps
- Global Fields screen exposes definitions only; Data tab and manual record authoring absent.
- Tables follow inconsistent styling and spacing, diminishing readability; modals lack refined layout.
- Listings table has truncated content, inconsistent filters, no undo for inline/bulk edits, and lacks analytics.
- Add Listing form depends on free-form inputs without catalog-backed dropdowns or inline field creation.
- Manual listing creation intermittently raises `sqlalchemy.exc.MissingGreenlet` due to improper async usage in component sync logic.

## Objectives
1. Deliver entity-specific Global Fields views with both definition and data management workflows.
2. Establish a cohesive table and modal design system that unifies Global Fields, Listings, and importer experiences.
3. Upgrade the Listings workspace for usability, resilience, and telemetry per PRD metrics.
4. Enhance Add Listing UX with catalog-backed dropdowns, inline field creation, and schema parity with importer.
5. Resolve backend async defects to eliminate the MissingGreenlet crash and harden listing creation pathways.
6. Ship with full QA coverage, analytics instrumentation, and a controlled rollout plan.

## Workstreams

### 1. Global Fields Workspace Expansion
- Build two-tab layout (`Fields`, `Data`) per entity with side navigation.
- Surface predefined core fields alongside custom definitions and enforce read-only state for locked keys.
- Implement Data tab using a backend aggregator (`FieldRegistry`, `FieldDataService`) with endpoints:
  - `GET /v1/fields/entities`
  - `GET/POST /v1/fields/{entity}` for definitions
  - `GET/POST/PATCH /v1/catalog/{entity}/records` for data rows
- Enable manual record creation/edit using dynamic forms and schema validation reused from importer.
- Cache field metadata per entity, emit analytics (`field_definition.viewed`, `field_data.created/updated`), and add pagination + filtering.
- Tests: service unit tests, FastAPI integration specs, Cypress E2E for create/edit flows.

### 2. Table & Modal Design System
- Partner with design on spacing, typography, density, and truncation guidelines; produce Figma source of truth.
- Extract shared `DataGrid` and `ModalShell` components (sticky headers/footers, consistent padding, focus traps).
- Migrate Global Fields, Listings, importer screens, and modals (e.g., New Field wizard) onto the shared components.
- Introduce column resizing, responsive breakpoints, and improved empty/error states.
- Instrument Chromatic or Playwright visual regression checks; run accessibility (axe) audits.
- Gate rollout via `design_v2_tables` feature flag.

### 3. Listings Workspace Enhancements
- Rebuild table on new grid; widen primary columns and add contextual metadata (chips for status, tooltips for long text).
- Persist filters/sorts/groupings per user (`/v1/listings/views` preferences API) with optimistic caching.
- Implement inline edit undo stack, toast feedback, and typed filter controls.
- Upgrade bulk edit drawer with summary chips, impact preview, undo, and consistent validation messaging.
- Add analytics events (`listings_inline_edit_success/failure`, `bulk_edit_applied`, `filter_saved`).
- Performance test with ≥10k rows × 75 fields; enable virtualization as needed.

### 4. Add Listing Flow UX
- Replace numeric inputs with catalog-backed dropdowns for RAM and storage (capacity + type) listing standard options.
- Support free-type + fuzzy search with inline “Add new…” path that launches the field modal.
- Auto-refresh options when fields are added from Global Fields or importer.
- Mirror importer CPU auto-create path and surface new CPU summaries.
- Add optimistic validation and E2E coverage for manual creation.

### 5. Backend Reliability & Async Hygiene
- Reproduce `MissingGreenlet` by simulating manual creation in tests.
- Refactor `sync_listing_components` in `apps/api/dealbrain_api/services/listings.py:189` to avoid lazy relationship access; use explicit delete/insert with `await session.execute` or `run_sync` helpers.
- Ensure API serializers preload required relationships before response.
- Add async unit + integration tests to guard against regressions and enhance structured logging around component sync.

### 6. Launch Readiness & Ops Enablement
- Update analytics docs, configure Metabase dashboards for field usage, listing edits, and error rates.
- Draft release checklist: data migration verification, feature flag rollout, training, support playbook, rollback steps.
- Schedule ops UAT post Data tab + design rollout; capture sign-offs.

## Timeline & Milestones (6 Weeks)
| Week | Milestones |
| --- | --- |
| 1 | Design kickoff; backend spike for FieldDataService; reproduce MissingGreenlet with failing test. |
| 2 | Field Data API + caching complete; frontend skeleton for Fields/Data tabs; async fix merged. |
| 3 | Table/Modal design system components ready; Global Fields tabs functional end-to-end. |
| 4 | Listings table migrated; inline/bulk enhancements live behind flag; Add Listing dropdown prototype. |
| 5 | Finalize Add Listing UX, analytics, and virtualization/perf tests; complete Cypress + axe runs. |
| 6 | UAT, documentation, Metabase dashboards, release checklist, and staged rollout execution. |

## Dependencies & Owners
- **Design**: Table/Modal system, Global Fields + Listings layouts.
- **Backend**: FieldDataService/API, async fixes, preferences endpoints.
- **Frontend**: Global Fields tabs, table system migration, Listings enhancements, Add Listing upgrades.
- **QA**: Integration/E2E tests, accessibility, load testing.
- **Product/Ops**: UAT coordination, training, analytics validation.

## Risks & Mitigations
- **Complex data joins for Data tab**: prefetch with async tasks and paginate; add caching.
- **Table redesign regression**: stagger rollout via flag, maintain unit/visual tests.
- **Undo implementation**: instrument telemetry and fallback to server rollback on errors.
- **Async refactor**: pair review + load testing before release.

## Deliverables
- Updated Global Fields UI with manual data entry.
- Unified table/modal components adopted in key screens.
- Enhanced Listings grid with state persistence, undo, analytics.
- Improved Add Listing flow with catalog dropdowns and inline creation.
- Backend async fix and regression coverage.
- Documentation, dashboards, UAT sign-offs, and release checklist.

## Next Actions
1. Confirm design availability and finalize joint working session (within 2 days).
2. Branch for FieldDataService prototype and MissingGreenlet regression test (within 3 days).
3. Draft feature flag strategy and analytics spec updates (within 1 week).
