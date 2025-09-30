# Global Fields & Listings Remediation Plan

## Purpose
Deliver the missing PRD scope for Global Fields management, Listings workspace, and manual listing entry so the platform supports schema agility, clean UX, and reliable backend behavior. This plan assumes a single developer/architect (me), no production users or data, and no requirement for phased rollouts or feature flags.

## Scope & Assumptions
- No existing users → changes can ship directly to `main` once validated locally.
- Database migrations are optional; prefer direct schema/service updates.
- All design decisions are handled in-line (Figma not required). Final UI polish is driven by Tailwind + Storybook snapshots.
- Tests run locally (pytest, playwright) and must cover critical paths.

## System Overview
- **Backend**: FastAPI + SQLAlchemy async stack. Custom fields live in `CustomFieldDefinition` with audit logging. Listing creation currently triggers `MissingGreenlet` when syncing components.
- **Frontend**: Next.js + React Query + TanStack Table. Global Fields tab uses a local table implementation; Listings grid lacks cohesion; Add Listing form is minimal.

## Implementation Sequencing
### Phase 1 – Backend Foundations (Days 1-3)
1. **Field Registry Service**
   - Create `FieldRegistry` module consolidating entity metadata (core + custom fields).
   - Expose new endpoints:
     - `GET /v1/fields/entities` → list supported entities.
     - `GET /v1/fields/{entity}` → definitions (core + custom, with read-only flags).
     - `GET /v1/catalog/{entity}/records` with pagination, filter query params, JSON join of custom attributes.
     - `POST /v1/catalog/{entity}/records` to create records with dynamic schema validation.
     - `PATCH /v1/catalog/{entity}/records/{id}` for updates.
   - Use SQL joins per entity: start with `listing` + `cpu`; keep service extensible for GPUs/ports later.
   - Add `FieldDataService` helper to map payloads to models and run validation (type coercion, enum enforcement).
2. **Listings Async Hygiene**
   - Replicate error with failing pytest.
   - Refactor `sync_listing_components` to issue explicit delete/insert using `await session.execute` and eager load relationships before response serialization.
   - Ensure manual creation path flushes before computing metrics.
3. **Telemetry Hooks**
   - Implement minimal logging (`logger.info`) for field/data CRUD and listing edits.
   - No external analytics until production; capture counts in logs for now.

### Phase 2 – Global Fields UI Expansion (Days 4-6)
1. **Layout & Navigation**
   - Convert Global Fields page to vertical navigation (entity list) with tabbed content (`Fields`, `Data`).
2. **Fields Tab Enhancements**
   - Reuse existing grid but display predefined core fields with lock badge + disabled editing.
   - Move create/edit modal to new design shell with consistent spacing (Tailwind adjustments only).
3. **Data Tab**
   - Implement shared `DataGrid` component (TanStack Table) with consistent typography, row padding, column resizing, sticky header, inline filters.
   - Fetch data via new backend endpoints; allow manual create/edit inline or via modal.
   - Support quick create: “Add Row” button surfaces dynamic form using schema metadata.
   - Provide bulk delete/inactivate controls for future use but keep disabled until needed.
4. **Testing**
   - Storybook stories for Fields/Data views.
   - Playwright spec to cover create field, create data row, edit row.

### Phase 3 – Unified Table & Modal Styling (Days 7-9)
1. **Shared Components**
   - Extract `DataGrid` and `ModalShell` components with design tokens (padding, typography, shadow).
   - Apply to Global Fields (both tabs), Listings table, importer workspace.
2. **Styling Guidelines**
   - Standard cell min height, text truncation with tooltip, zebra rows optional.
   - Modal improvements: 24px padding, sticky footer buttons, multi-step indicator styling.
3. **Regression Tests**
   - Update Storybook snapshots; run `pnpm lint` + `pnpm test` for frontend.

### Phase 4 – Listings Workspace Overhaul (Days 10-13)
1. **UI Refresh**
   - Rebuild `apps/web/components/listings/listings-table.tsx` to use `DataGrid`.
   - Expand default columns, add status/condition badges, wrap long titles with tooltip.
   - Add row density toggle and quick search.
2. **Interaction Enhancements**
   - Inline edit: add optimistic cache with rollback and toast notifications.
   - Bulk edit: include summary panel, undo by rehydrating previous values (store snapshot per request).
   - Filters: typed controls (range slider for numbers, multi-select for enums), persistent across sessions via localStorage (since no backend preferences yet).
3. **Analytics**
   - Track to local console/log for now; architecture-ready to pipe to Segment later.
4. **Performance**
   - Implement row virtualization (React-Window) for large datasets.
   - Benchmark with generated 10k dataset (local script). Document results.
5. **Testing**
   - Playwright tests for inline edit success/failure, bulk apply, undo.
   - Unit tests for helper utilities (parse/format).

### Phase 5 – Add Listing UX Upgrade (Days 14-16)
1. **Dropdown Catalogs**
   - Build `useCatalogOptions` hook pulling RAM/storage options from new registry (fallback to static defaults).
   - Replace numeric inputs with combobox (headless UI) supporting search, keyboard nav, and “Add new…” CTA.
2. **Inline Creation**
   - “Add new…” opens Global Field modal pre-filled for relevant entity/type; on success, refetch options.
3. **CPU Auto-Create**
   - Add optional inline CPU creation modal similar to importer flow; call existing backend service.
4. **Validation & UX**
   - Real-time validation messages, disable submit until form valid.
   - Success state links back to Listings table.
5. **Testing**
   - Playwright coverage for new listing creation with existing and new dropdown values.

### Phase 6 – Final QA & Hardening (Days 17-18)
1. **End-to-End Pass**
   - Run pytest, mypy (if configured), frontend unit tests, Playwright suite.
   - Manual exploratory testing across Global Fields, Listings, Add Listing.
2. **Documentation**
   - Update `docs/importer-usage-guide.md` for field creation references.
   - Write developer notes in `docs/global-fields-admin-guide.md` describing new APIs and UI patterns.
3. **Cleanup**
   - Remove stale utilities, ensure TypeScript types align with new endpoints.
   - Commit with clear history and merge.

## Detailed Task Breakdown
| ID | Task | File(s) | Notes |
| --- | --- | --- | --- |
| B1 | Create `FieldRegistry` module | `apps/api/dealbrain_api/services/field_registry.py` | Consolidate schema metadata and core/custom merge. |
| B2 | Add new catalog endpoints | `apps/api/dealbrain_api/api/fields_data.py`, `main.py` | Include pagination params, data validation. |
| B3 | Update listings component sync | `apps/api/dealbrain_api/services/listings.py` | Avoid lazy relationship access to eliminate `MissingGreenlet`. |
| FE1 | Implement two-tab layout | `apps/web/app/global-fields/page.tsx`, new components | Tabs + navigation. |
| FE2 | Build `DataGrid` component | `apps/web/components/ui/data-grid.tsx` | Shared styling + virtualization support. |
| FE3 | Adapt `listings-table.tsx` | `apps/web/components/listings/listings-table.tsx` | Use new grid, redesign controls. |
| FE4 | Overhaul Add Listing form | `apps/web/components/listings/add-listing-form.tsx` | Combobox, inline creation flows. |
| FE5 | Update modals to `ModalShell` | `apps/web/components/ui/modal-shell.tsx`, imports | Ensure New Field wizard uses shell. |
| T1 | Add Playwright specs | `apps/web/e2e/global-fields.spec.ts`, `listings.spec.ts` | Cover new flows end-to-end. |
| DOC1 | Update docs | `docs/global-fields-admin-guide.md`, `docs/importer-usage-guide.md` | Reflect new capabilities. |
| OPS1 | Record performance benchmarks | `docs/perf/listings-grid.md` | Document dataset, timings, virtualization impact. |

## Testing Strategy
- **Backend**: pytest with async fixtures; focus on data validation, listing creation, component sync.
- **Frontend**: unit tests for hooks/utils, Storybook visual spot checks, Playwright e2e for critical flows.
- **Performance**: local benchmark script generating sample data; ensure grid remains responsive (<100ms scroll). No external load testing needed yet.

## Deliverables Checklist
- [ ] New backend services + endpoints live, manual testing complete.
- [ ] Global Fields UI shows Fields/Data tabs with manual data CRUD.
- [ ] Listings grid redesigned with inline/bulk updates, undo, filters, virtualization.
- [ ] Add Listing form supports catalog dropdowns, inline field creation, CPU auto-create.
- [ ] MissingGreenlet issue resolved; regression tests added.
- [ ] Documentation and benchmarks committed; Playwright + pytest suites passing.

## Next Actions
1. Branch from `main`, scaffold FieldRegistry with initial tests (Day 1).
2. Refactor listings component sync and confirm error gone (Day 2).
3. Implement Global Fields tabs and Data tab MVP, wire to new endpoints (Day 3-4).
4. Proceed through phases sequentially, merging frequently once tests pass.
