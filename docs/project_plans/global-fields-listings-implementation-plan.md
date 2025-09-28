# Global Catalog Fields & Listings Enhancement Implementation Plan

## Overview
Structured delivery plan for dynamic global fields, importer integration, and Listings workspace upgrades, targeting an eight-week rollout with feature-flagged release and staged adoption.

## Phase Breakdown

### Phase 0 – Discovery & Alignment (Week 1)
- Inventory current schemas (`listing`, `cpu`, `gpu`, `ports_profile`, custom attribute usage).
- Audit importer mapping flow and identify UI component reuse opportunities.
- Confirm RBAC requirements and audit logging expectations with security.
- Partner with design to scope modal patterns, data grid interactions, and navigation adjustments.
- Deliver kickoff brief: success metrics, timeline, dependencies, risks.

### Phase 1 – Domain Model & Migrations (Week 2)
- Define `field_definition` table: `id`, `entity_type`, `key`, `label`, `type`, `options_json`, `validation_json`, `default_value`, `is_required`, `display_order`, `created_by`, timestamps, `deleted_at`.
- Generate alembic migration with data backfill for existing attribute keys.
- Extend ORM models and repositories; expose typed accessors.
- Add audit log table/entries for field changes.
- Unit tests for model constraints and validation helpers.

### Phase 2 – Backend Services & APIs (Week 3–4)
- Build FieldDefinition service (CRUD, validation, dependency checks, audit emission).
- Expose REST endpoints: `/v1/fields` (list, create, update, delete, history), `/v1/schemas/listings` (dynamic schema).
- Update importer backend to fetch definitions, validate new fields, and broadcast updates to frontend.
- Implement CPU auto-creation workflow with dedupe heuristics (normalize name, manufacturer suggestions, audit logging).
- Extend Listings bulk edit API to handle dynamic fields and multi-row transactions.
- Write integration tests (fields CRUD, importer field creation, CPU auto-create, bulk edit operations).

### Phase 3 – Field Management Frontend (Week 4–5)
- Implement Global Fields tab UI (data grid, filters, status chips, usage count badges).
- Create field create/edit modal wizard with live validation preview and duplicate guardrails.
- Hook into new APIs with optimistic updates and error handling.
- Audit log drawer displaying change history.
- Instrument analytics events for field operations.
- Frontend unit & storybook coverage for components.

### Phase 4 – Importer Enhancements (Week 5–6)
- Add “Add New Field…” option to mapping dropdown; integrate modal and schema refresh.
- Update mapping preview to reflect new field immediately; ensure validation messaging.
- Surface auto-created CPU summary in commit confirmation and history view.
- Emit analytics events (`import_field_created`, `cpu_autocreated`).
- Playwright/Cypress tests for import flow with new field creation and CPU auto-create.

### Phase 5 – Listings Workspace Upgrades (Week 6–7)
- Refactor Listings grid to load dynamic schema and render type-aware cells.
- Implement inline edit interactions with optimistic persistence and undo.
- Build bulk edit drawer (field selector, value entry, impact summary, apply/undo).
- Add column filters, multi-sort, and group-by controls with state persistence per user.
- Remove nested Listings header; ensure layout coherence.
- Extend analytics instrumentation for inline edit, bulk edit, filter usage.
- Performance testing with ≥10k rows / 50 custom fields.

### Phase 6 – Reference Hub & Manual Forms (Week 7)
- Update sidebar navigation (Global Fields tab, Reference hub with subtabs for CPUs, GPUs, Valuation Rules, Ports, Custom Fields).
- Implement shared grid for Reference entities with inline/bulk edit and creation modals.
- Update manual listing form to consume dynamic schema and include “Add new CPU” modal.
- QA regression for manual entry flow.

### Phase 7 – Stabilization, Docs, Launch (Week 8)
- Finalize unit/integration/e2e coverage; address flake.
- Conduct load testing for API endpoints under expected concurrency.
- Update documentation (`docs/importer-usage-guide.md`, ops playbooks) and record training materials.
- Configure Metabase dashboards and alerting for new metrics.
- Run stakeholder UAT; collect sign-offs.
- Prepare release notes, feature flag plan, rollout/rollback procedures.

## Resourcing
- Backend Engineer (primary Phases 1–2, support 4–6).
- Frontend Engineer (primary Phases 3–6).
- UX Designer (Phases 0–3, consult 5–6).
- QA Automation (Phases 4–7).
- Product/Program Lead for coordination and stakeholder comms.

## Dependencies & Integrations
- FastAPI/SQLAlchemy stack for new endpoints.
- Next.js frontend component library updates for data grid enhancements.
- Redis/event stream for importer state updates.
- Authentication/authorization services for audit and access control.
- Analytics pipeline (Segment/Metabase) for new events.

## Testing Strategy
- **Unit**: Validation utilities, CPU auto-create heuristics, bulk edit handlers.
- **Integration**: Field CRUD, importer session with dynamic schema, Listings bulk edit.
- **E2E**: Import flow with on-the-fly field creation, Listings inline/bulk edits, Reference hub management.
- **Performance**: API latency benchmarks, grid rendering under heavy load.
- **Accessibility**: Automated axe scans plus manual keyboard navigation review.

## Release & Rollout
- Feature flag gating new UI components.
- Migration runbook with pre/post checks and rollback path.
- Staged rollout: internal users (week 1 post-merge) → select tenants → full release.
- Monitoring dashboards tracking error rates, latency, adoption metrics.
- Support plan for ops (office hours, FAQ, escalation channel).

## Follow-On Opportunities
- Per-tenant field governance and visibility rules.
- GPU and other component auto-creation parity.
- Template bundles for rapid field setup per vertical.
- Deeper analytics on field utilization and data quality.
