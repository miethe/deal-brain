# 2025-10-10 Valuation & Ruleset Remediation Plan

## Summary
- Resolve adjusted price not diverging from base price by verifying rule evaluation path and data mapping.
- Fix Celery task signature mismatch causing rule update failures.
- Add missing metric selector for `per_unit` actions in UI and validate server-side.
- Correct ruleset selector state persistence and layout issues.

## Scope
- Backend: task signature, rule evaluation flow, validation, minimal logging.
- Frontend: action builder UI, ruleset selector state + layout, summary formatting.
- Tests: regression for evaluation/delta, API validation, UI interaction.

## Work Items

### A. Adjusted Prices Not Changing
- Verify evaluation path in `apps/api/dealbrain_api/services/listings.py:185` uses `RuleEvaluationService` and persists `adjusted_price_usd` and `valuation_breakdown` when present.
- Add targeted debug logging for evaluation results (counts, total adjustment) behind existing logger to help diagnose empty summaries.
- Confirm ruleset resolution in `apps/api/dealbrain_api/services/rule_evaluation.py`:
  - Honor listing `ruleset_id` if active; otherwise match by context; finally fallback to first active ruleset.
  - Respect disabled rulesets via `attributes_json.valuation_disabled_rulesets`.
- Validate action payload mapping (ensure `value_usd`, `metric`, `unit_type` are deserialized and aligned to `RuleEvaluator` expectations).
- Add/extend test in `tests/test_listing_metrics.py` to assert a seeded listing with an active ruleset yields non-zero delta and applied rules in breakdown.

Deliverables:
- Logging tweak, no behavior change except correct persistence when evaluation returns data.
- One integration test asserting adjusted price differs and breakdown contains matched rules.

### B. Rule Update Crash (unexpected kwarg `reason`)
- Align task and enqueuer signatures in `apps/api/dealbrain_api/tasks/valuation.py`:
  - Update `recalculate_listings_task` to accept `reason: str | None = None`.
  - Pass through `reason` only to logging; do not affect behavior.
  - Ensure both `.delay(**payload)` and sync fallback `recalculate_listings_task(**payload)` accept the same payload.
- Add a lightweight test to simulate update path calling enqueue with `reason` to prevent regression.

Deliverables:
- Fixed task signature and consistent payload handling.
- Unit test for enqueue call compatibility.

### C. `per_unit` Action Requires Metric Selector (UI + API)
- UI: In `apps/web/components/valuation/action-builder.tsx`:
  - When `action_type === "per_unit"`, render a dropdown to select the metric (e.g., `ram_gb`, `storage_gb`, `cpu_cores`).
  - Populate options from existing field registry/helpers; store selection in `action.metric`.
  - Keep `value_usd` input for per-unit price.
- Display: Update formatting in `apps/web/components/valuation/ruleset-card.tsx` to show `$X per <metric>`.
- API: Validate in rule create/update that `metric` is present when `action_type === "per_unit"`; return a clear error otherwise.
- Tests: Add request test covering validation; extend `test_per_unit_action` to assert metric-based adjustment.

Deliverables:
- Action builder supports per-unit metric selection; payload includes `metric`.
- Server validation ensures correctness; UI shows metric in summaries.

### D. Ruleset Selector State + Layout
- State: In `apps/web/components/listings/listing-valuation-tab.tsx`:
  - After save, optimistically update `selectedRulesetId` and `disabledRulesets` from response or re-fetch rulesets to reflect persisted state.
  - Ensure disabled list sorts and dedupes consistently.
- Layout: Increase trigger container height/padding and ensure dropdown content doesn’t overlap the trigger (adjust container classes where selector is rendered in the same component).
- UX: Keep “Calculated using …” label in sync with active ruleset post-save.
- Tests: Add UI interaction test to toggle enabled state and save; verify persistence and no visual overlap.

Deliverables:
- Accurate state reflection post-save; no dropdown overlap.

## Validation
- Backend: run valuation and rule tests, plus the new enqueue signature test.
- Frontend: run unit/interaction tests for action-builder and ruleset selector.
- Manual: create a per-unit rule (RAM $5/GB), assign/apply, open listing breakdown; confirm adjusted price delta and applied rule appear.

## Risks & Mitigations
- Task signature drift: add test and centralize enqueue payload.
- Metric naming mismatch: align UI option values to server `RuleEvaluator` context keys; add a mapping helper if needed.
- UX regressions: cover with a focused interaction test and visual check in story or local.

## Rollout
- Merge fixes; trigger recalculation queue for active listings.
- Note in release: rule edits no longer error; valuations reflect active rules; per-unit rules configurable with metrics.

