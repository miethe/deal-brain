# Importer Revamp

## Current State

- Existing flow auto-detects entity per sheet and maps suggested columns via _generate_initial_mappings and _auto_map_fields, but it lacks a way for the operator to assert “this is a CPU sheet” or flag unexpected columns apps/api/dealbrain_api/services/imports/service.py:694, apps/api/dealbrain_api/services/imports/service.py:705, apps/api/dealbrain_api/services/imports/service.py:717.
- Schemas are rigid tuples of predefined fields, so anything outside SchemaField definitions is dropped; there is no persistence layer for custom attributes apps/api/dealbrain_api/services/imports/specs.py:18, apps/api/dealbrain_api/services/imports/specs.py:63.
- UI currently doesn’t expose a reference workspace where CPUs, GPUs, valuation rules, etc. can be browsed/edited post-import, nor bulk edit mechanics mirroring Radarr/Sonarr.

## Proposed Enhancements

- Declarative file typing: add a required declared_entities payload (CLI flag, API field, UI dropdown) captured on ImportSession. Use it to (1) shortcut schema inference, (2) scope the column matcher, (3) drive combined uploads by mapping multiple sheets to explicitly chosen entities. Keep inference as fallback but surface warnings when declared type and heuristic disagree.

- Column mapping UX: extend the mapping step to show three buckets: mapped, unmapped-but-suggested, and “new fields”. Allow the operator to assign a column to an existing field, mark it ignored, or promote it to a new field.

- Dynamic attribute framework: introduce per-entity custom metadata. Suggested storage: add attributes_json to CPU/GPU/Listing tables (and any other reference models), plus a new custom_field_definition table keyed by entity with metadata (label, type, validation, default, visibility). Importer writes column metadata when user opts to “add to all records”. Listing components can continue to store structured data through metadata_json.

- Reference management UI: redesign navigation with a “Reference” section containing tabs (CPUs, GPUs, Valuation Rules, Ports, Custom Fields). Each tab uses a data grid with inline edit, filters, and persistent search. Detail drawer exposes full record, including dynamic attributes. Everything remains editable after import, using existing CRUD endpoints extended for custom fields.

- Bulk editing: implement multi-select in importer preview to apply overrides (e.g., component matches, shared attribute values) before commit. Mirror the pattern on listing/CPU/GPU grids: select items, pick an action (update field, attach profile, delete). Back these actions with new batch endpoints that validate against the same schemas.

- Safety / audit: expand ImportSessionAudit entries when custom fields created or batch updates applied; expose diff preview before commit. Add role/permission checks so only authorized users manage schema changes.

## Delivery Plan

- Sprint 1: backend groundwork. Migrate DB (attributes JSON columns + custom field definitions), update pydantic models, write CRUD endpoints, augment importer service to accept declared entities and produce new mapping payload.
- Sprint 2: importer experience. Build mapping UI with new column buckets, validations, preview/bulk override tooling, CLI/API parameter updates, automated tests for new flows.
- Sprint 3: reference workspace. Implement Next.js navigation restructure, data grids, inline edit forms, bulk action drawer, API integration. Add regression coverage (unit + integration + Cypress).
- Sprint 4: polish & rollout. Permission gates, audit logs, documentation updates, importer usage guide revision, release notes, and migration playbook for existing operators.

## Next Steps

- Confirm acceptance of JSON-based custom fields vs. additive columns, plus target data types and validation rules.
- Decide whether combined uploads should support cross-entity columns in a single sheet or enforce one entity per sheet. A: There should be a single entity per sheet for combined uploads.
