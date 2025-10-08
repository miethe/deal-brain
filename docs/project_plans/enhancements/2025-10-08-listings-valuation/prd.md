# PRD: Listing Link Enrichment & Valuation Rule Completion

## Overview
Deal Brain needs to close several gaps in the listings experience and valuation workflow identified in the 2025-10-08 enhancement request. Two themes drive this effort:
- Improve link management so every listing references its source marketplace cleanly and exposes supporting resources.
- Complete the intended "adjusted value" functionality so users can reason about CPU baseline value alongside rule-driven adjustments without digging through raw rule definitions.

The current backend model already exposes a single `url` column for listings (`apps/api/dealbrain_api/models/core.py:234`), but the UI lacks structured handling for additional URLs and graceful link presentation. Likewise, valuation rules exist but the listings service wires in an empty rule set (`apps/api/dealbrain_api/services/listings.py:48`), leaving adjusted prices stale and making the advanced rule authoring surface inaccessible to less technical users. This PRD establishes the product expectations to resolve these issues.

## Goals
- Provide a canonical `listing_url` for every listing, expose supplemental links, and render them consistently across catalog, modal, and detail views.
- Deliver an intuitive valuation workflow with Basic and Advanced modes that share the same rule engine while surfacing adjusted values wherever listings appear.
- Empower users to enable/disable rule groups, rule sets, and per-listing rule overrides without losing transparency into adjustment amounts.

## Non-Goals
- Building new marketplace integrations or automated scraping.
- Replacing the existing rule engine logic beyond what is required to wire it into listings and expose configuration controls.
- Redesigning dashboard analytics beyond necessary adjusted value visibility updates.

## Success Metrics
- ≥90% of listings created or edited in the first month after launch include a populated `listing_url`.
- 80% of valuation adjustments performed through the web app happen in Basic mode within two weeks (adoption indicator).
- Adjusted price values remain in sync with active valuation rules for 100% of listings during nightly audits (no divergence between stored adjusted price and rule evaluation).
- Support tickets related to “missing adjusted value” drop to zero within one sprint of release.

## Background & Current State
- Listings expose `url` as a generic string. Frontend components selectively render it but titles are not consistently clickable (`apps/web/app/listings/_components/master-detail-view/detail-panel.tsx:68`, `apps/web/components/listings/listing-details-dialog.tsx:75`).
- There is no facility for storing or displaying secondary links; users paste URLs into free-form notes.
- `apply_listing_metrics` never passes real rules to `compute_adjusted_price`, so adjusted values mirror list prices (`apps/api/dealbrain_api/services/listings.py:48`).
- Rule groups/sets cannot be toggled; only individual rules expose enable/disable affordances.
- No per-listing rule override screen exists; valuation adjustments are opaque on listing detail views.

## Scope
### In Scope
- Schema updates for `listing_url` (canonical source) and `other_urls` (list of supplemental links).
- Frontend UX for link entry, validation, display, and accessible labeling.
- Basic vs. Advanced valuation rule configuration, including toggle controls and shared persistence.
- Rule enable/disable propagation for groups, sets, and per-listing overrides with UI affordances in catalog modal/detail views.
- Ensuring adjusted values update immediately after listing edits and whenever active rules change.

### Out of Scope
- Bulk import/export format changes (will follow separately if needed).
- Automated detection of dead links or link previews.
- Mobile-native app parity (web-first).

## Target Users & Use Cases
- **Value hunters**: Need quick confirmation that a listing links back to its marketplace and see how component upgrades change value.
- **Power users / resellers**: Maintain nuanced rulesets, require fast toggling to model scenarios per listing.
- **Analysts**: Monitor adjusted valuations across catalog to identify high-value opportunities without manual recalculation.

## Functional Requirements
### FR1 – Listing Link Management
1. Introduce `listing_url` (string, required for new listings but optional for legacy records) and `other_urls` (array of objects `{url, label?}`) in the API schema.
2. Listing title renders as an external link when `listing_url` exists on catalog cards, dense table rows, modals, and detail pages. Links open in a new tab with `rel="noopener noreferrer"`.
3. Supplemental URLs render as a bullet list or tag list under a dedicated “Additional Links” section. Each entry auto-labels with the human-friendly host (e.g., `imgur.com`) using a trusted parsing utility; manual overrides remain editable.
4. Form validation enforces URL structure (HTTP/HTTPS) and prevents duplicates; UI communicates validation errors per field following the design guideline’s error state pattern.

### FR2 – Valuation Rule Modes
1. Valuation Rules page defaults to Basic mode with simplified inputs for RAM, Storage, and Condition adjustments. Options mirror existing listing enums to ensure parity.
2. Advanced mode exposes the current granular rule builder unchanged.
3. A toggle control persists the last used mode per user (local storage) and clarifies that both modes manipulate the same underlying ruleset.
4. Basic mode authors adjustments that persist into Advanced data structures without data loss; switching modes reflects existing configurations immediately.

### FR3 – Adjusted Value Propagation
1. Listing creation, edit, and import flows trigger application of the active ruleset so `adjusted_price_usd` and `valuation_breakdown` stay current.
2. Bulk rule changes (activating/deactivating groups/sets) enqueue background jobs to recalculate affected listings and surface progress in the UI.
3. Listings table, detail view, and dashboard widgets display both baseline (CPU-only) and adjusted values with tooltips explaining the delta.

### FR4 – Rule Enablement Controls
1. Rule sets and groups expose enable/disable toggles with clear status indicators; disabling cascades to contained rules for evaluation but maintains configuration.
2. Listing detail and modal screens add a “Valuation Rules” tab showing applicable rules, their contribution (positive/negative amount), and per-listing enable toggles.
3. Selecting a rule in the listing context opens a modal with rule metadata and edit CTA (subject to permissions).

### FR5 – Accessibility & Internationalization
1. All new interactive elements meet WCAG 2.1 AA contrast, focus, and keyboard navigation requirements per design guidance.
2. Link labels support localization (no hard-coded copy); currency displays respect existing locale settings.

## UX & Visual Requirements
- Follow shadcn-derived component patterns (button variants, tab panels) to maintain consistency.
- Auto-generated link labels use muted text with hover states aligning to `text-muted-foreground` styling.
- Tabs for “Details” and “Valuation Rules” in listing modals follow the primary/secondary tab hierarchy described in design guidance (active tab `font-semibold`, indicator underline).
- Empty states for “Additional Links” and “Valuation Rules” communicate next steps (“No additional links yet. Add one to share photos or documentation.”).

## Technical Considerations & Dependencies
- **Database**: Alembic migration must rename existing `url` column to `listing_url` and backfill values; add `other_urls` JSONB with default `[]`. Ensure indices remain performant for lookups.
- **API Models**: Update SQLAlchemy models, Pydantic schemas (`dealbrain_core/schemas`), and service layer update/patch allow-lists to cover new fields.
- **Frontend**: Update React Query hooks and TypeScript types generated for listings; ensure forms (create/edit) include dynamic URL field management with optimistic UI updates.
- **Rule Engine**: Integrate `RuleEvaluationService` into listing metric calculations to avoid duplicate logic while respecting caching strategy.
- **Background Jobs**: If recalculations could be long-running, leverage existing worker or schedule to avoid request timeouts.
- **Third-party Library**: Adopt a lightweight domain parsing helper (e.g., `tldts`) for link labeling; vet license compatibility.

## Data & Analytics
- Track events for `listing_link_opened`, `other_link_opened`, and `valuation_rule_toggled` with payload (listing_id, rule_id, context).
- Log recalculation jobs with duration and affected listing counts for observability dashboards.
- Add monitoring alert for discrepancies between stored `adjusted_price_usd` and on-the-fly evaluation > $1.

## Risks & Mitigations
- **Data Migration Risk**: Renaming `url` could break legacy clients. Mitigate by providing backward-compatible shadow field during transition and updating API contracts simultaneously.
- **Rule Consistency**: Simultaneous edits in Basic and Advanced modes may introduce race conditions. Mitigate with optimistic locking or timestamp checks.
- **Performance**: Per-listing rule previews could be heavy. Mitigate via batched queries and caching evaluation results.
- **Change Fatigue**: Users accustomed to Advanced-only view may be confused. Mitigate with inline education and gentle mode toggle messaging.

## Assumptions & Open Questions
- Assume there is a single “active” ruleset at any time; confirm whether per-profile rulesets must be supported in this iteration.
- Clarify audit requirements for tracking who toggled rules at listing level.
- Determine whether `other_urls` needs ordering guarantees or categories (default assumption: simple ordered list).

## Launch Checklist
- Schema migration applied and verified in staging with data backfill.
- Updated API and frontend deployed together to avoid contract mismatches.
- QA passes regression suite covering listing CRUD, valuation adjustments, and dashboard metrics.
- Documentation updated (user guide & internal runbooks).
