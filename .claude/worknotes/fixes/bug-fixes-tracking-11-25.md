# Bug Fixes Tracking

## 2025-11-01: FastAPI DELETE Endpoint 204 Response Body Issue

**Issue**: API failed to start with `AssertionError: Status code 204 must not have a response body`

**Location**: `apps/api/dealbrain_api/api/listings.py:351`

**Root Cause**: DELETE endpoint decorated with `status_code=status.HTTP_204_NO_CONTENT` without explicitly setting `response_model=None`. FastAPI's newer versions are stricter about HTTP 204 semantics - this status code must not have a response body.

**Fix**: Added `response_model=None` parameter to the `@router.delete()` decorator.

**Code Change**:
```python
# Before
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)

# After
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
```

**Testing**: Verified fix by rebuilding Docker container and confirming API starts successfully with no errors.

**Commit**: 0e1cf35

## 2025-11-02: Celery AsyncIO Event Loop Conflict

**Issue**: Celery task `admin.recalculate_cpu_mark_metrics` failing with `RuntimeError: Task got Future attached to a different loop`

**Location**: `apps/api/dealbrain_api/tasks/admin.py` and `apps/api/dealbrain_api/tasks/baseline.py`

**Root Cause**: Tasks used `asyncio.run()` which creates implicit event loops. In Celery forked workers with global SQLAlchemy async engine state, the cached engine remains attached to old event loops, causing conflicts when new event loops are created.

**Fix**: Replaced `asyncio.run()` with explicit event loop management pattern:
1. Create fresh event loop with `asyncio.new_event_loop()`
2. Call `dispose_engine()` to reset cached SQLAlchemy engine
3. Execute async function with `loop.run_until_complete()`
4. Proper cleanup in finally block (shutdown async generators, close loop, clear context)

**Files Modified**:
- `apps/api/dealbrain_api/tasks/admin.py` - Fixed 4 tasks (recalculate_metrics, recalculate_cpu_mark_metrics, import_passmark, import_entities)
- `apps/api/dealbrain_api/tasks/baseline.py` - Fixed 1 task (load_ruleset)

**Pattern Used**: Followed working pattern from `apps/api/dealbrain_api/tasks/valuation.py:145-169`

**Testing**: Worker restarted successfully with fixed code, no event loop errors in logs

**Commit**: 8f93897

## 2025-11-03: Delete Button Enhancements and UI Fixes

### Issue 1: Missing Delete Buttons

**Issue**: Delete button was only on detail page, missing from listing cards and overview modal

**Locations**:
- `apps/web/app/listings/_components/grid-view/listing-card.tsx`
- `apps/web/components/listings/listing-overview-modal.tsx`

**Fix**: Added Delete button to both components:
- ListingCard: Top-right corner, visible on hover with ghost variant
- ListingOverviewModal: Next to "View Full Listing" button with destructive variant
- Both use ConfirmationDialog, React Query mutations, and toast notifications
- Proper error handling and query invalidation

**Commit**: 4fd0263

### Issue 2: DELETE Endpoint Path Incorrect

**Issue**: DELETE requests failing with "Not Found" error on detail page

**Location**: `apps/web/components/listings/detail-page-layout.tsx` and `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`

**Root Cause**: Frontend using `/api/v1/listings/${id}` but backend router at `/v1/listings` (without `/api` prefix)

**Fix**: Removed `/api` prefix from DELETE fetch URLs in both components

**Commit**: 7bf9c52

### Issue 3: Nested Anchor Tag Warning

**Issue**: React DOM warning about nested `<a>` tags in clickable containers

**Location**: EntityTooltip rendering EntityLink inside clickable ListingCard and modal

**Root Cause**: EntityLink uses Next.js Link (renders as `<a>`), creating nested anchors when used in clickable containers

**Fix**: Implemented `disableLink` prop pattern:
- Added `disableLink?: boolean` prop to EntityLink and EntityTooltip
- When true, renders as `<span>` instead of `<Link>`
- Applied `disableLink={true}` to all EntityTooltip instances in ListingCard and ListingOverviewModal
- Maintains visual consistency while preventing invalid HTML

**Commit**: 4fd0263

## 2025-11-07: Amazon URL Ingestion Failure - Missing Product Data Extraction

**Issue**: Amazon product URLs failing with `NO_STRUCTURED_DATA` error during URL ingestion

**Location**: `apps/api/dealbrain_api/adapters/jsonld.py`

**Root Cause**: Amazon doesn't use Schema.org structured data (JSON-LD) or OpenGraph price meta tags. Instead, Amazon uses HTML element selectors for product data:
- Price: `span.a-price > span.a-offscreen`
- Title: `span#productTitle`
- Images: Standard `<img>` tags with data attributes

The JsonLdAdapter only attempted Schema.org and meta tag extraction, failing on Amazon's HTML structure.

**Fix**: Implemented three-tier fallback extraction strategy in JsonLdAdapter:
1. **Primary**: Schema.org structured data (JSON-LD, Microdata, RDFa) - existing
2. **Fallback 1**: Meta tags (OpenGraph, Twitter Card) - previously added
3. **Fallback 2**: HTML elements (Amazon-style direct parsing) - **NEW**

**Implementation Details**:
- Added `_extract_from_html_elements()` method with Amazon-specific selectors
- Title extraction: `#productTitle`, `.product-title`, `itemprop="name"`, or first `<h1>`
- Price extraction: `.a-price > .a-offscreen` (Amazon), `.price`, `itemprop="price"`
- Image extraction: `data-old-hires`, `data-a-image-source`, or `src` (skips 1x1 tracking pixels)
- Spec extraction: Reuses existing `_extract_specs()` on title + description
- Enhanced debug logging to troubleshoot extraction failures

**Testing**:
- Added 14 comprehensive test cases for HTML element fallback
- All 90 JsonLdAdapter tests passing
- No regressions in existing Schema.org or meta tag extraction

**Files Modified**:
- `apps/api/dealbrain_api/adapters/jsonld.py` - Added HTML element parsing + debug logging
- `tests/test_jsonld_adapter.py` - Added `TestJsonLdAdapterHtmlElementFallback` test class

**Notes**: Amazon has aggressive bot detection that may still block requests. The HTML element fallback addresses the data format issue, but bot blocking is a separate concern that may require:
- Better User-Agent rotation
- Request rate limiting
- Residential proxies
- CAPTCHA handling
- Or using Amazon Product Advertising API for legitimate access

**Commits**: 10d44fa (meta tag fallback), ae1b735 (HTML element fallback + debug logging)

## 2025-11-07: False Success Toast on Import Failures

**Issue**: Frontend showed "Import successful!" toast even when imports failed (e.g., Amazon URLs with extraction failures)

**Location**: `apps/web/components/ingestion/single-url-import-form.tsx`

**Root Cause**: Success condition only checked `jobData.status === 'complete' && jobData.result` without validating that `listing_id` was actually created. Backend can return `status: 'complete'` with `listing_id: null` in some error scenarios.

**Fix**: Enhanced validation and added error handlers:

1. **Success Validation** (Line 104-110):
   - Added checks for `listing_id !== null`, `!== undefined`, and `> 0`
   - Only shows success toast when listing actually persisted

2. **Incomplete Result Handler** (Line 130-147):
   - Catches `status: 'complete'` with missing/invalid `listing_id`
   - Shows error toast: "Import failed - Import completed but listing was not created"
   - Error code: `INCOMPLETE_RESULT`, retryable: `true`

3. **Partial Data Handler** (Line 148-165):
   - Handles `status: 'partial'` when extraction incomplete
   - Shows error toast: "Import incomplete - [backend message]"
   - Error code: `PARTIAL_DATA`, retryable: `true`

**Testing**: Users importing Amazon URLs that fail extraction now see error toasts instead of false success messages

**Commits**: b5785d5 (diagnostic logging), a1efe3c (frontend toast fix)

## 2025-11-07: Enhanced Amazon Price Extraction with Additional Selectors

**Issue**: Amazon product imports failing with "Price extraction failed" even though price data exists on page. Logs showed title extraction succeeded but price extraction consistently failed for URL: `https://www.amazon.com/dp/B0FD3BCMBS?th=1` (Beelink SER5 MAX - $299)

**Location**: `apps/api/dealbrain_api/adapters/jsonld.py:1041-1122`

**Root Cause**: The HTML element fallback (added earlier on 2025-11-07) only tried 4 price selectors:
1. `span.a-price span.a-offscreen` (generic Amazon pattern)
2. `.price` (generic)
3. `itemprop="price"` (Schema.org - doesn't exist on modern Amazon)
4. `.product-price` (generic)

Amazon's HTML structure has evolved and now uses more specific container IDs and newer class patterns. The generic `span.a-price span.a-offscreen` selector was not specific enough to match Amazon's current desktop price display structure.

**Research Findings**: Comprehensive research of 2025 Amazon HTML structure revealed:
- Desktop price container: `#corePriceDisplay_desktop_feature_div`
- Multiple legacy selectors still in use: `#price_inside_buybox`, `#priceblock_ourprice`, `#priceblock_dealprice`
- Modern priceToPay pattern: `span.priceToPay span.a-offscreen`
- Visible price fallback: `.a-price span[aria-hidden='true']`

**Fix**: Enhanced price extraction with comprehensive Amazon-specific selector priority list (6 additional selectors):

**Priority Order** (before generic fallbacks):
1. `#corePriceDisplay_desktop_feature_div span.a-offscreen` - **NEW** - Most specific desktop price
2. `span.a-price span.a-offscreen` - Existing generic offscreen
3. `span.priceToPay span.a-offscreen` - **NEW** - Modern priceToPay pattern
4. `#price_inside_buybox` - **NEW** - Buy box price (legacy but still used)
5. `#priceblock_ourprice` - **NEW** - Legacy "our price" selector
6. `#priceblock_dealprice` - **NEW** - Legacy deal/sale price
7. `.a-price span[aria-hidden='true']` - **NEW** - Visible price components (aria-hidden pattern)
8. `.price`, `itemprop="price"`, `.product-price` - Existing generic fallbacks

**Implementation Details**:
- Added 6 new Amazon-specific CSS selectors before generic patterns
- Maintains backward compatibility with existing extraction logic
- Enhanced debug logging to show all attempted selectors
- Proper line length formatting (< 100 chars)

**Code Changes**:
```python
# Before: Only 1 Amazon-specific selector
offscreen_price = soup.select_one("span.a-price span.a-offscreen")

# After: 7 Amazon-specific selectors in priority order
# Priority 1: Desktop core price
offscreen_price = soup.select_one("#corePriceDisplay_desktop_feature_div span.a-offscreen")
# Priority 2: Generic offscreen
offscreen_price = soup.select_one("span.a-price span.a-offscreen")
# Priority 3: Modern priceToPay
element = soup.select_one("span.priceToPay span.a-offscreen")
# Priority 4: Buy box
element = soup.select_one("#price_inside_buybox")
# Priority 5-6: Legacy selectors
element = soup.select_one("#priceblock_ourprice")
element = soup.select_one("#priceblock_dealprice")
# Priority 7: Visible price with aria-hidden
element = soup.select_one(".a-price span[aria-hidden='true']")
```

**Testing**:
- Code linting passed (ruff)
- Worker service restarted to apply changes
- Awaiting real-world Amazon URL import verification

**Expected Outcome**: Amazon product pages with standard 2025 HTML structure should now successfully extract prices using the more comprehensive selector list, particularly the desktop core price display selector.

**Notes**:
- Amazon frequently updates their HTML structure; quarterly selector audits recommended
- Bot detection remains a separate concern that may require additional measures
- Selectors based on research of Amazon.com HTML structure as of 2025
- Regional Amazon domains (.co.uk, .de, etc.) may have variations

**Commit**: c102b3b
