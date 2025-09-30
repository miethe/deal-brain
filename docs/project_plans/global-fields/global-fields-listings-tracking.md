# Global Fields & Listings Implementation Tracking

_Status as of 2025-09-27_

## Legend
- ✅ Complete (validated)
- 🔄 In Progress / Partial
- ⏳ Not Started

## Phase 0 – Discovery & Alignment
| Task | Status | Notes |
| --- | --- | --- |
| Inventory current schemas (listing, cpu, gpu, ports_profile, custom attribute usage) | ✅ | Schema review performed while extending ORM models and services (`apps/api/dealbrain_api/models/core.py:251`; `apps/api/dealbrain_api/services/listings.py:1`). |
| Audit importer mapping flow and identify UI component reuse opportunities | ✅ | Required to retrofit importer workspace with new modal and state management (`apps/web/components/import/importer-workspace.tsx:1`). |
| Confirm RBAC requirements and audit logging expectations with security | ⏳ | No explicit RBAC/audit coordination recorded. |
| Partner with design to scope modal patterns, data grid interactions, navigation adjustments | ⏳ | No dedicated design sync captured; current UI work leveraged existing patterns ad hoc. |
| Deliver kickoff brief (success metrics, timeline, dependencies, risks) | ⏳ | No kickoff artifact produced. |

## Phase 1 – Domain Model & Migrations
| Task | Status | Notes |
| --- | --- | --- |
| Define `field_definition` table with expected columns | ✅ | Added `validation_json`, `display_order`, `deleted_at` plus indexes (`apps/api/dealbrain_api/models/core.py:252`; migration `apps/api/alembic/versions/0005_custom_field_enhancements.py:1`). |
| Generate Alembic migration with data backfill for existing attribute keys | ✅ | Added script-driven backfill utility for dev snapshots (`apps/api/dealbrain_api/services/custom_fields_backfill.py:1`) keeping migrations lightweight per greenfield guidance. |
| Extend ORM models and repositories; expose typed accessors | ✅ | Model exposes `.validation` property and services updated (`apps/api/dealbrain_api/models/core.py:261`; `apps/api/dealbrain_api/services/custom_fields.py:34`). |
| Add audit log table/entries for field changes | ✅ | `custom_field_audit_log` table + service hooks (`apps/api/alembic/versions/0006_custom_field_audit.py:1`; `apps/api/dealbrain_api/services/custom_fields.py:1`). |
| Unit tests for model constraints and validation helpers | ✅ | Added validation-focused tests (`tests/test_custom_fields_service.py:1`). |

## Phase 2 – Backend Services & APIs
| Task | Status | Notes |
| --- | --- | --- |
| Build FieldDefinition service (CRUD, validation, dependency checks, audit emission) | ✅ | Dependency checks, audit writes, analytics events, and usage summaries implemented (`apps/api/dealbrain_api/services/custom_fields.py:1`). |
| Expose REST endpoints `/v1/fields`, `/v1/schemas/listings` | ✅ | `/v1/fields` router with CRUD, history, usage plus legacy proxy for compatibility (`apps/api/dealbrain_api/api/fields.py:1`). |
| Update importer backend to consume definitions and refresh clients | ✅ | New `/sessions/{id}/fields` endpoint and mapping refresh (`apps/api/dealbrain_api/api/imports.py:192`; `apps/api/dealbrain_api/services/imports/service.py:640`). |
| Implement CPU auto-creation workflow with dedupe heuristics & audit logging | ✅ | Auto-create logic with manufacturer guess + audit (`apps/api/dealbrain_api/services/imports/service.py:420`). |
| Extend Listings bulk edit API for dynamic fields & multi-row transactions | ✅ | Added `/v1/listings/bulk-update` endpoint and service support (`apps/api/dealbrain_api/api/listings.py:191`; `apps/api/dealbrain_api/services/listings.py:120`). |
| Integration tests (fields CRUD, importer field creation, CPU auto-create, bulk edit) | 🔄 | Added async coverage for field guardrails; importer/listings scenarios still pending (`tests/test_custom_fields_integration.py:1`). |

## Phase 3 – Field Management Frontend
| Task | Status | Notes |
| --- | --- | --- |
| Implement Global Fields tab UI (grid, filters, status chips, usage count) | ✅ | React Table grid with filters, status toggles, usage badges (`apps/web/components/custom-fields/global-fields-table.tsx:1`). |
| Create field create/edit modal wizard with validation preview | ✅ | Multi-step wizard with validation preview and JSON payload review (`apps/web/components/custom-fields/global-fields-table.tsx:347`). |
| Hook into APIs with optimistic updates and error handling | ✅ | React Query mutations with optimistic cache updates and inline errors (`apps/web/components/custom-fields/global-fields-table.tsx:198`). |
| Audit log drawer displaying change history | ✅ | Audit drawer backed by `/v1/fields/{id}/history` (`apps/web/components/custom-fields/global-fields-table.tsx:612`). |
| Instrument analytics events for field operations | ✅ | Frontend analytics hooks + backend emission (`apps/web/components/custom-fields/global-fields-table.tsx:212`; `apps/api/dealbrain_api/services/custom_fields.py:72`). |
| Frontend unit & storybook coverage | ⏳ | No new tests/stories committed. |

## Phase 4 – Importer Enhancements
| Task | Status | Notes |
| --- | --- | --- |
| Add “Add New Field…” option with modal and schema refresh | ✅ | Importer modal creates fields inline (`apps/web/components/import/importer-workspace.tsx:262`). |
| Update mapping preview to immediately include new fields & validation messaging | ✅ | `attach_custom_field` refreshes mappings and preview (`apps/api/dealbrain_api/services/imports/service.py:615`). |
| Surface auto-created CPU summary in commit confirmation/history | ✅ | Commit response now returns `auto_created_cpus` and UI message surfaces them (`apps/api/dealbrain_api/api/imports.py:212`; `apps/web/components/import/importer-workspace.tsx:329`). |
| Emit analytics events (`import_field_created`, `cpu_autocreated`) | ⏳ | No analytics instrumentation implemented. |
| Playwright/Cypress tests for new flow | ⏳ | No e2e tests added. |

## Phase 5 – Listings Workspace Upgrades
| Task | Status | Notes |
| --- | --- | --- |
| Refactor Listings grid for dynamic schema & type-aware cells | ✅ | Grid consumes `/v1/listings/schema` and renders dynamic columns (`apps/web/components/listings/listings-table.tsx:65`). |
| Implement inline edit with optimistic persistence and undo | 🔄 | Inline edits submit on blur but lack explicit undo/optimistic rollback (`apps/web/components/listings/listings-table.tsx:195`). |
| Build bulk edit drawer with apply/undo workflow | 🔄 | Bulk apply implemented without undo support (`apps/web/components/listings/listings-table.tsx:363`). |
| Add column filters, multi-sort, group-by, state persistence | 🔄 | Filters/sorting/grouping exist; no persistence across sessions (`apps/web/components/listings/listings-table.tsx:270`). |
| Remove nested Listings header; ensure layout coherence | ✅ | Table rendered without nested heading (verified in refactored component). |
| Extend analytics instrumentation for inline/bulk usage | ⏳ | No analytics events added. |
| Performance testing ≥10k rows / 50 fields | ⏳ | No perf testing evidence. |

## Phase 6 – Reference Hub & Manual Forms
| Task | Status | Notes |
| --- | --- | --- |
| Update sidebar navigation (Global Fields tab, Reference hub subtabs) | 🔄 | Global Fields nav added (`apps/web/components/app-shell.tsx:10`); Reference hub tabs pending. |
| Implement shared grid for Reference entities with inline/bulk edit | ⏳ | Not delivered. |
| Update manual listing form for dynamic schema + “Add new CPU” modal | ⏳ | Manual form untouched. |
| QA regression for manual entry flow | ⏳ | Not run/documented. |

## Phase 7 – Stabilization, Docs, Launch
| Task | Status | Notes |
| --- | --- | --- |
| Finalize unit/integration/e2e coverage; resolve flakes | 🔄 | Added targeted unit tests only (`tests/test_custom_fields_service.py:1`). |
| Conduct load testing for API endpoints | ⏳ | Not executed. |
| Update documentation & training materials | 🔄 | Importer guide and new backend/frontend notes updated (`docs/importer-usage-guide.md:1`; `docs/global-fields-backend.md:1`; `docs/listings-workspace-notes.md:1`). |
| Configure Metabase dashboards & alerting | ⏳ | Not attempted. |
| Run stakeholder UAT; collect sign-offs | ⏳ | Not completed. |
| Prepare release notes, feature flag plan, rollout/rollback procedures | ⏳ | Not prepared. |

## Testing & Tooling Tasks
| Task | Status | Notes |
| --- | --- | --- |
| Unit tests (validation utilities, CPU auto-create, bulk edit handlers) | 🔄 | Validation tests added; auto-create & bulk edit still lack dedicated coverage. |
| Integration tests (field CRUD, importer flow, listings bulk) | ⏳ | Not implemented. |
| E2E tests (importer field creation, listings grid) | ⏳ | Not implemented. |
| Performance benchmarks | ⏳ | Not implemented. |
| Accessibility scans | ⏳ | Not implemented. |

## Release & Rollout Tasks
| Task | Status | Notes |
| --- | --- | --- |
| Feature flag gating for new UI | ⏳ | No flag implementation observed. |
| Migration runbook with rollback path | ⏳ | Not documented. |
| Staged rollout plan | ⏳ | Not documented. |
| Monitoring dashboards for error/latency/adoption | ⏳ | Not configured. |
| Support plan for ops (office hours, FAQ, escalation) | ⏳ | Not prepared. |

## Summary
Core backend capabilities, importer integration, and listings grid have been delivered. Design/analytics work, advanced QA (integration/e2e, load, accessibility), Reference hub build-out, and launch-readiness tasks remain outstanding.
