# Global Fields & Listings Execution Plan (Phases 1–3)

_Last updated: 2025-09-27_

## Purpose
Consolidated execution plan to close remaining gaps in Phases 1 and 2 and deliver the full Phase 3 scope for the Global Fields & Listings program. This plan aligns the PRD requirements with actionable engineering, design, analytics, and QA workstreams, ready for hand-off to development pods and AI agents.

## Status Snapshot
- **Phase 1**: Complete – audit log table wired, backfill utility available for staged datasets.
- **Phase 2**: Complete – `/v1/fields` API, dependency guardrails, analytics, and partial integration coverage in place.
- **Phase 3**: Feature-complete UI shipped with analytics; remaining follow-up limited to automated UI tests.

## Guiding Principles
- Treat the PRD as source of truth; no scope reductions without product approval.
- Prefer incremental PRs gated behind `global_fields_v1` flag until UAT sign-off.
- Ensure every backend change ships with telemetry and auditability hooks.

## Phase 1 Close-Out (Domain Model & Migrations)

### P1.1 Migration Backfill for Existing Attribute Keys
- **Objective**: Populate `custom_field_definition` with definitions inferred from historical `attributes_json` payloads across entities.
- **Actions**:
  1. Run inventory query (materialize to CSV) capturing distinct attribute keys, inferred data types, option sets across `listing`, `cpu`, `gpu`, `ports_profile`, `valuation_rule` tables.
  2. Define mapping heuristics: treat numeric-only values as `number`, `true/false` as `boolean`, repeated string sets ≥3 unique values but ≤15 → enum.
  3. Author Alembic data migration (`apps/api/alembic/versions/0005_custom_field_enhancements.py`) to insert missing `custom_field_definition` rows using above heuristics. Ensure idempotency via `ON CONFLICT (entity, key)`.
  4. Seed `display_order` using alphabetical ordering per entity unless explicit metadata exists.
- **Deliverables**: Migration script update + companion SQL snapshot stored at `docs/migrations/0005_backfill-sample.sql` for audit.
- **Owner**: Backend (Miguel).
- **Acceptance**: All historical attributes represented in `custom_field_definition`; migration passes on staging dump; unit test verifying sample backfill in `tests/migrations/test_0005_backfill.py`.

### P1.2 Field Definition Audit Logging
- **Objective**: Persist immutable history of field lifecycle events for compliance.
- **Actions**:
  1. Create table `custom_field_audit_log` with columns `(id, field_id, action, actor, payload_json, created_at)` and index on `field_id`.
  2. Update `CustomFieldService` create/update/delete flows to write audit entries and enqueue analytics events.
  3. Add SQLAlchemy relationship on `CustomFieldDefinition` for `.audit_events`.
  4. Provide factory + unit tests covering insertions (`tests/services/test_custom_field_audit.py`).
- **Deliverables**: New migration `0006_custom_field_audit.py`, model/service updates with tests.
- **Owner**: Backend (Priya).
- **Acceptance**: Audit log entries appear for every C/U/D in local run; schema doc updated `docs/global-fields-backend.md#audit-logging`.

## Phase 2 Close-Out (Backend Services & APIs)

### P2.1 Dependency Guardrails & Soft-Delete Enforcement
- **Objective**: Prevent deleting fields in active use; surface impact summary per PRD.
- **Actions**:
  1. Add repository method `CustomFieldRepository.field_usage_counts(entity, field_key)` scanning `attributes_json` across entities via JSONB queries.
  2. On delete/disable, block action if usage > 0 unless `force=true`, returning counts to caller.
  3. Implement soft-delete flagging `deleted_at` and toggling `is_active`.
- **Deliverables**: Service logic, error model `FieldDependencyError`, tests in `tests/services/test_custom_fields.py` covering happy/error paths.
- **Owner**: Backend (Miguel).
- **Acceptance**: API returns 409 with usage summary; soft-deleted fields excluded by default list call.

### P2.2 REST Endpoint Realignment
- **Objective**: Ship versioned `/v1/fields` API with history endpoints per implementation plan.
- **Actions**:
  1. Introduce router `apps/api/dealbrain_api/api/fields.py` with resources: `GET /v1/fields`, `POST /v1/fields`, `PATCH /v1/fields/{id}`, `DELETE`, `GET /v1/fields/{id}/history`.
  2. Add schema models under `api/schemas/fields.py` (reuse existing custom field response models where possible).
  3. Maintain backwards compatibility by delegating `/v1/reference/custom-fields` to new handlers (return 301 or internal call until frontend cutover).
- **Deliverables**: Router + FastAPI wiring in `apps/api/dealbrain_api/main.py`, OpenAPI docs regenerated.
- **Owner**: Backend (Priya).
- **Acceptance**: Swagger shows new endpoints; integration tests cover CRUD + history retrieval.

### P2.3 Analytics & Audit Event Emission
- **Objective**: Meet PRD telemetry requirements.
- **Actions**:
  1. Extend service to emit Segment events (`field_definition.created/updated/deleted`) via existing analytics client (see `apps/api/dealbrain_api/services/imports/service.py:420` for pattern).
  2. Write audit messages to existing `system_audit_log` (if absent, repurpose newly created table).
  3. Update configuration to ensure events are behind env flag.
- **Deliverables**: Analytics client integration, config docs `docs/analytics-events.md` updated.
- **Owner**: Backend (Priya) + Data Eng consultant.
- **Acceptance**: Events visible in staging Segment with correct payload schema.

### P2.4 Integration Test Suite
- **Objective**: Regression-proof service interactions.
- **Actions**:
  1. Build fixture seeding sample field definitions.
  2. Tests covering: field CRUD happy path, dependency failure, importer session creating new field, CPU auto-create, and listings bulk update.
  3. Use async `httpx.AsyncClient` to hit FastAPI app; run in CI pipeline stage `backend-integration`.
- **Deliverables**: New module `tests/integration/test_fields_and_listings.py`, GitHub Actions job update.
- **Owner**: QA Automation (Lina).
- **Acceptance**: Tests passing locally and in CI.

## Phase 3 Execution (Field Management Frontend)

### P3.1 Experience Design & UX Artifacts
- **Objective**: Lock UI/UX before development sprint.
- **Actions**:
  1. Figma flow for Global Fields tab (grid, chips, filters, usage indicators, status banners).
  2. Modal wizard screens (step 1 metadata, step 2 validation preview, step 3 impact confirmation for delete).
  3. Audit drawer blueprint showing timeline + diff.
- **Deliverables**: Figma link + exported PNGs in `docs/design/global-fields/`.
- **Owner**: UX (Hannah).
- **Acceptance**: Stakeholder review sign-off, design tokens documented.

### P3.2 Data Grid Enhancements
- **Objective**: Feature-complete Global Fields list.
- **Actions**:
  1. Replace static table with `DataGrid` component enabling column filters (entity, status, type), quick search, and selectable rows.
  2. Display usage count badge via new `/v1/fields/usage` API (reuse counts from P2.1).
  3. Status chips for Active/Inactive/Deleted.
  4. Persist view preferences in local storage keyed by user id.
- **Deliverables**: Updates to `apps/web/components/custom-fields/global-fields-table.tsx`, new hook `useFieldDefinitions` with SWR caching.
- **Owner**: Frontend (Noah).
- **Acceptance**: UX review; unit test snapshots covering empty/error/loading states.

### P3.3 Create/Edit Modal Wizard
- **Objective**: Provide end-to-end field lifecycle management in UI.
- **Actions**:
  1. Build modal component `FieldDefinitionWizard` with three steps (Basics, Validation, Review).
  2. Step-specific validation leveraging shared schema in `@/lib/validation/field-definition.ts`.
  3. Preview panel showing JSON payload + duplicate detection via API `GET /v1/fields?entity=&key=`.
  4. Support edit path preloading existing values, update call on submit.
- **Deliverables**: Components under `apps/web/components/custom-fields/wizard/`, Storybook stories.
- **Owner**: Frontend (Noah) + Support from UX.
- **Acceptance**: Storybook interactions reviewed by PM; Cypress component test ensures validation flow.

### P3.4 Delete & Dependency Workflow
- **Objective**: Align with dependency guardrails.
- **Actions**:
  1. Introduce confirmation modal summarizing usage counts, require `type field name` confirmation for hard delete.
  2. Offer “Mark inactive” alternative when dependencies exist.
- **Deliverables**: UI component `FieldDeleteDialog.tsx`, service call hooking into dependency API.
- **Owner**: Frontend (Noah).
- **Acceptance**: Unit tests for dialog logic; manual QA script in `docs/qa/global-fields.md`.

### P3.5 Audit History Drawer
- **Objective**: Surface change history per PRD.
- **Actions**:
  1. Slide-over drawer showing chronological list from `/v1/fields/{id}/history`.
  2. Diff view using `react-diff-viewer` for before/after payload.
  3. Filter by event type (create/update/delete) and actor.
- **Deliverables**: Component `FieldAuditDrawer.tsx`, API integration.
- **Owner**: Frontend (Noah) + Data Eng for event payload format.
- **Acceptance**: Visual QA; ensure keyboard accessibility per WCAG.

### P3.6 Optimistic Updates & Error States
- **Objective**: Responsive UX with resilience.
- **Actions**:
  1. Implement optimistic cache updates for create/update/delete with rollback on failure.
  2. Toast notifications for success/error leveraging existing `useToast` hook.
  3. Global error boundary around tab to capture and reset state.
- **Deliverables**: React Query mutation wrappers, tests verifying rollback logic (`apps/web/components/custom-fields/__tests__/field-mutations.test.tsx`).
- **Owner**: Frontend (Noah).
- **Acceptance**: Tests green; manual QA scenario for network failure.

### P3.7 Analytics Instrumentation
- **Objective**: Track adoption metrics.
- **Actions**:
  1. Hook screens into analytics service (e.g., `useAnalytics().track`).
  2. Emit events per PRD: `field_definition.created/updated/deleted`, `field_definition.audit_viewed`.
  3. Document properties schema in `docs/analytics-events.md`.
- **Deliverables**: Analytics calls embedded in modal/drawer, updated docs.
- **Owner**: Frontend (Noah) + Data Eng QA.
- **Acceptance**: Events observed in Segment dev workspace.

### P3.8 Testing & Accessibility
- **Objective**: Guarantee quality baseline.
- **Actions**:
  1. Jest tests for key hooks/components, Storybook visual regression using Chromatic.
  2. Cypress e2e spec `global_fields.cy.ts` covering list view, create, edit, delete.
  3. Automated axe-core accessibility checks embedded in Cypress flow.
- **Deliverables**: Test suites, GitHub Action job `frontend-e2e` update, QA checklist.
- **Owner**: QA Automation (Lina).
- **Acceptance**: Tests passing; axe reports no critical violations.

## Cross-Cutting Support
- **Docs**: Update `docs/importer-usage-guide.md` and create `docs/global-fields-admin-guide.md` after Phase 3 QA.
- **Monitoring**: Extend Metabase dashboards for field usage, error rates.

## Timeline & Milestones
| Week | Milestones |
| --- | --- |
| W1 | Phase 1 tasks complete (migration backfill, audit table). |
| W2 | Phase 2 backend updates merged; integration tests running in CI. |
| W3 | UX finalized; P3.2–P3.4 development in feature branch. |
| W4 | P3.5–P3.8 delivered; Cypress + Storybook checks green. |
| W5 | UAT + documentation + flag enablement prep. |
