# Importer Usage Guide

## 1. Uploading a Workbook
1. Navigate to `/import` in the web app.
2. Drag-and-drop a `.xlsx`, `.csv`, or `.tsv` file (or use the select button). The backend stores the upload under `data/uploads/{session_id}/source` and returns a session snapshot.
3. For each sheet, pick the intended entity (CPU, GPU, Listing, Ports Profile, Valuation Rule). Declared types are submitted with the upload and immediately applied on the backend.
4. The header card confirms detected sheets, declared types, and provides the session identifier for audit/reference.

## 2. Mapping Fields
- Use the tabs to switch between entities (CPUs, GPUs, Valuation Rules, Ports Profiles, Listings).
- Autodetected columns are marked as **Auto** with a confidence percentage. Changing a select input records a manual mapping.
- Required fields without a mapping are highlighted. Add a column and click **Save mapping** before leaving the tab.
- If a column represents a brand-new attribute, click **Add field** to launch the in-session field builder. You can define the label, data type, validation, and options without leaving the importer. The newly created field appears immediately in the mapping grid and persists to the tenant schema.
- Saving triggers `/v1/imports/sessions/{id}/mappings` followed by `/conflicts`, refreshing previews and conflict status in one step.

## 3. Reviewing Previews & Matches
- The preview table shows the first few rows for the active entity. If values look off, adjust the mapping and re-save.
- Listings include a **Listing component matches** panel. Rows are tagged as `Auto`, `Needs review`, or `Unmatched` based on RapidFuzz scores against existing CPUs.
- Use the dropdown to override a CPU suggestion. Leaving it blank keeps the row unmatched.

## 4. Resolving Conflicts
- CPU conflicts appear in the **Conflicts** card with a diff for each field that would change.
- Choose one of `Update`, `Skip`, or `Keep` for every conflict. These selections become the `conflict_resolutions` payload during commit.

## 5. Committing
- Ensure every conflict has a decision and mappings are saved.
- Click **Commit import**. The frontend submits:
  ```json
  {
    "conflict_resolutions": [
      {"entity": "cpu", "identifier": "Intel Core i7-8700", "action": "update"}
    ],
    "component_overrides": [
      {"entity": "listing", "row_index": 2, "cpu_match": "Intel Core i7-8700"}
    ]
  }
  ```
- The API writes the batch via `ImportSessionService.commit`, which builds a `SpreadsheetSeed` and calls `apply_seed`. Missing CPUs referenced by the listing sheet are now auto-created before the seed runs and surfaced in the response (`auto_created_cpus`).
- A success message returns the updated session snapshot, per-entity counts, and any auto-generated CPU names.

## 6. API Reference
- `POST /v1/imports/sessions` (multipart `upload`, optional `declared_entities` JSON string) → `ImportSessionSnapshot`
- `POST /v1/imports/sessions/{id}/mappings` (JSON) → updated snapshot with previews/conflicts
- `POST /v1/imports/sessions/{id}/conflicts` → conflict refresh (auto-invoked after mapping save)
- `POST /v1/imports/sessions/{id}/fields` → create a custom field in-line and receive the refreshed session snapshot
- `POST /v1/imports/sessions/{id}/commit` → `{status, counts, session, auto_created_cpus}`
- `GET /v1/reference/custom-fields` → list of custom field definitions (filterable by `entity`)
- `POST /v1/reference/custom-fields` → create a new custom field (admin only)
- `PATCH /v1/reference/custom-fields/{id}` → update label, validation, visibility, or activation state
- `DELETE /v1/reference/custom-fields/{id}` → soft delete (and optionally hard delete) a field

## 7. Declared Entities & Custom Fields
- **Declared entities** are stored on the import session (`declared_entities_json`). If the system inference disagrees, the audit log records a `declared_entity_mismatch` event so you can investigate quickly.
- The mapping UI shows the declared type in the sheet header and defaults the suggestions to that entity.
- Field creation during mapping writes a `custom_field_definition` record with validation, display order, and audit metadata, then refreshes the session state so the field can be mapped immediately.
- Manage custom fields from the Reference → Custom Fields tab or the REST API. Enum and multi-select fields require at least one option.
- Soft deleting a field sets `deleted_at` and hides the field from mapping unless `include_deleted=true`.

## 8. Automatic CPU Creation
- During commit, any listing rows referencing CPUs that do not exist are materialised as lightweight CPU records before listings are upserted. Manually entered overrides are respected.
- Newly created CPUs are annotated (`attributes_json.auto_created_from_import`) with the import session ID for easy auditing.
- The commit payload now includes `auto_created_cpus` so operators can review what was generated automatically and reconcile details later.

## 9. Operational Notes
- Uploaded files are deduplicated via SHA256 checksum recorded on the session.
- RapidFuzz (`rapidfuzz==3.6.1`) powers fuzzy column scoring and component matches.
- Sessions remain available for read-only audit; rerunning the importer simply creates a new session ID.
