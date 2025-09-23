# Importer Revamp Implementation Plan

## 1. Overview
- **Owner:** Strategic Tech Lead (Codex)
- **Last Updated:** 2024-09-22
- **Reference Docs:** docs/importer-revamp-prd.md, docs/importer-revamp-9-22.md, docs/importer-usage-guide.md
- **Release Target:** Production launch by end of Sprint 4 (approx. 8 weeks)

## 2. Objectives
1. Deliver the importer revamp per PRD requirements with minimal downtime.
2. Equip operators with reliable tools for mapping, custom fields, and post-import editing.
3. Maintain backward compatibility for existing API consumers throughout rollout.

## 3. Workstreams
- **Backend / Data Platform:** schema migrations, importer service updates, custom field APIs, audit logging.
- **Frontend / UX:** importer UI overhaul, reference workspace redesign, bulk edit components.
- **QA & Automation:** unit, integration, and end-to-end test coverage; regression suite updates.
- **DevOps / Release:** migration orchestration, feature flag rollout, monitoring & analytics.
- **Ops Enablement:** documentation, training, SOP updates.

## 4. Timeline & Milestones
| Sprint | Duration | Milestone | Exit Criteria |
| --- | --- | --- | --- |
| Sprint 1 | Weeks 1-2 | Backend groundwork | Migrations merged, API contracts drafted, importer service handles declared entities in CLI test harness |
| Sprint 2 | Weeks 3-4 | Importer experience | UI mapping flow functional behind flag, bulk preview overrides working, backend endpoints integration-tested |
| Sprint 3 | Weeks 5-6 | Reference workspace | Reference tabs live in staging, inline edit & bulk actions validated, custom field CRUD end-to-end |
| Sprint 4 | Weeks 7-8 | Hardening & release | Performance tuned, audit/permission checks complete, docs updated, production launch checklist signed |

## 5. Detailed Execution Plan
### Sprint 1 – Backend Groundwork
1. **DB Migrations**
   - Create `custom_field_definition` table with indexes on `entity` and `key`.
   - Add `attributes_json` column (JSONB, default `{}`) to CPU, GPU, Listing, ValuationRule, PortsProfile tables.
   - Add `declared_entities_json` to `import_session` and backfill nulls with `{}`.
2. **Domain Models & Schemas**
   - Update SQLAlchemy models and Alembic revision.
   - Extend Pydantic schemas for entities to include `attributes: dict[str, Any]`.
3. **Importer Service Enhancements**
   - Accept `declared_entities` input; bypass inference when provided.
   - Persist declared entities and raise discrepancies when auto-detect disagrees.
   - Emit audit events for declared entities and custom field promotions.
4. **Custom Field Services**
   - Implement CRUD service layer with validation (type, default, enum values).
   - Introduce utility to apply custom field values when importing rows.
5. **API Contracts**
   - Draft FastAPI routes for custom fields and bulk updates; generate OpenAPI stubs.
   - Update CLI importer to send declared entity metadata.
6. **Testing & Validation**
   - Unit tests for migrations, service methods, and validation logic.
   - CLI smoke test: import CPU sheet with declared entity and custom field creation.

### Sprint 2 – Importer Experience
1. **UI Architecture**
   - Introduce importer feature flag and route guard.
   - Create reusable column mapping components (list columns, drag/drop optional).
2. **Mapping Enhancements**
   - Render Mapped/Suggested/New buckets with sample data and confidence scores.
   - Implement custom field creation modal with validation tied to backend.
   - Support column ignore and reassignment interactions.
3. **Bulk Overrides in Preview**
   - Add row selection controls and action drawer (set value, override component, discard).
   - Wire actions to backend preview override endpoints; update session state.
4. **API Integration**
   - Connect UI to new declared entity APIs and audit logging endpoints.
   - Ensure optimistic UI updates with rollback on failure.
5. **QA**
   - Component tests (React Testing Library) for mapping panel.
   - Integration tests covering upload → mapping → preview flows.

### Sprint 3 – Reference Workspace
1. **Navigation & Layout**
   - Add "Reference" sidebar group; route tabs for CPUs, GPUs, Valuation Rules, Ports, Custom Fields.
   - Implement shared data-grid component with sorting, filtering, inline edit.
2. **Record Management**
   - Inline edit standard fields; open detail drawer for advanced/custom fields.
   - Persist edits via entity PATCH endpoints including attributes payload.
3. **Bulk Actions**
   - Implement multi-select with contextual actions (edit field, attach profile, delete/disable).
   - Add confirmation dialogs summarizing affected rows.
4. **Custom Field Admin**
   - Build list/create/edit UI for custom fields with validation preview.
   - Gate custom field creation behind admin permission.
5. **Staging Validation**
   - Populate staging with anonymized datasets; run end-to-end flows.
   - Collect operator feedback; log issues for Sprint 4.

### Sprint 4 – Hardening & Rollout
1. **Performance & Scale**
   - Benchmark importer preview with 10k row sheets; optimize queries & indexing.
   - Cache schema metadata where helpful.
2. **Security & Permissions**
   - Finalize RBAC checks on custom field endpoints and bulk updates.
   - Pen-test or security review for new surfaces.
3. **Audit & Observability**
   - Ensure audit events cover all critical actions; expose audit UI filters.
   - Add metrics dashboards (imports per day, custom field usage, bulk updates).
4. **Documentation & Enablement**
   - Update importer usage guide, API docs, SOPs.
   - Record training walkthrough and host feedback session.
5. **Launch Activities**
   - Run production dry run with feature flag disabled.
   - Create launch checklist (backup, migration timing, rollback plan).
   - Enable feature flag for pilot group, monitor, then roll out broadly.

## 6. Dependencies
- Finalization of PRD requirements and design mocks (due before Sprint 2 start).
- Updated design system components for data grid and action drawer.

## 7. Testing Strategy
- Backend unit tests for importer service, custom field validation, bulk update logic.
- Integration tests (FastAPI + DB) for import session lifecycle and custom field CRUD.
- Frontend unit/component tests for mapping UI and reference grids.
- Cypress end-to-end scenarios: CPU import with custom field, bulk edit listings, audit log review.
- Load testing for importer preview endpoints with large datasets.

## 8. Risk Management
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| UX complexity overwhelms operators | Medium | Medium | Iterative feedback sessions, contextual help, simplified defaults |
| Custom fields cause inconsistent analytics | Medium | Low | Limit data types, require admin approval, document usage |

## 9. Deliverables Checklist
- [ ] Migrations and importer backend updates merged (Sprint 1)
- [ ] Mapping UI & bulk preview overrides behind feature flag (Sprint 2)
- [ ] Reference workspace with inline/bulk edit in staging (Sprint 3)
- [ ] Production release with documentation and training complete (Sprint 4)

## 10. Post-Launch Follow-Up
- Monitor importer health metrics for two weeks post-launch.
- Collect operator feedback and prioritize fast-follow fixes.
- Schedule retrospective to capture lessons learned and backlog improvements.

