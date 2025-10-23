# URL Ingestion - Follow-Up Work

**Status:** Phase 4 (Frontend & Testing) complete. Ready for next phase of development.

---

## Quick Wins (< 4 hours, high value)

### Install Frontend Dependencies
Add date-fns and @radix-ui/react-switch to `apps/web/package.json`.
These enable date formatting in import history and toggle UI for adapter settings.

**Related files:** `apps/web/package.json`

### Wire Import Dialog into Listings Page
Connect the ImportDialog component to the main listings page import button.
Provides end-to-end import flow from UI through API without switching views.

**Related files:** `apps/web/app/listings/page.tsx`, `apps/web/components/import/ImportDialog.tsx`

---

## Backend Completion (4-8 hours, required for full functionality)

### Implement Admin Adapters API Endpoints
Create `GET /api/v1/admin/adapters` (list all adapters with config schemas) and `PATCH /api/v1/admin/adapters/{id}` (update adapter settings like API keys).
Enables configuration UI to persist adapter-specific settings (credentials, rate limits, endpoints).

**Related files:** `apps/api/dealbrain_api/api/admin_routes.py` (new file)

### Add Adapter Metrics Aggregation Queries
Query adapter import success rates, average parse times, and failure patterns from `ImportJob` and `TaskRun` tables.
Provides observability into which adapters are most reliable and where to focus optimization efforts.

**Related files:** `apps/api/dealbrain_api/services/imports/` (add `metrics.py`)

---

## Future Enhancements (P1, medium priority)

### Amazon PA-API Adapter
Build adapter to fetch product details and pricing from Amazon Product Advertising API.
Unlocks Amazon listings as import source, largest e-commerce platform in target market.

**Effort:** Medium | **Impact:** High

### Generic Scraper Adapter
Create configurable web scraper adapter (BeautifulSoup + retry logic) for custom retailer URLs.
Allows rapid addition of new retailers without building individual adapters.

**Effort:** Medium | **Impact:** High

### Price History Tracking
Store historical prices in new `PriceHistory` table, aggregate to `Listing` model.
Enables price trend analysis and identifies rapid price changes indicating deals.

**Effort:** Small-Medium | **Impact:** Medium

### Browser Extension for One-Click Import
Build Chrome extension that intercepts product page visits and auto-submits URLs via the import API.
Streamlines UX for power users and drives import volume.

**Effort:** Large | **Impact:** Medium

---

## Recommended Next Steps

1. **Immediately:** Install frontend dependencies and wire import dialog (1-2 hours)
2. **This week:** Implement admin adapters endpoints (4-6 hours)
3. **Next phase:** Start Amazon PA-API adapter (highest impact P1)

