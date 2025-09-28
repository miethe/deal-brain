# Global Catalog Fields & Listings Workspace PRD

## Summary
Deliver a dynamic data model and UI that lets operators add and manage catalog fields without engineering support, extend the importer to create those fields on the fly, and upgrade the Listings workspace with inline, bulk, and analytical controls.

## Background & Problem Statement
- Current schema hard-codes listing attributes, requiring migrations for every new hardware trait.
- Imports fail when spreadsheets include columns that have no schema support.
- Analysts duplicate effort in spreadsheets while waiting on engineering.
- CPU records must be pre-created, causing friction during manual entry and imports.
- Listings data grid lacks modern tooling for inline updates, filters, grouping, and bulk edits.
- September importer revamp documentation highlights operator frustration with missing schema flexibility.

## Goals
1. Empower operations staff to add, edit, and delete global fields for Listings, CPUs, GPUs, Ports, and Valuation Rules in under two minutes.
2. Ensure importer sessions complete without schema blockers and automatically create referenced CPUs when missing.
3. Boost analyst throughput on Listings table via inline and bulk edits plus advanced filters and grouping, maintaining <1% error rate.
4. Ship navigation updates (Global Fields, Reference hub) with cohesive UX that centralizes catalog governance.

## Success Metrics
- ≥80% of new attribute requests resolved via UI (no engineering tickets).
- ≥60% of imports that previously failed on missing columns now complete successfully.
- ≥70% of weekly active analysts adopt inline or bulk edits in Listings.
- Median Listings edit session time reduced by 40%.
- Post-launch user satisfaction survey for new tooling ≥4.3/5.

## Personas
- **Ops Analyst**: Maintains listing data, needs quick edits and imports.
- **Catalog Lead**: Defines taxonomy standards, governs fields.
- **Data Engineer**: Ensures data integrity, monitors performance.
- **Import Agent**: Runs bulk loads, resolves mapping gaps.
- **Product Manager**: Tracks adoption and quality metrics.

## In Scope
- Global field definition system supporting string, number, boolean, enum, and multi-select types with validation, defaults, display order, and soft delete.
- Field lifecycle management, audit log, and impact analysis within new Global Fields UI.
- Automatic propagation of new fields to importer mapping, manual entry forms, and Listings grid.
- Importer modal to add new field during mapping; session immediately reflects added field.
- Automatic CPU creation when importing or manually adding listings with missing CPU references.
- Listings data grid upgrades: inline edit, multi-row bulk edit, per-column filter/sort, group-by, and state persistence.
- Sidebar navigation updates: dedicated Global Fields tab and Reference hub with entity subtabs.
- Removal of nested Listings title on Listings page.

## Out of Scope
- Per-tenant field visibility or RBAC expansion.
- Advanced validation scripting beyond regex, ranges, and enum lists.
- Historical backfill for existing records beyond default values.
- GPU auto-creation heuristics (future consideration).
- Exporting custom schema definitions or API public exposure.

## Functional Requirements
### Global Field Management
- Persist entity-agnostic `FieldDefinition` with metadata: key, label, type, default, validation, options, display order, created_by, timestamps, soft delete.
- Present searchable, filterable field list with usage counts and status tags.
- Provide create/edit modal wizard with live validation preview and duplicate detection.
- Enforce soft delete with dependency check (prevent removal if active or require confirmation with impact summary).
- Surface change history (who/when/what changed) for each field.

### Importer Enhancements
- Mapping dropdown includes "Add New Field…"; opens modal matching Global Fields flow scoped to entity.
- Newly created field appears in mapping instantly without refreshing session.
- Import engine recognizes new definitions and validates incoming data accordingly.
- Automatic CPU creation when no match found; record provenance in audit log and allow optional manual overrides.
- Commit summary lists any auto-created CPUs and field definitions added during session.

### Listings Workspace
- Inline edit for all fields (core and custom) with type-aware controls, validation messaging, # undo within session.
- Bulk edit panel supporting set, clear, append operations for selected rows; track success/failure and rollback on partial errors.
- Per-column filter UI (text search, numeric range sliders, enum chips, multi-select) with saved filter presets.
- Sort toggles (asc/desc) on every field; support multi-sort priority.
- Group-by control enabling grouping by any field (one level) with aggregate counts and key metrics per group.
- Persist table state (columns, filters, groupings) per user.
- Remove nested Listings header to declutter UI.

### Reference Hub & Navigation
- Sidebar adds Global Fields tab and Reference section with subtabs (CPUs, GPUs, Valuation Rules, Ports, Custom Fields).
- Each reference tab uses shared grid component with inline/bulk edit, filters, and create modals.
- Manual listing form consumes dynamic schema, includes "Add new CPU" modal mirroring importer behavior.

## Non-Functional Requirements
- Maintain backward compatibility for existing `attributes_json` data; zero downtime migrations.
- Inline edits persist within 300 ms median round trip; importer field creation responds within 1 s.
- API endpoints authenticated and authorized with current RBAC; log every create/update/delete.
- Accessibility: WCAG 2.1 AA compliance for new modals, grids, and controls.
- Audit logs retained ≥12 months.

## UX & Design Principles
- Follow importer revamp visual language (modal layout, typography, tone).
- Use design system components for inputs, chips, data grids, and notifications.
- Provide context tooltips for validation options and field types.
- Bulk edit drawer communicates impact, includes confirmation before apply.
- CPU creation modal auto-suggests manufacturer/socket based on entered name when possible.

## Data & Analytics
- Emit events: `field_definition.created`, `.updated`, `.deleted`, `import_field_created`, `cpu_autocreated`, `listings_inline_edit_success`, `listings_bulk_edit_success`/`failure`, `listings_filter_applied`.
- Capture latency metrics for inline edit, bulk edit, and importer field creation endpoints.
- Extend Metabase dashboards to monitor adoption, error rates, and performance.

## Dependencies
- FastAPI/SQLAlchemy backend for new models & endpoints.
- Next.js frontend with component library upgrades for data grid features.
- Redis/event bus reuse for live updates and importer status.
- Coordination with design, ops enablement, and QA automation teams.

## Risks & Mitigations
- **Schema drift**: Centralize validation in service layer, add contract tests.
- **Performance degradation**: Lazy-load field metadata, server-side pagination/caching.
- **CPU duplication**: Normalized matching, highlight similar names, require confirmation when confidence low.
- **User overwhelm**: Provide templates, default presets, updated documentation and training.

## Release Criteria
- Unit & integration coverage for new domain services and APIs.
- End-to-end tests for field creation, importer mapping, inline and bulk edits.
- Migration plan validated on staging snapshot with rollback instructions.
- Documentation updates complete; training delivered to ops team.
- Monitoring dashboards ready with alert thresholds.

## Open Questions
- Should custom fields include per-tenant visibility controls in MVP? A: No, defer to future phase.
- What governance rules apply to deleting fields containing historical data? A: Soft delete with impact analysis only.
- Do we need GPU auto-creation parity now or later? A: Now, same logic as CPU.
- Confirm analytics platform ownership for new events.
