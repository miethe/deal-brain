# Global Fields & Dynamic Listings Infrastructure

_Last updated: 2025-09-27_

## Overview
The data model now supports operator-defined catalog fields across entities. Core enhancements:

- `custom_field_definition` includes validation metadata, display ordering, and soft-delete handling (`deleted_at`).
- REST endpoints for CRUD support typed validation, multi-select options, and safe removal.
- Import sessions can spawn new fields inline; the mapping grid refreshes instantly without restarting the workflow.
- Listing services expose granular PATCH/bulk update endpoints and a combined schema payload for UI consumption.
- Import commits auto-create missing CPUs referenced by listing rows and record them for audit.

## Database & ORM Changes
- Columns added: `validation_json`, `display_order`, `deleted_at` with index `ix_custom_field_definition_order` on `(entity, display_order)`.
- SQLAlchemy model exposes `.validation` property for Pydantic compatibility.
- Soft delete toggles `is_active=False` and stores `deleted_at`; hard delete remains available via query parameter.

## Service Enhancements
- `CustomFieldService`
  - Supports data types: `string`, `number`, `boolean`, `enum`, `multi_select`, `text`, `json`.
  - Normalises validation rules (regex, numeric bounds, allowed values) per field type with helpful errors.
  - Provides `delete_field(..., hard_delete=False)` for reversible removals.
- `ImportSessionService`
  - `commit` now returns `(counts, auto_created_cpus)` and records audit events for field attachments and auto-created CPUs.
  - `_collect_missing_cpus` detects unmatched CPU names from listings (respecting overrides) and `_auto_create_cpus` persists placeholders before seeding listings.
  - `attach_custom_field` injects the new field into session mappings and logs `custom_field_attached`.

## API Surface

### Custom Fields
- `GET /v1/reference/custom-fields?entity=listings&include_inactive=1&include_deleted=0`
- `POST /v1/reference/custom-fields`
- `PATCH /v1/reference/custom-fields/{id}`
- `DELETE /v1/reference/custom-fields/{id}?hard_delete=0`

### Importer
- `POST /v1/imports/sessions/{id}/fields` → `{field, session}` (used by importer modal)
- `POST /v1/imports/sessions/{id}/commit` → includes `auto_created_cpus`

### Listings
- `GET /v1/listings/schema` → `{core_fields, custom_fields}` with validation metadata
- `PATCH /v1/listings/{id}` → partial update + custom attributes
- `POST /v1/listings/bulk-update` → multi-row updates, returns updated records

## Frontend Hooks
- Importer workspace now features an **Add field** modal with validation-aware controls, posting to the new session endpoint and updating state from the returned snapshot.
- Commit success messaging highlights any auto-generated CPU names.

## Testing
- Expanded unit coverage for `CustomFieldService` (multi-select options, validation rules, error handling).
- Targeted pytest run: `poetry run pytest tests/test_custom_fields_service.py`.

## Follow-Up Ideas
- Extend auto-creation to GPUs and other reference entities.
- Surface auto-created CPUs in the commit confirmation modal (frontend work).
- Build a reusable modal component in the design system for parity with the new importer dialog.
