# Listing Link Enrichment & Valuation Rule Completion – Worknotes

## Current Focus
- Migration `0015` renames `listing.url` to `listing_url`, adds `other_urls`, optional `ruleset_id`, and ruleset `priority`/`conditions_json`.
- SQLAlchemy models now expose the new fields; `ValuationRuleset` holds `priority`/`conditions_json` and a `listings` relationship.
- Pydantic `ListingBase` uses `listing_url` with a validation alias for legacy `url` payloads and surfaces `other_urls`/`ruleset_id`.
- Listings service normalizes payload keys via `_normalize_listing_payload` and includes new fields in `MUTABLE_LISTING_FIELDS`.
- Listings API schema advertises `listing_url`, `other_urls`, and `ruleset_id` as core editable fields.
- Ruleset requests/responses now surface `priority`, `conditions`, and `is_active`; service layer validates condition trees, accepts schema payloads, and orders listings by priority.
- Rule evaluation now honors static `ruleset_id`, matches active rulesets by priority/condition context, and falls back to highest-priority active set.
- Shared TypeScript listing types/API responses updated; listing tables/cards/dialogs consume `listing_url` in place of deprecated `url`.

## Follow-Ups
- Implement listing override endpoints + UI controls for per-listing enable/disable flows.
- Regenerate API/TS clients and add automated coverage for ruleset priority/condition handling.
- Expand frontend forms to manage `listing_url`/`other_urls` with validation and supplemental link presentation.
- Introduce recalculation workers + tests ensuring priority changes trigger listing updates.
