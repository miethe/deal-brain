# PRD: RAM & Storage Valuation Modernization

## Overview
Deal Brain now persists normalized RAM specifications and storage profiles at the database level (`apps/api/alembic/versions/0017_ram_and_storage_profiles.py:55`). Listings reference these entities and expose derived `ram_type` and `ram_speed_mhz` in the API surface (`apps/api/dealbrain_api/models/core.py:307`, `apps/api/dealbrain_api/api/listings.py:92`). The valuation context builder also hydrates RAM and storage objects for rule execution (`packages/core/dealbrain_core/rules/evaluator.py:262`). However, catalog management and valuation tooling still behave as if RAM and storage are flat text fields—listing creation relies on freeform inputs (`apps/web/components/listings/add-listing-form.tsx:626`), importer utilities never classify components, and rule builders lack RAM/Storage-aware predicates. This PRD aligns product expectations around the new component catalog so valuation analysts can price listings by spec while operations teams maintain clean inventories.

## Goals
- Provide a curated RAM and storage catalog that backs every listing, importer, and rule evaluation.
- Deliver guided listing and valuation UX that makes spec selection faster than manual entry while keeping advanced overrides available.
- Enable analysts to author pricing logic that targets RAM type, speed, capacity, and storage characteristics without manual JSON.
- Instrument adoption so we can confirm catalog usage and price accuracy improvements.

## Non-Goals
- Automating third-party scraping or sourcing for catalog entries (handled by existing ingest workflows).
- Replacing the valuation engine; changes are limited to context enrichment, metrics, and rule authoring affordances.
- Supporting mobile-native clients during this iteration.

## Success Metrics
- ≥95 % of active listings carry a linked `ram_spec` **and** primary storage profile within two weeks of rollout (checked via nightly audit).
- ≥80 % of new listings select catalog-backed RAM/storage options instead of falling back to free text within the first sprint.
- Valuation rule adjustments exhibit ≤1 % deviation between expected and stored adjusted prices across DDR5 vs. DDR4 and NVMe vs. HDD regression suites.
- Telemetry shows at least one valuation rule per active ruleset using RAM or storage predicates within the first month.

## Background & Current State
- Schema: Alembic revision `0017` introduces `ram_spec` and `storage_profile` tables and backfills legacy records (`apps/api/alembic/versions/0017_ram_and_storage_profiles.py:55`). Listings now store foreign keys plus derived accessors (`apps/api/dealbrain_api/models/core.py:321`).
- API surface: Core listing schema exposes spec/profile IDs and flattened fields so builders can query without joins (`apps/api/dealbrain_api/api/listings.py:82`). FieldRegistry serializes new fields to consumers (`apps/api/dealbrain_api/services/field_registry.py:301`).
- Valuation context: The rule evaluator publishes structured RAM/storage data and adds per-unit metric aliases (`packages/core/dealbrain_core/rules/evaluator.py:262`, `apps/web/lib/valuation-metrics.ts:8`).
- UX gaps: Listing creation/edit flows still rely on free-text inputs and datalists for RAM/storage, offering no visibility into catalog entries (`apps/web/components/listings/add-listing-form.tsx:626`). The listings table provides simple dropdowns but without spec metadata or guidance for dual-drive setups (`apps/web/components/listings/listings-table.tsx:970`).
- Operations: Importers and seed utilities ignore the new tables—classification logic, deduping, and seeding are still pending (`apps/api/dealbrain_api/seeds.py:19`, `apps/api/dealbrain_api/importers/universal.py`).

## Target Users & Use Cases
- **Valuation analysts** need to tune pricing based on RAM type, speed, and storage tiers without writing custom expressions each time.
- **Sourcing managers** must ingest vendor catalogs quickly, ensuring inventories share consistent component metadata for cross-listing comparisons.
- **Ops coordinators** require visibility into RAM/storage configurations across the catalog to confirm upgrade opportunities and highlight anomalies.

## User Experience Requirements
- **Catalog management**
  - Maintain an admin-accessible catalog view for RAM specs and storage profiles with search, dedupe suggestions, and merge capability to avoid fragmenting the dataset.
  - Support bulk seeding/import via importer workflows; show classification summaries (matched vs. new vs. ambiguous).
- **Listing creation & edit**
  - Offer type-ahead selectors for RAM spec and storage profiles showing type, speed, capacity, and interface details.
  - Provide guardrails for dual-drive listings (primary/secondary) with logical defaults and validation to prevent contradictory combinations (e.g., same profile reused for both positions unless explicitly allowed).
  - Allow fallbacks to ad-hoc specs but require justification/comment and flag them for later catalog promotion.
- **Valuation rule authoring**
  - Present RAM and storage predicates in the condition builder with friendly labels (generation, speed range, capacity bands, medium, performance tier).
  - Extend per-unit metric pickers to include contextual options (primary vs. secondary storage) with tooltips explaining data provenance.
  - Allow compound modifiers (fixed + per-unit + multiplier) on RAM/storage attributes and preview resulting adjustments.
- **Catalog browsing & analytics**
  - Display structured RAM/storage summaries wherever listings appear (cards, detail drawers, valuation modals) using consistent chip/badge styles.
  - Add dashboards or reports highlighting top RAM/storage configurations, adoption trends, and valuation adjustments triggered by spec differences.

## Functional Requirements
1. **Data normalization**
   - Expand RAM spec schema to capture module layout and JEDEC/XMP indicators; ensure storage profiles map medium, interface, form factor, and performance tier.
   - Provide deduplication heuristics and tooling to merge overlapping specs/profiles without data loss.
2. **Importer & seeding updates**
   - Update spreadsheet/import pipelines to classify RAM/storage attributes, creating or linking catalog entries; surface conflicts requiring human review.
   - Cache catalog lookups during batch imports for performance.
3. **Service behavior**
   - Enforce consistent catalog linkage on listing create/update, emitting structured errors when payloads conflict with catalog constraints.
   - Trigger valuation recalculation whenever RAM or storage linkage changes, including bulk actions.
4. **Valuation engine**
   - Support RAM/storage-specific condition types, per-unit metrics, and modifier actions; guarantee backwards compatibility for legacy rules.
   - Ensure evaluation summaries include RAM/storage context for transparency.
5. **Frontend UX**
   - Deliver reusable selectors/comboboxes for RAM specs and storage profiles with inline creation that flows through backend upsert helpers.
   - Surface validation errors and fallback warnings inline, with escalation to catalog management when freeform values are used.
6. **Telemetry & operations**
   - Instrument listing edits, rule modifications, and importer runs to capture catalog adoption.
   - Provide runbooks covering catalog seeding, backfill verification, and rollback strategies.

## Non-Functional Requirements
- Maintain listing create/update latency under 400 ms at P95 despite catalog lookups (cache and index hot paths).
- Keep importer reclassification throughput at ≥500 listings per minute with batched catalog resolution.
- Ensure all new UI components meet WCAG AA contrast and keyboard accessibility.
- Extend automated test suites across backend unit/integration and frontend component flows; include scenario coverage for DDR generation combinations and dual-drive setups.

## Rollout & Telemetry
- Deploy immediately without migration or rollouts, as the app is in active development.
