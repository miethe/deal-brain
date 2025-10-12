# Implementation Plan — Basic Valuation Enhancements

## Alignment & Assumptions
- The valuation runtime already evaluates rulesets in priority order; we will enforce `System: Baseline → Basic · Adjustments → Advanced` solely by adjusting ruleset and group priorities plus metadata tagging (no forked evaluator). `ValuationRuleset.metadata_json` and `ValuationRuleV2.metadata_json` exist today; we must add a `metadata_json` column to `ValuationRuleGroup` to carry `basic_managed`, `entity_key`, and ordering hints.
- Existing services (`RulesService`, `RulePreviewService`, `RulesetPackagingService`) support CRUD, preview, and packaging for versioned rulesets; we will extend them rather than introduce a parallel ingestion path.
- Current Basic editor (`apps/web/components/valuation/basic-valuation-form.tsx`) only manages a handful of additive rules. It will be replaced with an entity-driven baseline view that writes to a managed rule group while leaving the Advanced UI untouched.
- `data/deal_brain_valuation_rules.json` is the authoritative source for baseline ranges/formulas. Import tooling must treat it as versioned content with hash-based idempotency.

## Workstreams

### 1. Data Modeling & Baseline Ingestion
- Add Alembic migration introducing `valuation_rule_group.metadata_json` (JSONB default `{}`) and indexes to query `metadata_json->>'entity_key'`. Backfill existing groups with `{}`.
- Define a baseline ingestion service (`BaselineLoaderService`) that maps JSON entities to domain models:
  - Resolve or create the `System: Baseline v{X.Y}` ruleset with `metadata_json` flags (`system_baseline`, `source_version`, `source_hash`, `read_only`).
  - For each entity block, create/read rule groups tagged with `entity_key` and `basic_read_only=true`; populate rules using existing action/condition builders, storing clamp ranges and explanations in `ValuationRuleAction.modifiers_json`.
  - Provision or update the sibling writable `Basic · Adjustments` group under the active customer ruleset, tagging it `basic_managed=true` and mirroring entity keys via child metadata for lookup.
- Package ingestion behind both a Celery task and CLI (`python -m dealbrain_api.cli baselines load <path>`) to satisfy FR-1 and enable ops automation. Ensure idempotency by comparing stored `source_hash`.

### 2. Evaluation Precedence & Runtime Integration
- Extend ruleset selection logic (likely in `RuleEvaluationService`) to always include the latest `System: Baseline` ruleset ahead of customer rulesets, honoring `is_active` and `priority`. Persist precedence decisions in metadata so evaluators only read configuration.
- Update packaging/import workflows to keep baseline rulesets separate: exporting ignores `system_baseline=true` unless explicitly requested; installing a baseline package creates a new version rather than mutating the active one.
- Ensure recalculation pathways (`enqueue_listing_recalculation`) fire when baseline versions change or when `Basic · Adjustments` updates occur.

### 3. API Surface for Baseline Management
- Introduce FastAPI router (`apps/api/dealbrain_api/routes/baseline.py`) with:
  - `GET /api/v1/baseline/meta` returning entity/field descriptors sourced from rules metadata (or a `baseline_catalog` view if caching is required).
  - `POST /api/v1/baseline/instantiate` invoking the ingestion task idempotently.
  - `POST /api/v1/baseline/diff` comparing uploaded JSON against stored baseline rules to produce added/changed/removed entries (rule-level granularity with min/max/formula deltas).
  - `POST /api/v1/baseline/adopt` triggering creation of a new versioned ruleset and updating active baseline pointers; record actor and diff summary in audit logs.
- Extend existing Rules CRUD schemas to expose `basic_managed`, `entity_key`, and `modifiers_json` so the Basic UI can read/write overrides safely.
- Wire API auth guards: reuse RBAC utilities to enforce `baseline:admin` for diff/adopt, `rules:write_basic` for adjustments, and read-only access for analysts.

### 4. Basic Mode UX
- Replace `BasicValuationForm` with a tabbed entity layout that consumes `baseline/meta` data and `RulesService` payloads:
  - For each entity tab, render read-only baseline ranges/formulas with rich explanations (tooltips, badges) and editable override controls reflecting the rule type (scalar, toggle, coefficient).
  - Maintain override state per field keyed by rule metadata; persist via batch update API that writes rules into the `Basic · Adjustments` group (creating or deleting rules as deltas become zero).
  - Implement “Reset to Baseline” per field and per entity by issuing delete/disable requests on matching override rules.
- Build `Preview Impact` panel using `RulePreviewService` on the last N listings; surface match rate and valuation delta compared to baseline-only evaluation, updating asynchronously to keep the UI responsive.
- Partner with design to align typography, empty states, and delta badges with the navigation shell delivered in Phase 7 (see `.claude/progress/ui-enhancements-context.md`).

### 5. Diff & Adopt Workflow
- Create admin-only flow accessible from Basic mode:
  - Upload step validates schema version and displays metadata (source, generated_at).
  - Diff step surfaces entity/field changes with collapsible rows comparing baseline vs. candidate ranges/formulas.
  - Adoption step issues `baseline/adopt`, then prompts optional recalculation kickoff; log actions via audit trail service.
- Persist prior baseline versions and allow users to inspect previous diffs; provide rollback by re-activating older baseline rulesets.

### 6. Telemetry, Observability & Ops
- Emit structured events (`valuation.layer_contribution`) during evaluation by annotating the breakdown generator; include layer, rule IDs, and delta USD. Aggregate metrics for percentage of listings touched by each layer and top contributing rules.
- Instrument API endpoints with audit entries capturing actor, payload hash, and resulting version IDs.
- Add health checks to ensure a baseline ruleset is present; surface warnings in the admin UI if baseline metadata is stale or hash mismatch occurs.

## Testing & Rollout
- Expand unit coverage for ingestion mapping (JSON fixtures → rules) and diff/adopt logic. Include regression tests ensuring idempotency when the same baseline file is applied twice.
- Add integration tests exercising evaluation precedence: baseline-only vs. baseline+basic vs. full stack.
- Implement frontend Cypress or Playwright smoke flows: load Basic tab, apply overrides, preview impact, reset, and run Diff & Adopt happy path.
- Stage rollout by importing baseline to a pre-prod environment, capturing evaluation metrics, then enable the Basic UI flag gating access. Provide fallback plan to disable Basic mode while keeping baseline read-only layer active.

## Risks & Mitigations
- **Schema drift**: keep migrations reversible and ensure API clients tolerate missing metadata by defaulting to empty objects.
- **Override confusion**: emphasise deltas and layer origin in both Basic UI and breakdown modal; document precedence in user guide updates.
- **Performance regression**: monitor evaluator latency post-baseline import; cache baseline metadata for Basic UI to avoid large payloads on every load.
