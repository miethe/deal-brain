# Listing Link Enrichment & Valuation Rule Completion – Worknotes

## Current Focus
- Migration `0015` renames `listing.url` to `listing_url`, adds `other_urls`, optional `ruleset_id`, and ruleset `priority`/`conditions_json`.
- SQLAlchemy models now expose the new fields; `ValuationRuleset` holds `priority`/`conditions_json` and a `listings` relationship.
- Pydantic `ListingBase` uses `listing_url` with a validation alias for legacy `url` payloads and surfaces `other_urls`/`ruleset_id`.
- Listings service normalizes payload keys via `_normalize_listing_payload` and includes new fields in `MUTABLE_LISTING_FIELDS`.
- Listings API schema advertises `listing_url`, `other_urls`, and `ruleset_id` as core editable fields.

## Follow-Ups
- Update ruleset-facing schemas/services to leverage `priority` and `conditions_json`.
- Regenerate API/TS clients and adjust frontend consumers for `listing_url`/`other_urls`.
- Plan tests covering migration defaults, alias handling, and payload normalization.
