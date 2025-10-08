# Implementation Plan: Listing Link Enrichment & Valuation Rule Completion

## Milestones
- **M1 – Schema ready (Week 1)**: Alembic migration merged, API and domain models compile with new fields, legacy data backfilled.
- **M2 – Backend valuation wiring (Week 2)**: Adjusted prices recomputed via active ruleset, background recalculation path validated.
- **M3 – Frontend UX (Week 3)**: Listing link management UI shipped across catalog views; Basic/Advanced valuation toggle feature-complete.
- **M4 – Per-listing overrides & release prep (Week 4)**: Valuation Rules tab in listing modal/detail live, QA signed off, documentation updated.

## Workstream 1 – Data Model & Migration
1. Create Alembic revision under `apps/api/alembic/versions/`:
   - Rename `listing.url` → `listing_url` using `op.alter_column`.
   - Add `other_urls` JSONB column with default `[]`.
   - Backfill historical rows by copying `url` values into `listing_url`.
2. Update ORM model (`apps/api/dealbrain_api/models/core.py:234`) to rename field and include `other_urls: Mapped[list[dict[str, str]]]`.
3. Adjust `MUTABLE_LISTING_FIELDS` in `apps/api/dealbrain_api/services/listings.py:18` to include new keys.
4. Update Pydantic schemas in `packages/core/dealbrain_core/schemas` (e.g., `listings.py` if present) so `ListingCreate`, `ListingRead` expose `listing_url` and `other_urls`.
5. Regenerate OpenAPI spec (if auto-generated) and TypeScript client types, ensuring the web app picks up schema changes.
6. Provide migration fallback for legacy clients: optionally allow payloads containing `url` for one deploy cycle by accepting aliases in Pydantic model (`Field(alias="url")`) and logging usage.

## Workstream 2 – Backend API & Services
1. Update create/update endpoints (`apps/api/dealbrain_api/api/listings.py`) to accept new fields; ensure `payload.model_dump()` includes them.
2. Extend `sync_listing_components` if supplemental links map to components or notes (no change expected but confirm).
3. Introduce validation helpers (e.g., `validate_external_urls`) in `apps/api/dealbrain_api/services/listings.py` to normalize URLs, strip whitespace, and deduplicate.
4. Update serializers in `apps/api/dealbrain_api/api/schemas/listings.py` (response models) to include new fields with documentation strings.
5. Adjust dashboard queries (e.g., `apps/api/dealbrain_api/api/dashboard.py`) if they display links or need adjusted price recalculations.

## Workstream 3 – Rule Engine Integration
1. Refactor `apply_listing_metrics` to fetch the active ruleset via `RuleEvaluationService` instead of the placeholder rule list:
   - Inject service dependency or utility function fetching cached rules.
   - Reuse `evaluate_listing` to obtain adjustment summary; update `valuation_breakdown` to include base vs. adjustments.
2. Ensure bulk operations (`bulk_update_listing_metrics`, `bulk_update_listings`) reuse the same evaluation path.
3. Implement background job trigger (Celery worker in `apps/api/dealbrain_api/services/rule_evaluation.py`) that recalculates listings when rule sets/groups toggle, respecting batch size.
4. Add regression tests covering recalculation and verifying `adjusted_price_usd` persistence.

## Workstream 4 – Frontend Listing Experience
1. Update shared listing types (likely in `packages/js-ui` or generated client) to use `listing_url` and `other_urls`.
2. Extend listing create/edit forms (check `apps/web/app/listings` form components) to:
   - Render primary URL input with validation feedback.
   - Provide dynamic chip/field list for `other_urls` (add/remove).
3. Update catalog components:
   - Dense table (`apps/web/app/listings/_components/dense-list-view/dense-table.tsx`) to wrap titles with anchor tags when `listing_url` exists.
   - Detail panel (`apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`) and card view to render Additional Links section; adopt accessible markup (`<ul><li>`).
4. Ensure global badge/button styles follow design guidance; add tooltip for hostnames if truncated.
5. Instrument click analytics (likely via existing telemetry hook) for link events.

## Workstream 5 – Valuation UX Enhancements
1. Build Basic valuation mode UI (new component under `apps/web/components/valuation/basic-form.tsx` or similar):
   - Dropdowns for RAM/Storage/Condition sourcing options from enums; numeric inputs for adjustments.
   - Map to existing rule model by generating structured payload before saving.
2. Implement mode toggle (persisted via local storage or user settings service) with contextual messaging.
3. Extend Advanced mode to reflect Basic edits; ensure diff view handles both.
4. Add enable/disable toggles to Rule Sets and Rule Groups in `apps/web/components/valuation` using accessible toggle components.
5. Surface per-listing overrides inside listing dialog:
   - Add `Tabs` component with “Details” and “Valuation Rules” (update `apps/web/components/listings/listing-details-dialog.tsx` and `apps/web/components/listings/listings-table.tsx` modal triggers).
   - Display rule list with toggle switches, adjustment amount chips, and edit CTA.
6. Wire frontend actions to new API endpoints (may require additional routes for toggling rules and listing overrides).

## Workstream 6 – Testing, Analytics, Documentation
1. Backend: add unit tests for URL validation, migration smoke tests, rule evaluation integration tests (`apps/api/tests/`).
2. Frontend: extend Vitest/Playwright coverage for link rendering, mode toggling, and per-listing controls.
3. Performance test recalculation workflow with realistic data volume to ensure batch jobs finish within SLA.
4. Update runbooks and user docs describing new valuation flow and link management.
5. Configure observability dashboards to track recalculation success metrics and link click analytics.

## Testing Strategy
- **Unit Tests**: Schema validation, rule evaluation integration, React component behavior.
- **Integration Tests**: End-to-end listing CRUD with valuation recalculation (API + DB).
- **UI Regression**: Visual diff on catalog and listing modal to catch layout regressions.
- **Migration Verification**: Pre/post-migration SQL snapshot verifying `listing_url` populated and no data loss.
- **Accessibility Audit**: Keyboard navigation and screen reader checks for new tabs/toggles.

## Rollout & Communication
1. Deploy backend first behind feature flags (accepting new fields while continuing to serve legacy responses), then ship frontend toggling on the flag.
2. Run full catalog recalculation in staging, compare adjusted values to expected baselines, then schedule production recalculation off-peak.
3. Announce changes in release notes with short Loom walkthrough for valuation modes.
4. Monitor error logs and analytics dashboards for 48 hours post-release; fast-follow fixes as needed.

## Dependencies & Resources
- Coordination with data team for migration scheduling.
- Access to design system resources for toggle and tab patterns.
- Potential need for Celery worker capacity review if recalculation load increases.
