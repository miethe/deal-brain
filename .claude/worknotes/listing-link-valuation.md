# Listing Link Enrichment & Valuation Rule Completion – Worknotes

## Current Focus
- Schema and API layers now expose `listing_url`, `other_urls`, optional `ruleset_id`, and ruleset `priority`/`conditions_json`; service payload normalisation keeps legacy `url` aliases working.
- Rule evaluation path relies on `RuleEvaluationService`, supports static overrides, records detailed breakdowns, and triggers background recalculation tasks on ruleset mutations.
- Listing detail dialog introduces a Valuation tab with per-listing override controls (auto vs. static, disabled rulesets) wired to `/v1/listings/{id}/valuation-overrides` and live breakdown modal access.
- Valuation Rules page defaults to a persisted Basic mode; the new Basic form writes to a generated “Basic · Adjustments” rule group via create/update APIs while Advanced mode remains available through a segmented toggle.
- Shared condition builder adds inline NOT toggles by swapping between paired operators (`equals`⇆`not_equals`, `in`⇆`not_in`, etc.), keeping rule and ruleset editors aligned.

## Follow-Ups
- Regenerate API/TS clients (manual TS updates done) and extend automated coverage for overrides + Basic mode flows.
- Add ruleset/rule-group enable/disable toggles and surface priority badges across selectors.
- Wire recalculation telemetry/monitoring and expose admin affordances to view job status.
