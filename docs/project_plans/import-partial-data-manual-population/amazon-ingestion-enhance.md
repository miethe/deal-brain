---
title: "Amazon Product Ingestion Enhancement Plan"
description: "Technical remediation plan for fixing Amazon HTML product data extraction. Addresses selector specificity issues, missing brand/specs/images, and list price extraction."
audience: [ai-agents, developers]
tags: [amazon, import, html-parsing, data-extraction, adapters, selectors]
created: 2025-11-10
updated: 2025-11-10
category: "product-planning"
status: published
related:
  - /docs/project_plans/import-partial-data-manual-population/phase-0-discovery.md
  - /docs/architecture/import-architecture-adr.md
---

# Amazon Product Ingestion Enhancement Plan

## Executive Summary

Amazon product ingestion is failing to extract pricing and key product attributes due to incorrect CSS selector specificity (`a-offscreen` vs. `aok-offscreen` class names). Current implementation extracts only title, missing deal price, list price, brand, structured specifications, and product images. This remediation implements 5 priority fixes to the JSON-LD/HTML fallback adapter, enabling complete product data extraction with >95% success rate on modern Amazon product pages.

## Root Cause Analysis

### Current Selector Failure Mechanism

The current price extraction in `apps/api/dealbrain_api/adapters/jsonld.py` (line ~1146) uses an incorrect CSS selector:

```python
offscreen_price = soup.select_one("#corePriceDisplay_desktop_feature_div span.a-offscreen")
```

**Why this fails:**

1. **Selector Matches Empty Element**: The selector matches a `<span class="a-offscreen">` inside the `priceToPay` container, but this span contains **empty or whitespace text** only.
2. **Missing Class Name Variant**: Amazon updated their CSS class from `a-offscreen` to `aok-offscreen` in recent versions. The "aok" prefix indicates "Amazon OK" (accessibility-related).
3. **Fallback Not Triggered**: When the selector finds an empty element, the fallback to regex-based price parsing is not triggered, resulting in `None` price value.

### Missing Data Extractions

Beyond the price selector issue, current implementation lacks:

- **Brand Information**: Not extracted from `#bylineInfo` or product table
- **List Price**: No separate extraction of original/regular price (only deal price attempted)
- **Structured Specifications**: CPU, RAM, Storage not extracted from product specs table
- **Product Images**: No image URLs extracted from product gallery

### Architectural Context

This adapter is the **HTML fallback** in a multi-adapter import strategy:

```
URL-Based Import Flow:
  ↓
  Marketplace Adapter (eBay, Amazon, etc.)
    ↓
    [Success] → Marketplace-specific parser
    ↓
    [Fallback] → Generic JSON-LD extraction
              → [Fallback] → HTML parsing (jsonld.py)
```

The HTML fallback must be robust for pages with missing or malformed JSON-LD metadata.

## Findings

### Selector Analysis: Current vs. Working

| Field | Current Selector | Status | Working Selector | Notes |
|-------|------------------|--------|------------------|-------|
| **Title** | `#productTitle` | ✓ Works | `#productTitle` | Already correct |
| **Deal Price** | `#corePriceDisplay_desktop_feature_div span.a-offscreen` | ✗ Broken | `#corePriceDisplay_desktop_feature_div span.aok-offscreen` | **Critical**: Class name variant; matches non-empty span |
| **List Price** | *(Not extracted)* | ✗ Missing | `span.basisPrice span.a-offscreen` | Fallback price in sale contexts |
| **Brand** | *(Not extracted)* | ✗ Missing | `#bylineInfo` with regex `Visit the (.+?) Store` | Extract from byline link text |
| **Specs** | Regex-parsed from description | ⚠ Fragile | `table.prodDetTable tr` key-value rows | Structured table extraction |
| **Images** | *(Not extracted)* | ✗ Missing | `img[data-old-hires]` or `img[data-a-dynamic-image]` | High-res image URLs in attributes |

### Test Case: Beelink SER5 MAX

**Product URL**: Amazon product page (captured HTML)

**Expected Extraction**:
- Title: "Beelink SER5 MAX Gaming Mini PC..."
- Brand: "Beelink"
- Deal Price: "$299.00"
- List Price: "$419.00"
- Specs: {"CPU": "AMD Ryzen 7 5700U", "RAM": "16GB", "Storage": "512GB SSD", ...}
- Images: [URL1, URL2, URL3, ...]

**Current Result**:
- Title: ✓ Extracted
- Brand: ✗ None
- Deal Price: ✗ None (selector matches empty element)
- List Price: ✗ None
- Specs: ⚠ Regex-parsed, unreliable
- Images: ✗ None

## Implementation Plan

### Priority 1: Fix Price Extraction (Critical)

**File**: `apps/api/dealbrain_api/adapters/jsonld.py`
**Line**: ~1146

**Change**: Update CSS selector class name from `a-offscreen` to `aok-offscreen`

```python
# BEFORE (Line ~1146)
offscreen_price = soup.select_one("#corePriceDisplay_desktop_feature_div span.a-offscreen")
if offscreen_price:
    raw_price = offscreen_price.get_text(strip=True)

# AFTER
offscreen_price = soup.select_one("#corePriceDisplay_desktop_feature_div span.aok-offscreen")
if offscreen_price:
    raw_price = offscreen_price.get_text(strip=True)
```

**Validation**: The fixed selector will match `<span class="aok-offscreen">$299.99</span>` directly instead of empty element.

**Fallback Logic**: If `aok-offscreen` fails, also try `a-offscreen` (older pages):
```python
offscreen_price = soup.select_one("#corePriceDisplay_desktop_feature_div span.aok-offscreen")
if not offscreen_price:
    offscreen_price = soup.select_one("#corePriceDisplay_desktop_feature_div span.a-offscreen")
    if offscreen_price and offscreen_price.get_text(strip=True):  # Validate non-empty
        pass
```

---

### Priority 2: Add List Price Extraction

**File**: `apps/api/dealbrain_api/adapters/jsonld.py`
**Location**: After price extraction (after line ~1160)

**Rationale**: Amazon shows `List Price: $X` separately from deal price. This enables pricing context for deal scoring.

```python
# NEW: Extract list price (original/regular price)
def _extract_list_price(soup: BeautifulSoup) -> Optional[str]:
    """Extract list price from 'basisPrice' section (original MSRP)."""
    basis_price = soup.select_one("span.basisPrice span.a-offscreen")
    if basis_price:
        raw_price = basis_price.get_text(strip=True)
        # Clean: "$419.99" → "419.99"
        price_match = re.search(r"[\d,]+\.?\d*", raw_price)
        if price_match:
            return price_match.group().replace(",", "")
    return None

# In main extraction function, after deal_price:
list_price = _extract_list_price(soup)
if list_price:
    product_data["list_price"] = list_price
```

**Integration**: Add `list_price` field to schema and ProductData model if not already present.

---

### Priority 3: Add Brand Extraction

**File**: `apps/api/dealbrain_api/adapters/jsonld.py`
**Location**: After price extraction (after line ~1165)

**Rationale**: Brand is critical for product identification and component valuation rules may filter by manufacturer.

```python
# NEW: Extract brand from byline
def _extract_brand(soup: BeautifulSoup) -> Optional[str]:
    """Extract brand from 'bylineInfo' link text pattern."""
    byline = soup.select_one("#bylineInfo")
    if byline:
        text = byline.get_text(strip=True)
        # Pattern: "Visit the [Brand] Store" → extract [Brand]
        match = re.search(r"Visit the (.+?) Store", text)
        if match:
            return match.group(1).strip()

    # Fallback: Check product title prefix
    title = soup.select_one("#productTitle")
    if title:
        title_text = title.get_text(strip=True)
        # Extract first word (often brand)
        brand_candidate = title_text.split()[0]
        if len(brand_candidate) > 1:  # Avoid single letters
            return brand_candidate

    return None

# In main extraction function:
brand = _extract_brand(soup)
if brand:
    product_data["brand"] = brand
```

**Integration**: Add `brand` field to ProductData model.

---

### Priority 4: Add Structured Specs Extraction

**File**: `apps/api/dealbrain_api/adapters/jsonld.py`
**Location**: Replace existing regex-based spec parsing (around line ~1180)

**Rationale**: Amazon provides structured `prodDetTable` with key-value rows. Replaces fragile regex parsing with reliable table extraction.

```python
# NEW: Extract structured specs from product details table
def _extract_specs_from_table(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract specifications from Amazon product details table."""
    specs = {}

    # Find the product details table
    spec_table = soup.select_one("table.prodDetTable")
    if not spec_table:
        return specs

    # Parse each row as key-value pair
    rows = spec_table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).rstrip(":")
            value = cells[1].get_text(strip=True)

            # Normalize key names
            key_normalized = key.lower().replace(" ", "_")

            # Extract only relevant specs (CPU, RAM, Storage, etc.)
            if any(term in key_normalized for term in ["cpu", "processor", "ram", "memory", "storage", "gpu", "graphics"]):
                specs[key_normalized] = value

    return specs

# In main extraction function:
specs = _extract_specs_from_table(soup)
if specs:
    product_data["specs"] = specs
```

**Integration**: Add `specs` dict field to ProductData model.

---

### Priority 5: Add Image Extraction

**File**: `apps/api/dealbrain_api/adapters/jsonld.py`
**Location**: After title extraction (after line ~1140)

**Rationale**: Product images are valuable for UI display and validation.

```python
# NEW: Extract product images
def _extract_images(soup: BeautifulSoup) -> List[str]:
    """Extract high-resolution product images from gallery."""
    images = []

    # Primary method: data-old-hires attribute (high-res)
    image_elements = soup.select("img[data-old-hires]")
    if not image_elements:
        # Fallback: data-a-dynamic-image attribute
        image_elements = soup.select("img[data-a-dynamic-image]")

    for img in image_elements:
        # Extract from data-old-hires attribute
        if img.has_attr("data-old-hires"):
            url = img.get("data-old-hires", "").strip()
            if url and url.startswith("http"):
                images.append(url)
        # Extract from data-a-dynamic-image attribute (JSON encoded)
        elif img.has_attr("data-a-dynamic-image"):
            try:
                dynamic_data = json.loads(img.get("data-a-dynamic-image", "{}"))
                # Keys are image URLs, values are dimensions
                for url in dynamic_data.keys():
                    if url.startswith("http"):
                        images.append(url)
                        break  # Take first/largest image
            except json.JSONDecodeError:
                pass

    return images[:5]  # Return max 5 images

# In main extraction function:
images = _extract_images(soup)
if images:
    product_data["images"] = images
```

**Integration**: Add `images` list field to ProductData model.

---

## Testing Strategy

### Unit Test Cases

**File**: Create or update `tests/adapters/test_amazon_html_extraction.py`

```python
import pytest
from dealbrain_api.adapters.jsonld import AmazonHTMLExtractor

class TestAmazonHTMLExtraction:
    """Test Amazon HTML fallback extraction."""

    @pytest.fixture
    def beelink_html(self):
        """Load captured Beelink SER5 MAX HTML."""
        with open("tests/fixtures/amazon_beelink_ser5_max.html") as f:
            return f.read()

    def test_extract_price(self, beelink_html):
        """Verify aok-offscreen selector extracts deal price."""
        data = AmazonHTMLExtractor.extract(beelink_html)
        assert data.get("price") == "299.00"

    def test_extract_list_price(self, beelink_html):
        """Verify list price extraction."""
        data = AmazonHTMLExtractor.extract(beelink_html)
        assert data.get("list_price") == "419.00"

    def test_extract_brand(self, beelink_html):
        """Verify brand extraction from byline."""
        data = AmazonHTMLExtractor.extract(beelink_html)
        assert data.get("brand") == "Beelink"

    def test_extract_specs(self, beelink_html):
        """Verify structured specs table extraction."""
        data = AmazonHTMLExtractor.extract(beelink_html)
        specs = data.get("specs", {})
        assert "cpu" in specs or "processor" in specs
        assert "ram" in specs or "memory" in specs

    def test_extract_images(self, beelink_html):
        """Verify image extraction with valid URLs."""
        data = AmazonHTMLExtractor.extract(beelink_html)
        images = data.get("images", [])
        assert len(images) > 0
        assert all(img.startswith("http") for img in images)

    def test_fallback_selector_a_offscreen(self, beelink_html_old):
        """Verify fallback to a-offscreen for older pages."""
        data = AmazonHTMLExtractor.extract(beelink_html_old)
        assert data.get("price") is not None  # Should still extract
```

### Integration Test

**Test against live capture**:
```bash
# Store captured Amazon HTML
cp amazon_product_page.html tests/fixtures/amazon_beelink_ser5_max.html

# Run extraction tests
poetry run pytest tests/adapters/test_amazon_html_extraction.py -v

# Verify import pipeline
poetry run dealbrain-cli import --test-adapter amazon tests/fixtures/amazon_beelink_ser5_max.html
```

### Manual Validation Checklist

- [ ] Extract deal price ($299.00) from test HTML
- [ ] Extract list price ($419.00) from test HTML
- [ ] Extract brand ("Beelink") from byline
- [ ] Extract CPU/RAM/Storage specs from prodDetTable
- [ ] Extract at least 1 product image URL (format: https://m.media-amazon.com/...)
- [ ] Fallback selector handles older Amazon pages (a-offscreen)
- [ ] Empty element detection prevents None values
- [ ] Regex price cleaning handles currency symbols and commas

## Success Metrics

### Quantitative Targets

| Metric | Current | Target | Validation |
|--------|---------|--------|------------|
| **Price Extraction Success Rate** | ~0% (selector broken) | >95% | Extract deal price from 95+ modern Amazon pages |
| **List Price Capture** | 0% (not extracted) | >80% | Extract from sale-context products |
| **Brand Extraction Rate** | 0% (not extracted) | >90% | Match against known manufacturers |
| **Specs Completeness** | ~40% (regex, unreliable) | >85% | CPU/RAM/Storage from table extraction |
| **Image Extraction Rate** | 0% (not extracted) | >90% | Get valid image URLs (https://) |
| **Overall Data Completeness** | ~20% (title only) | >85% | 6+ fields populated per product |

### Qualitative Improvements

- **Robustness**: Selector-based extraction more reliable than regex parsing
- **Maintainability**: Structured HTML selectors easier to update than brittle regexes
- **Coverage**: Enables brand/price filtering for deal scoring
- **User Experience**: Better UI display with images and complete metadata

### Regression Testing

- **Old Amazon Pages**: Verify fallback selector (a-offscreen) still works
- **Missing Specs Table**: Graceful handling when `prodDetTable` absent
- **Missing Images**: Optional field, doesn't break import pipeline
- **Malformed Prices**: Currency symbol/comma handling prevents crashes

## Implementation Checklist

### Code Changes
- [ ] Update price selector: `a-offscreen` → `aok-offscreen` (Priority 1)
- [ ] Add fallback selector logic for older pages
- [ ] Implement `_extract_list_price()` function (Priority 2)
- [ ] Implement `_extract_brand()` function (Priority 3)
- [ ] Implement `_extract_specs_from_table()` function (Priority 4)
- [ ] Implement `_extract_images()` function (Priority 5)
- [ ] Update ProductData schema with new fields (list_price, brand, specs, images)

### Testing
- [ ] Create test fixture: `tests/fixtures/amazon_beelink_ser5_max.html`
- [ ] Write unit tests for each extractor function
- [ ] Add integration tests to import pipeline
- [ ] Verify fallback logic for older pages
- [ ] Test edge cases (missing fields, malformed HTML)

### Documentation
- [ ] Update adapter documentation with new field descriptions
- [ ] Document Amazon-specific selector quirks (aok-offscreen class)
- [ ] Add troubleshooting guide for failed extractions

### Deployment
- [ ] Merge to `feat/amazon-ingestion-enhance` branch
- [ ] Run full test suite: `make test`
- [ ] Test with sample Amazon URLs in staging
- [ ] Update CHANGELOG with fixes

## Reference: Current Code Location

**File**: `apps/api/dealbrain_api/adapters/jsonld.py`

**Key Sections**:
- Line ~1140: Title extraction (working)
- Line ~1146: Price extraction (broken selector)
- Line ~1160: Current price fallback logic
- Line ~1180: Regex-based spec parsing (to be replaced)

**Schema**: Check `packages/core/dealbrain_core/schemas/product_data.py` for ProductData model

## Rollback Plan

If regressions occur:

1. **Revert selector change**: Keep fallback to both `aok-offscreen` and `a-offscreen`
2. **Disable new features**: Make brand/specs/images optional, non-blocking
3. **Adjust timeout**: If HTML parsing slows imports, reduce image extraction
4. **Monitor**: Track success rates in import logs for early detection

## Related Work

- **Import Architecture ADR**: `/docs/architecture/import-architecture-adr.md`
- **Phase 0 Discovery**: `/docs/project_plans/import-partial-data-manual-population/phase-0-discovery.md`
- **Adapter Patterns**: `apps/api/dealbrain_api/adapters/` directory structure
- **HTML Parsing Utilities**: BeautifulSoup4 selector documentation and CSS selectors reference
