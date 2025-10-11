# RAM & Storage Catalog Integration Guide

This guide summarizes the catalog-powered RAM and storage workflow introduced on 2025-10-11. It covers backend APIs, frontend components, and operational considerations so engineers can extend the valuation stack without re-reading the full PRD.

## Backend: Catalog APIs & Services
- **Endpoints** (FastAPI):
  - `GET /api/v1/catalog/ram-specs`: query by `search`, `generation`, `min_capacity_gb`, `max_capacity_gb`, `limit`. Results include `id`, `ddr_generation`, `speed_mhz`, and capacity metadata.
  - `POST /api/v1/catalog/ram-specs`: accepts RAM spec payloads (`ddr_generation`, `total_capacity_gb`, optional speed/module metadata). Reuses the shared resolver to dedupe neighbours.
  - `GET /api/v1/catalog/storage-profiles`: supports `search`, `medium`, capacity filters, and returns medium/interface/tier fields.
  - `POST /api/v1/catalog/storage-profiles`: upserts storage profiles with normalization shared with listing services.
- **Shared helpers** live in `apps/api/dealbrain_api/services/component_catalog.py` and power the API, listing normalization, seeds, and importers. Use these helpers whenever you touch component metadata—no bespoke normalization.
- **Seeds & importer**:
  - Spreadsheet seeds now support `ram_specs` and `storage_profiles` arrays (see `packages/core/dealbrain_core/schemas/imports.py`).
  - `seed_component_catalog` bootstraps canonical specs/profiles for RAM DDR4/DDR5 and NVMe/SATA/HDD drives.
  - Universal importer accepts `ram_spec` and `storage_profile` entities to hydrate the catalog from CSV/JSON.

## Frontend: Selector Components & Inline Editing
- **Reusable components**:
  - `RamSpecSelector`: async combobox backed by `/catalog/ram-specs`, inline create dialog, and telemetry (`ram_spec.select` / `.create`). Selecting a spec pushes capacity into the form/table automatically.
  - `StorageProfileSelector`: mirrored behaviour for storage profiles with medium filter tabs and telemetry (`storage_profile.select` / `.create`).
- **Add Listing form** (`apps/web/components/listings/add-listing-form.tsx`):
  - Selecting catalog items fills RAM totals, storage capacities, and storage type inputs. Submissions send `ram_spec_id`, `primary/secondary_storage_profile_id`, and keep legacy fallbacks for manual entries.
  - Form reset clears selector state, ensuring fresh entries start with blank data.
- **Listings table inline edit** (`listings-table.tsx`):
  - `EditableCell` detects `ram_spec_id` / `primary_storage_profile_id` / `secondary_storage_profile_id` and renders selectors.
  - `buildUpdatePayload` fans out derived updates (e.g., set `ram_gb` with spec capacity, update storage type labels).
  - Selectors play nicely with existing mutation/error flows and emit analytics events.

## Rule Builder Enhancements
- The entities metadata service (`FieldMetadataService`) now exposes:
  - `ram_spec.*` fields (generation, speed, capacities).
  - `storage.primary.*` and `storage.secondary.*` fields (medium, capacity, tier, interface, form factor).
- The rule builder UI immediately picks up these fields, allowing analysts to author predicates such as `ram_spec.ddr_generation equals ddr5` or `storage.primary.medium equals nvme`. No frontend hard-coding required.
- `RuleBuilderModal` emits analytics (`valuation_rule.created` / `.updated`) for visibility into authoring activity.

## Telemetry & Observability
- All selector interactions dispatch analytics events via `window` (`ram_spec.*`, `storage_profile.*`). Hook into `dealbrain-analytics` if you need to forward to external tooling.
- Rule builder saves now emit structured events with rule/group IDs and condition/action counts.

## Operational Notes
- No new migrations were introduced; all changes ride on Alembic revision `0017`.
- Always rely on `component_catalog` service helpers when manipulating specs/profiles to keep normalization consistent.
- Seeder defaults can be adjusted in `apps/api/dealbrain_api/seeds/component_catalog.py` if you expand supported tiers.
- When adding new valuation logic or UI surfaces, consume `getRamGenerationLabel` / `getStorageMediumLabel` from `apps/web/lib/component-catalog.ts` to keep labelling consistent.
