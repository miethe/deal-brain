# Dynamic Data Grid & Catalog Enhancements Implementation Plan

**Document Info**
- Author: Codex (AI architecture partner)
- Date: 2025-09-30
- Status: Draft for review

## Overview
This plan executes the 9-30 enhancements PRD by delivering adaptive data grids, full global field lifecycle management, and a polished Add Listing flow. Assumes one dedicated full-stack engineer (E1), one frontend engineer (E2), and design support at 0.25 FTE across a 3-week sprint (15 working days). Backend uses FastAPI + SQLAlchemy; frontend uses Next.js + TanStack Table.

## Milestones & Timeline
| Week | Milestone | Exit Criteria |
| --- | --- | --- |
| Week 1 | Architecture & Backend Enablement | Field registry exposes lock state, option CRUD, safe field delete pathway; analytics hooks defined. |
| Week 2 | Data Grid & Global Fields UX | New grid component deployed to staging with resizing, filters, inline/bulk edit; Global Fields UI updated with import CTA and dropdown option management. |
| Week 3 | Listings Creation Modal & Launch Prep | Add Listing modal live on staging, QA complete, rollout checklist signed, training assets recorded. |

## Phase Breakdown

### Phase 1 – Foundations (Days 1-3)
- Finalize design specs (grid layout, modal steps) with Design.
- Extend `FieldRegistry` to expose locked flag, option CRUD endpoints, and soft-delete logic with archival table (`custom_field_attribute_history`).
- Add audit logging utilities capturing actor, action, resource.
- Draft analytics event schema for grid interactions and edits (to console/log sink initially).
- Update API documentation (`docs/api/field-registry.md`).

### Phase 2 – Data Grid Infrastructure (Days 4-7)
- Build reusable `DataGrid` component with virtualization, sticky headers, column resize/drag, zebra stripes, and tooltip support.
- Implement preference persistence service using `localStorage` + environment-aware keys.
- Integrate new grid into Listings and Global Fields data tabs; ensure legacy grid remains behind feature flag for rollback.
- Implement inline edit UX with optimistic updates tied to FieldRegistry endpoints.
- Implement bulk edit drawer with diff preview, rollback (cache original row snapshots), and conflict toast surfaced when a record changed after selection (last-write-wins strategy).

### Phase 3 – Global Fields Enhancements (Days 8-10)
- Add Import CTA button with routing to importer wizard and return breadcrumbs.
- Enhance field edit modal: locked state messaging, dropdown option editor with optimistic UI, danger zone for delete.
- Ensure deleted dropdown options remain visible on historical records but greyed out with tooltip copy "Option no longer available".
- Implement backend job to scrub deleted option references and log affected records.
- Add Playwright coverage for field edit/delete/option flows.

### Phase 4 – Listings Creation Experience (Days 11-13)
- Build multi-step Add Listing modal; fetch schema dynamically and render components based on data types.
- Implement CPU inline creation modal with success injection and error recovery.
- Wire dropdowns to shared multi-select component with search and option creation when permitted.
- Add validation syncing using schema metadata; surface contextual errors and summary banner.
- Instrument success/error events.

### Phase 5 – Hardening & Launch (Days 14-15)
- Execute full regression suite: pytest, mypy (if configured), frontend unit tests, Playwright.
- Conduct performance benchmarking with synthetic 10k row dataset, document outcomes.
- Run staged rollout dry run, validate audit logs and interim logging (config-flagged) for analytics events.
- Prepare enablement assets: Loom walkthrough, quickstart doc update.
- Launch feature flag to internal users; schedule post-launch monitoring checkpoints (Day 17 + Day 24).

## Detailed Task Matrix
| ID | Task | Owner | Dependencies |
| --- | --- | --- | --- |
| BE-01 | Extend FieldRegistry schema (locked flag, option CRUD) | E1 | Phase 1 design sign-off |
| BE-02 | Implement field soft-delete + attribute archival | E1 | BE-01 |
| BE-03 | Add audit logging + analytics hooks | E1 | Existing logging infra |
| BE-04 | Option cleanup background job incl. greyed-out historical option state | E1 | BE-02 |
| FE-01 | Ship DataGrid base component with virtualization | E2 | Design tokens finalized |
| FE-02 | Implement column resize + persistence | E2 | FE-01 |
| FE-03 | Add inline edit & optimistic updates | E2 | BE-01 (endpoints) |
| FE-04 | Build bulk edit drawer | E2 | FE-03 |
| FE-05 | Integrate grid into Listings & Global Fields | E2 | FE-01..04 |
| FE-06 | Import CTA + routing | E2 | BE-01 |
| FE-07 | Field modal enhancements incl. dropdown option editor + historical grey-out | E2 | FE-05 |
| FE-08 | Add Listing modal | E2 | BE-01, Design sign-off |
| FE-09 | CPU inline create modal | E2 | Existing CPU endpoint validation |
| QA-01 | Update and run Playwright specs | QA | FE-05..09 |
| QA-02 | Performance benchmarking | QA | FE-05 |
| DOC-01 | Update docs and record Loom | PM | Phase 5 readiness |

## Testing Strategy
- **Automated**: pytest for FieldRegistry changes, unit tests for bulk edit reducers, Playwright flows covering grid resize persistence, field option edits, and listing creation.
- **Manual**: Cross-browser (Chrome, Safari) smoke tests, accessibility audit with axe, responsive layout checks at 1280px and 1440px widths.
- **Performance**: Benchmark DataGrid with 10k rows × 40 columns; target <100ms scroll latency.

## Deployment & Rollback
- Deploy backend and frontend together behind `NEXT_PUBLIC_FEATURE_DATAGRID_V2` flag.
- Rollback path: revert flag to false; legacy grid still compiled for 1 sprint.
- Database migrations (if any) are additive (history table) and do not block rollback.

## Analytics & Telemetry
- Log events: `grid.column_resize`, `grid.filter_apply`, `bulk_edit.commit`, `field.option_delete`, `listing.create_success`, `listing.create_error`.
- Temporary storage: application logs; plan to route to Segment in future milestone.
- Capture counts and correlate with telemetry to validate success metrics.

## Risks & Mitigations
- **Timeline compression** – Daily standups and mid-week demos; scope guard on lower-priority polish if critical paths slip.
- **Complex bulk edit edge cases** – Implement server-side validation with diff preview; conflict toast communicates last-write-wins outcome to user.
- **Schema drift** – Add contract tests ensuring frontend schema rendering matches backend definitions.
- **Deferred RBAC** – Document gap for future multi-user support; ensure audit logs capture actor for retroactive review.

## Open Work & Follow-Ups
- Confirm security review requirement for bulk edit + field delete endpoints.
- Decide on longer-term storage for user preferences (server vs client) for Q4 roadmap.
- Plan GPU/Ports entity enablement as sequel project once pattern validated.

## Approvals
- Engineering Lead: _Pending_
- Product Lead: _Pending_
- Design Lead: _Pending_
