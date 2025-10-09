# Listing Link Enrichment & Valuation Rule Completion – Worknotes

## Current Focus
- Migration `0015` renames `listing.url` to `listing_url`, adds `other_urls`, optional `ruleset_id`, and ruleset `priority`/`conditions_json`.
- SQLAlchemy models now expose the new fields; `ValuationRuleset` holds `priority`/`conditions_json` and a `listings` relationship.
- Pydantic `ListingBase` uses `listing_url` with a validation alias for legacy `url` payloads and surfaces `other_urls`/`ruleset_id`.
- Listings service normalizes payload keys via `_normalize_listing_payload` and includes new fields in `MUTABLE_LISTING_FIELDS`.
- Listings API schema advertises `listing_url`, `other_urls`, and `ruleset_id` as core editable fields.
- Ruleset requests/responses now surface `priority`, `conditions`, and `is_active`; service layer validates condition trees, accepts schema payloads, and orders listings by priority.
- Rule evaluation now honors static `ruleset_id`, matches active rulesets by priority/condition context, and falls back to highest-priority active set.
- `apply_listing_metrics` now delegates to `RuleEvaluationService`, normalizes breakdown metadata (ruleset info, adjustments, legacy lines), and persists static override decisions with graceful fallback when no rulesets exist.
- Added valuation regression tests covering rule application, static overrides, and baseline fallbacks (`tests/test_listing_metrics.py`).
- `/v1/listings/{id}/valuation-breakdown` response schema upgraded for rule adjustments + legacy lines; frontend modal/detail views now render rule cards/table using shared TypeScript `ValuationBreakdown` types.
- Shared TypeScript listing types/API responses updated; listing tables/cards/dialogs consume `listing_url` in place of deprecated `url`.
- Added `/v1/listings/{id}/valuation-overrides` endpoint with service helpers for static assignments and per-listing disabled rulesets.
- Listing creation + quick edit flows now capture and validate `listing_url` and supplemental links; UI surfaces additional links in catalog detail views.

## Follow-Ups
- Regenerate API/TS clients (manual TS types updated; generator still pending) and add automated coverage for ruleset priority/condition handling (including override scenarios).
- Add valuation override UI (selector, disable toggles) and wiring to new endpoint.
- Introduce recalculation workers + tests ensuring priority changes trigger listing updates.
