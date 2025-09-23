# Importer Revamp PRD

## 1. Overview
- **Document Owner:** Strategic Tech Lead (Codex)
- **Last Updated:** 2024-09-22
- **Status:** Draft for stakeholder review
- **Related Docs:** docs/importer-revamp-9-22.md, docs/importer-revamp-implementation-plan.md, docs/importer-usage-guide.md

## 2. Executive Summary
DealBrain operators need a resilient importer that allows them to explicitly declare sheet intent, map columns confidently, capture new attributes without code changes, and manage reference data with the same ergonomics as leading media library tools. The importer revamp delivers a flexible mapping workflow, dynamic custom fields, and a post-import workspace for maintaining CPUs, GPUs, valuation rules, and ports. The end result is higher data quality, faster onboarding of external datasets, and reduced engineering intervention.

## 3. Problem Statement
The current importer assumes schema inference and drops unknown columns, which prevents rapid ingestion of partner datasets, limits experimentation, and risks data mismatches. Reference records become difficult to update after import, requiring manual database work. Operators lack bulk edit tooling and guardrails, creating fear of corrupting reference tables.

## 4. Goals & Non-Goals
### 4.1 Goals
- Allow users to declare the intended entity type(s) for each sheet or file before mapping.
- Provide a guided mapping UI that surfaces suggested, missing, and new columns, with clear confidence scores.
- Support promotion of new columns into custom fields that persist across records and future imports.
- Ensure all imported entities remain fully editable post-import with inline & bulk edit flows.
- Deliver auditability for import decisions, custom field changes, and bulk operations.

### 4.2 Non-Goals
- Building a full schema designer for arbitrary relational relationships.
- Automating approval workflows beyond audit logging and permission checks.
- Replacing existing ETL or data warehouse pipelines.
- Supporting multi-entity sheets (each sheet continues to map to a single entity).

## 5. Target Users & Personas
- **Data Operator (primary):** Operates importer regularly, curates reference tables, needs confidence and speed.
- **Business Analyst:** Reviews import outcomes, performs spot checks, may trigger bulk updates.
- **Administrator:** Manages permissions, resolves mapping conflicts, approves new custom fields.

## 6. User Stories & Use Cases
1. As a data operator, I can upload a workbook, declare that Sheet1 is "CPU", and see the importer pre-map known columns.
2. As a data operator, I can mark an unmapped column as a new attribute, define its label and type, and apply it to all CPUs.
3. As a data operator, I can multi-select rows during import preview to apply a shared override (eg, assign a GPU match).
4. As a business analyst, I can open the Reference workspace, filter CPUs, edit a record inline, and save without leaving the table.
5. As an administrator, I can review audit logs of imports, including custom field additions and bulk edits.

## 7. Functional Requirements
### 7.1 Import Intake
- UI, API, and CLI accept a `declared_entities` payload per sheet/file.
- System validates declared entity against supported schemas and warns when inference disagrees (>15% variance).
- Import session stores declared entities for audit (`import_session.declared_entities_json`).

### 7.2 Column Mapping Workflow
- Mapping view shows three lists: Mapped, Suggested, and New Columns.
- Each suggested column includes: column name, sample data, suggested field, confidence score, rationale.
- Users can override mapping by selecting a different field or setting to Ignored.
- New columns prompt for: label, description (optional), data type (string, number, boolean, enum), default value, visibility scope.
- Saving mappings triggers preview regeneration and audit logging.

### 7.3 Custom Field Framework
- Add `custom_field_definition` table (entity, key, label, data_type, validation, default, created_by, created_at).
- Add `attributes_json` (JSONB) column on CPU, GPU, Listing, ValuationRule, PortsProfile.
- Importer stores values for promoted columns under `attributes_json[custom_key]`.
- APIs expose custom fields in read/write payloads; schema metadata endpoint describes available custom fields.
- Validation honors required flag and data type coherence (numbers, booleans, enums).

### 7.4 Post-Import Reference Workspace
- Sidebar gains "Reference" section with tabs: CPUs, GPUs, Valuation Rules, Ports, Custom Fields.
- Each tab uses data grid with sorting, filtering, inline edit, and multi-select.
- Detail drawer shows standard fields + custom attributes, with ability to edit and save.
- Bulk actions include: Edit field (standard or custom), Attach profile (listings), Delete (soft delete where applicable).

### 7.5 Bulk Edit & Conflict Handling
- Import preview supports row multi-select; available actions: set field value, apply component override, discard row.
- Conflict detection continues for CPU name collisions, now incorporating custom field differences.
- Conflict resolution UI allows choosing existing record, new record, or merge with custom attribute mapping.

### 7.6 Audit & Permissions
- `ImportSessionAudit` records events for declared entities saved, custom fields created, bulk overrides applied, and commit.
- Permission matrix: only admins can create custom fields; operators can map and use existing ones.
- Audit view filters by session, entity, user, and action type.

## 8. Non-Functional Requirements
- Maintain import performance: preview generation for 10k-row sheet completes in under 10 seconds.
- Transactions maintain data integrity when writing custom fields; rollback on failure.
- API responses remain backward compatible for existing clients; new fields flagged as optional.
- Feature toggles to gate release by environment (dev/staging/prod).

## 9. UX & Interaction Notes
- Declared entity selection appears in the upload modal (dropdown with search + tags for multiple sheets).
- Mapping screen uses three-column layout: Sheet Preview, Mapping Panel, Custom Field Builder.
- Reference workspace uses sticky action bar for bulk operations similar to Radarr/Sonarr.
- Bulk action modals mirror importer preview UX for consistency.
- Empty states explain required steps (e.g., "Select a column to map" or "No custom fields created yet").

## 10. Data Model & API Changes
- Database migrations for `custom_field_definition` and `attributes_json` columns.
- Update SQLAlchemy models and Pydantic schemas to include `attributes` dictionary.
- New API endpoints:
  - `GET /reference/custom-fields` (list)
  - `POST /reference/custom-fields` (create)
  - `PATCH /reference/custom-fields/{id}` (update)
  - `POST /reference/{entity}/bulk-update`
- Update `POST /import/sessions` to accept `declared_entities` and return mapping suggestions grouped.

## 11. Analytics & Success Metrics
- Adoption: % of imports with declared entities vs auto-only (target >90% within two weeks of launch).
- Data quality: reduction in post-import manual fixes (target 50% fewer support tickets).
- Speed: average time from upload to commit decreases by 30%.
- Custom field usage: count of active custom fields, and reuse rate across imports.

## 12. Rollout Plan
1. All at once/

## 13. Risks & Mitigations
- **Risk:** Custom fields misused for critical schema elements. **Mitigation:** Admin approval flow and guardrails in UI copy.
- **Risk:** Performance degradation with large `attributes_json`. **Mitigation:** Index frequently queried keys; limit stored value size.
- **Risk:** Bulk edits mistakenly applied to wrong records. **Mitigation:** Confirmation modal summarizing affected rows and undo audit trail.
- **Risk:** API clients not aware of new payload fields. **Mitigation:** Versioned API docs and compatibility testing.

## 14. Open Questions
- Should custom fields support scoped visibility (importer-only vs listing UI)? A: Yes, add visibility flag.
- Do we need enum value management UI for custom fields? A: Yes
- How should we handle localization/label translations for custom fields if required later? A: Plan for future i18n support in schema.

## 15. Approval Checklist
- [ ] Product sign-off (Founder)
- [ ] Engineering sign-off (Backend Lead, Frontend Lead)
- [ ] Design sign-off (UX Lead)
- [ ] Operations sign-off (Importer SME)

