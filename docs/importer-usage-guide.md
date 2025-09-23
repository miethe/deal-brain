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
- The API writes the batch via `ImportSessionService.commit`, which builds a `SpreadsheetSeed` and calls `apply_seed`. A success message returns the updated session snapshot and per-entity counts.

## 6. API Reference
- `POST /v1/imports/sessions` (multipart `upload`, optional `declared_entities` JSON string) → `ImportSessionSnapshot`
- `POST /v1/imports/sessions/{id}/mappings` (JSON) → updated snapshot with previews/conflicts
- `POST /v1/imports/sessions/{id}/conflicts` → conflict refresh (auto-invoked after mapping save)
- `POST /v1/imports/sessions/{id}/commit` → `{status, counts, session}`
- `GET /v1/reference/custom-fields` → list of custom field definitions (filterable by `entity`)
- `POST /v1/reference/custom-fields` → create a new custom field (admin only)
- `PATCH /v1/reference/custom-fields/{id}` → update label, validation, visibility, or activation state

## 8. Declared Entities & Custom Fields
- **Declared entities** are stored on the import session (`declared_entities_json`). If the system inference disagrees, the audit log records a `declared_entity_mismatch` event so you can investigate quickly.
- The mapping UI now shows the declared type in the sheet header and defaults the suggestions to that entity.
- When you elevate an unmapped column to a custom field, the backend creates or reuses a `custom_field_definition` record and stores values under each entity’s `attributes_json` column.
- Manage custom fields from the Reference → Custom Fields tab or the REST API. Enum fields require at least one option; other types default to free-form text.
- Custom attributes surface alongside core fields in previews, bulk edits, and the new reference workspace grids.

## 7. Operational Notes
- Uploaded files are deduplicated via SHA256 checksum recorded on the session.
- RapidFuzz dependency (`rapidfuzz==3.6.1`) powers fuzzy column scoring and component matches.
- Sessions remain available for read-only audit; rerunning the importer simply creates a new session ID.
