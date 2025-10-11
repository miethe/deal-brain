# Implementation Plan: RAM & Storage Valuation Modernization

## Milestones
- **M1 – Catalog foundation (Week 1)**: Expand RAM/storage schemas, seed baseline catalog, update importer + seed utilities, ship admin tooling for review.
- **M2 – Service & valuation wiring (Week 2)**: Harden listing payload normalization, extend valuation actions/conditions, and guarantee recalculation coverage.
- **M3 – Frontend UX rollout (Week 3)**: Deliver guided selectors across listing CRUD, valuation rule builder enhancements, and catalog-aware display components.
- **M4 – Telemetry (Week 4)**: Land analytics, QA matrix

## Workstream 1 – Data Model & Catalog Enrichment
1. **Schema refinements (deferred)**
   - Per latest guidance we will not introduce new migrations. Focus on leveraging existing `ram_spec` and `storage_profile` columns, adding derived metadata within attributes JSON where needed.
   - Ensure ORM defaults and query helpers expose the existing fields efficiently (indexes already cover FK lookups).
2. **Seeder support**
   - Extend seed utilities to bootstrap canonical specs/profiles (desktop, workstation, server sets). Update `apps/api/dealbrain_api/seeds.py:19` to read JSON fixtures and insert via ORM with conflict handling.
3. **Importer updates**
   - Implement classification helpers in `apps/api/dealbrain_api/importers/universal.py` to normalize vendor-provided RAM/storage fields and reuse catalog entries; cache resolved IDs to minimize DB chatter.
   - Emit structured import summary (matched/new/failed) for monitoring.
4. **Admin catalog tooling**
   - Build FastAPI endpoints for catalog listing/search/merge; expose via new routes under `/v1/reference/ram-specs` and `/v1/reference/storage-profiles`.
   - Provide bulk merge operation with conflict safeguards (no deletion while referenced).

## Workstream 2 – Services & Valuation Engine
1. **Listing payload enforcement**
   - Expand `_normalize_ram_spec_payload` and `_normalize_storage_profile_payload` to require catalog linkage when sufficient hints exist, emitting actionable errors otherwise (`apps/api/dealbrain_api/services/listings.py:360`).
   - Add audit logging when freeform specs are created to flag for review.
2. **Recalculation triggers**
   - Update `apply_listing_metrics` to trigger Celery recalculation whenever RAM/storage foreign keys change; ensure job deduplicates by listing ID (`apps/api/dealbrain_api/tasks/valuation.py:68`).
3. **Rule condition & action support**
   - Extend rule schema builders so conditions support range queries on `ram_spec.speed_mhz`, `ram_spec.total_capacity_gb`, and storage medium/performance tiers; add multipliers for RAM generation uplifts (`packages/core/dealbrain_core/rules/actions.py:109`).
   - Update API validators to prevent incompatible metric/action pairings.
4. **Legacy compatibility**
   - Analyze existing seed scripts and related seed data to support any new fields or similar.

## Workstream 3 – Frontend UX Enhancements
1. **Shared selectors**
   - Build `RamSpecSelector` and `StorageProfileSelector` components with async search, badges for spec attributes, and inline “promote ad-hoc spec” flow (`apps/web/components/forms/`).
   - Integrate into `add-listing-form` (`apps/web/components/listings/add-listing-form.tsx:626`) and inline editing table (`apps/web/components/listings/listings-table.tsx:970`), replacing plain inputs/datalists.
2. **Dual-drive guidance**
   - Update listing detail surfaces to render both storage profiles with icons, capacity, and interface. Warn when secondary drive absent but rules expect it.
3. **Valuation rule builder**
   - Add RAM/storage condition groups, metric pickers, and modifier stacks inside `apps/web/components/valuation/rule-builder-modal.tsx`. Provide live preview using per-unit metric helper (`apps/web/lib/valuation-metrics.ts:8`).
   - Surface validation messages when predicates require catalog linkage that the listing lacks.
4. **Catalog admin UI**
   - Create dedicated table views under `/app/catalog/components` that mirror backend admin endpoints, including merge, archive, and analytics charts (adoption, duplicates).

## Workstream 4 – Telemetry, QA, and Ops
1. **Telemetry instrumentation**
   - Emit events for catalog selection, ad-hoc spec creation, rule saves with RAM/storage conditions, and importer classification results. Wire into existing analytics service or capture via PostHog instrumentation.
2. **QA matrix**
   - Define regression suite covering DDR4 vs DDR5 pricing, mixed NVMe/HDD dual-drive listings, importer fallback scenarios, and UI accessibility checks. Automate via pytest + Playwright.
3. **Docs**
   - Update product docs to describe new workflow.

## Testing Strategy
- **Backend**
  - Unit tests for normalization helpers (RAM/storage), import classification, and rule evaluation permutations (with spec-based modifiers).
  - Integration tests covering listing create/update with catalog linkage, recalculation triggers, and Celery task execution.
- **Frontend**
  - Component tests for selectors (search, inline creation, validation), valuation builder updates, and listing forms.
  - Playwright flows: create listing with dual drives, edit listing to swap storage profile, author valuation rule referencing RAM speed, confirm adjusted price updates.
- **Performance**
  - Benchmark importer batch runs (≥500 listings) and listing update throughput under catalog lookups.
- **Accessibility**
  - Axe audits on new selectors and catalog admin views; manual keyboard traversal.

## Release Plan
1. Merge schema migration and run seeds in staging; verify data matches acceptance thresholds.
2. Run importer dry run and reconcile catalog diffs.
3. Roll out frontend selectors.
4. Archive deprecated freeform fields and clean up audit backlog of ad-hoc specs.

## Risks & Mitigations
- **Catalog drift**: Without governance, duplicate specs could reappear. Mitigate with merge tooling, nightly dedupe jobs, and alerts when ad-hoc specs exceed threshold.
- **Importer latency**: Classification could slow ingest. Mitigate with cached lookups and batched DB queries; monitor metrics with alerts on throughput drops.
- **User learning curve**: New selectors may overwhelm casual users. Provide inline education, sensible defaults, and escape hatch for freeform entry with follow-up review.
