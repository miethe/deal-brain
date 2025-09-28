# Listings Workspace Enhancements

_Last updated: 2025-09-27_

## What Changed
- Listings table now exposes partial and bulk update APIs to support inline/bulk edit tooling.
- Schema endpoint merges core columns with tenant-defined custom fields so the frontend can render dynamic grids.
- Custom attributes are stored under `attributes_json` and updated atomically alongside core columns.

## API Summary
- `GET /v1/listings/schema` → returns `core_fields` (static metadata) and `custom_fields` (live definitions).
- `PATCH /v1/listings/{id}` → accepts `{fields: {...}, attributes: {...}}` for single-record edits.
- `POST /v1/listings/bulk-update` → accepts `{listing_ids: [], fields: {...}, attributes: {...}}`; returns updated listings and count.

## Usage Patterns
- Inline edit: fetch schema, render appropriate input per `data_type`, submit via PATCH with a single field.
- Bulk edit: allow users to select listings, choose a field, and send a bulk update payload (null values remove custom attributes).
- Custom fields: look up metadata from schema response (validation, options) to drive form controls.

## Backend Notes
- `partial_update_listing` and `bulk_update_listings` centralise attribute merging and re-run `apply_listing_metrics` so derived scores stay fresh.
- Allowed mutable columns are defined by `MUTABLE_LISTING_FIELDS` to avoid overwriting computed metrics accidentally.

## Next Steps
- Wire the listings grid to consume the schema payload and call the new endpoints.
- Introduce optimistic UI updates and undo affordances backed by the PATCH/ bulk APIs.
