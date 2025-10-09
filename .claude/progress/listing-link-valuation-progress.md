# Listing Link Enrichment & Valuation Rule Completion – Progress

**Start Date:** October 8, 2025  
**Status:** In Progress

## Backend Foundations (Week 1)
- [x] Create Alembic revision 0015 renaming `listing.url` → `listing_url`, adding `other_urls`, `ruleset_id`, and ruleset priority metadata.
- [x] Update SQLAlchemy models and Pydantic schemas for listings and rulesets, including legacy `url` alias handling.
- [x] Normalize listing service payloads and expose new core fields via the listings API schema.
- [x] Extend ruleset schemas/services with priority validation and condition metadata plumbed through API + service layers.
- [x] Build listing override endpoints to manage per-listing enable/disable flows.
- [ ] Regenerate API/TypeScript clients once schema changes stabilize and add backend tests for new fields. _(Backend tests landed Oct 9; client regeneration pending tooling refresh.)_

## Valuation Engine Integration (Week 2)
- [x] Wire `RuleEvaluationService` into listing metric calculations with static override support.
- [x] Implement background job for recalculating listings when rules change and cover with tests.

## Frontend Listing Experience (Week 3)
- [x] Update listing tables, cards, and detail surfaces to consume `listing_url` and refreshed schema types.
- [x] Expand listing forms to capture `listing_url`/`other_urls` with validation and display supplemental link UI.
- [ ] Implement ruleset selector and valuation tab with override controls.
- [ ] Introduce Basic/Advanced valuation mode toggle with shared persistence.

## QA & Launch Prep (Week 4)
- [ ] Expand automated test coverage (backend + frontend) for link validation, rule priority, and overrides.
- [ ] Update documentation and release notes for valuation workflow changes.
