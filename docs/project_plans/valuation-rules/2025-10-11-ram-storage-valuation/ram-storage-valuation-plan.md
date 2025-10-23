# Implementation Plan: RAM & Storage Classification & Valuation

## Objectives
- Establish structured RAM and Storage entities so listings capture type, speed, interface, and capacity consistently.
- Enable valuation rules to price RAM and Storage using per-unit baselines plus spec-based modifiers.
- Unify Storage Option 1 and 2 on a single backend model while keeping the UX simple for dual-drive configurations.

## Milestones
- **M1 – Schema & default fields ready (Week 1)**: Alembic migration merged, RAM/Storage entities available, listings expose `ram_spec` and storage profile references, existing data backfilled.
- **M2 – Service & valuation wiring (Week 2)**: API, ingestion, and valuation ruleset engine consume the new models and apply spec-aware pricing.
- **M3 – Frontend UX & analytics (Week 3)**: Listing forms, catalog views, and valuation editors surface the new controls; telemetry and docs updated.

## Workstream 1 – Data Model & Default Fields
1. Create `ram_spec` table with columns: `id`, `ddr_generation` (enum backed by `ram_type`), `speed_mhz`, `module_count`, `capacity_per_module_gb`, `total_capacity_gb`, `notes_json`. Seed canonical specs (e.g., DDR4-2400, DDR5-5600).
2. Create `storage_profile` table with columns: `id`, `medium` (enum: NVMe, SATA SSD, HDD, Hybrid), `interface`, `form_factor`, `capacity_gb`, `performance_tier`, `attributes_json`.
3. Add nullable `ram_spec_id`, `primary_storage_profile_id`, and `secondary_storage_profile_id` foreign keys to `listing`. Retain existing capacity columns for now; mark them derived.
4. Introduce default listing fields `ram_type` and `ram_speed_mhz` (pulled from `ram_spec`) in `FieldRegistry._listing_core_fields` so builders can filter/sort without joining.
5. Backfill migration: derive `ram_spec` entries from existing `ram_gb`, `ram_notes`, `attributes_json`; default to “Unknown DDRx TBD” when classification fails. Map existing primary/secondary storage fields into `storage_profile` rows keyed by `(medium, capacity)` to minimise duplication.
6. Update ORM models (`apps/api/dealbrain_api/models/core.py`) with relationships: `ram_spec`, `primary_storage_profile`, `secondary_storage_profile`. Add SQLAlchemy enums for RAM type & storage medium.
7. Extend Pydantic schemas (`dealbrain_core/schemas/listings.py`) and TS clients to surface the new relationships plus flattened `ram_type`/`ram_speed_mhz`.

## Workstream 2 – Services, Registry & Importers
1. Expand `FieldRegistry` serialization to embed RAM/Storage metadata (e.g., nested objects with `id`, `type`, `speed_mhz`, `capacity_gb`). Ensure `RecordPayload` normalization accepts spec/profile IDs while keeping legacy payloads functional.
2. Update listing create/update flows (`apps/api/dealbrain_api/services/listings.py`, `api/listings.py`) to:
   - Resolve or upsert `ram_spec` via helper (similar to `ports.get_or_create_ports_profile`).
   - Reuse a shared storage profile resolver for both primary and secondary drives.
   - Maintain backward compatibility: if callers still send `ram_gb` or `primary_storage_type`, infer or link appropriate profiles; log deprecation warnings.
3. Adjust importer scripts (`scripts/import_entities.py`, `apps/api/dealbrain_api/importers/universal.py`) to normalize RAM/Storage inputs, populate classification enums, and cache lookups for performance.
4. Add seeding utilities (`apps/api/dealbrain_api/seeds.py`) to bootstrap a starter catalog of RAM specs and storage profiles so valuation rules have IDs to target.

## Workstream 3 – Valuation Engine & Rules
1. Extend rule condition schema to allow predicates on `ram_spec.ddr_generation`, `ram_spec.speed_mhz`, `storage.medium`, `storage.performance_tier`, and capacity bands.
2. Update per-unit metrics (`apps/web/lib/valuation-metrics.ts`, backend rule evaluation helpers) to support:
   - RAM per-unit pricing keyed by `ram_spec.total_capacity_gb`.
   - Storage per-unit pricing by profile capacity for both `primary` and `secondary` selectors (sharing the same backend metric definition with `context: "primary" | "secondary"`).
3. Introduce rule actions for additive/multiplicative modifiers based on RAM/Storage attributes (e.g., +$X for DDR5, multiplier for >5200 MHz, separate NVMe tiers).
4. Update valuation calculation pipeline (`apps/api/dealbrain_api/services/valuation.py` or equivalent) so:
   - Listing context includes `ram_spec` and both storage profiles.
   - Base per-unit price is computed once, then modifiers apply according to device profile (gaming workstation types). Consider adding listing `usage_profile` attribute for weighting.
5. Ensure recalculation task enqueues whenever RAM/Storage specs or linked profiles change; include targeted batch recalculation for affected listings.
6. Expand regression test matrix to include scenarios: DDR4 vs DDR5 pricing, NVMe vs HDD modifiers, mixed drive configurations, and legacy fallback.

## Workstream 4 – Frontend Listing & Valuation UX
1. Update shared listing types and hooks to include `ram_spec` and `storage_profile` objects plus flattened type/speed fields.
2. Listing create/edit forms (`apps/web/app/listings/...`) should:
   - Provide dropdowns/autocomplete for RAM type (DDR3/4/5/LP variants) and speed (derived from spec catalog).
   - Allow quick entry mode that accepts total GB + type/speed, creating a transient spec if needed.
   - Surface primary/secondary storage selectors backed by the unified profile list with capacity + interface descriptors.
3. Enhance valuation rule builders:
   - Add condition chips for RAM type/speed and storage medium/performance.
   - Support choosing per-unit metric “RAM Spec (GB)” vs “Storage Profile (GB)” with context (Primary/Secondary).
   - Allow stacking modifiers (e.g., +$X per GB for DDR5 plus fixed uplift for >6000 MHz).
4. Update catalog/listing detail views to display structured RAM info (type, speed, module count) and storage badges (NVMe 1TB, HDD 2TB) while maintaining existing capacity fields for readability.
5. Wire analytics events for RAM/Storage spec changes and valuation rule modifications so adoption can be tracked.

## Workstream 5 – Operations, Docs & Rollout
1. Draft migration runbook covering spec/profile seeding, backfill verification, and rollback strategy (include SQL to revert FK columns safely).
2. Update documentation (`docs/project_plans/.../prd.md`, user help center pages) describing the new RAM/Storage classification workflow and valuation flexibility.
3. Refresh valuation strategy templates so pricing analysts know how to configure modifiers for gaming vs workstation profiles.
4. Create QA checklist with sample listings spanning common configurations (e.g., DDR4-3200 + NVMe, DDR5-6000 + dual drives) to validate UI, API, and valuation outputs.
5. Plan phased rollout: enable schema in release branch, run backfill, then toggle frontend controls behind feature flag until valuation rules are updated.

## Acceptance Criteria & Metrics
- 100% of active listings have a linked `ram_spec` and at least one `storage_profile` after backfill, with no null `ram_type`/`ram_speed_mhz`.
- Valuation engine applies differentiated pricing for DDR4 vs DDR5 and NVMe vs HDD in regression scenarios with zero calculation drift.
- Frontend forms support selecting from shared RAM/Storage catalogs without manual JSON edits, and telemetry confirms usage within first sprint.
- Documentation and runbooks deployed alongside feature, and analytics dashboards show modifier-driven valuations triggering as expected.
