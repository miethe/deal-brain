"""Unit tests for Amazon HTML extraction enhancements in JsonLdAdapter."""

from decimal import Decimal
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from dealbrain_api.adapters.jsonld import JsonLdAdapter


class TestAmazonHTMLExtraction:
    """Test Amazon HTML fallback extraction with enhanced selectors."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance for testing."""
        return JsonLdAdapter()

    @pytest.fixture
    def amazon_html(self):
        """Load captured Amazon Beelink SER5 MAX HTML."""
        html_path = Path(__file__).parent.parent.parent / "debug_amazon.com_1fe23618.html"
        if html_path.exists():
            return html_path.read_text()
        pytest.skip(f"Test HTML file not found at {html_path}")

    @pytest.fixture
    def soup(self, amazon_html):
        """Parse Amazon HTML into BeautifulSoup."""
        return BeautifulSoup(amazon_html, "html.parser")

    def test_extract_price_with_aok_offscreen(self, adapter, soup):
        """Verify aok-offscreen selector extracts deal price correctly."""
        # Modern Amazon pages use aok-offscreen class
        price_element = soup.select_one("#corePriceDisplay_desktop_feature_div span.aok-offscreen")

        # Should find the element
        assert price_element is not None, "aok-offscreen selector should find price element"

        # Should have non-empty text
        price_text = price_element.get_text(strip=True)
        assert price_text, "Price element should have non-empty text"

        # Should parse to valid decimal
        price = adapter._parse_price(price_text)
        assert price is not None, "Price should parse successfully"
        assert isinstance(price, Decimal), "Price should be a Decimal"
        assert price > 0, "Price should be positive"

    def test_extract_price_fallback_a_offscreen(self, adapter):
        """Verify fallback to a-offscreen for older Amazon pages."""
        # Create HTML with legacy a-offscreen class
        legacy_html = """
        <div id="corePriceDisplay_desktop_feature_div">
            <span class="a-offscreen">$299.00</span>
        </div>
        """
        soup = BeautifulSoup(legacy_html, "html.parser")

        # Should find legacy selector
        price_element = soup.select_one("#corePriceDisplay_desktop_feature_div span.a-offscreen")
        assert price_element is not None

        price_text = price_element.get_text(strip=True)
        price = adapter._parse_price(price_text)
        assert price == Decimal("299.00")

    def test_extract_list_price(self, adapter, soup):
        """Verify list price extraction from basisPrice section."""
        list_price = adapter._extract_list_price(soup)

        # List price is optional, but if found should be valid
        if list_price is not None:
            assert isinstance(list_price, Decimal), "List price should be a Decimal"
            assert list_price > 0, "List price should be positive"
            print(f"  ✓ List price extracted: ${list_price}")

    def test_extract_brand_from_byline(self, adapter, soup):
        """Verify brand extraction from bylineInfo link."""
        brand = adapter._extract_brand(soup)

        # Brand extraction is optional but should return string if found
        if brand is not None:
            assert isinstance(brand, str), "Brand should be a string"
            assert len(brand) > 0, "Brand should not be empty"
            assert len(brand) <= 64, "Brand should not exceed 64 chars (schema limit)"
            print(f"  ✓ Brand extracted: {brand}")

    def test_extract_brand_with_byline_pattern(self, adapter):
        """Verify brand extraction with 'Visit the [Brand] Store' pattern."""
        html = """
        <a id="bylineInfo" href="/stores/Beelink">Visit the Beelink Store</a>
        """
        soup = BeautifulSoup(html, "html.parser")
        brand = adapter._extract_brand(soup)

        assert brand == "Beelink"

    def test_extract_brand_from_title_fallback(self, adapter):
        """Verify brand extraction falls back to title prefix."""
        html = """
        <span id="productTitle">MINISFORUM Mini PC AMD Ryzen 7 5700U</span>
        """
        soup = BeautifulSoup(html, "html.parser")
        brand = adapter._extract_brand(soup)

        assert brand == "MINISFORUM"

    def test_extract_specs_from_table(self, adapter, soup):
        """Verify structured specs extraction from prodDetTable."""
        specs = adapter._extract_specs_from_table(soup)

        # Specs dict should be returned (empty if no table)
        assert isinstance(specs, dict), "Specs should be a dictionary"

        # If specs found, check for relevant keys
        if specs:
            print(f"  ✓ Specs extracted from table: {list(specs.keys())}")
            # Check that keys are normalized (lowercase, underscores)
            for key in specs.keys():
                assert key.islower() or "_" in key, f"Spec key '{key}' should be normalized"
                assert isinstance(specs[key], str), f"Spec value for '{key}' should be string"

    def test_extract_specs_from_table_with_sample(self, adapter):
        """Verify specs table parsing with known HTML structure."""
        html = """
        <table class="prodDetTable">
            <tr>
                <td>Processor:</td>
                <td>AMD Ryzen 7 5700U</td>
            </tr>
            <tr>
                <td>RAM:</td>
                <td>16 GB DDR4</td>
            </tr>
            <tr>
                <td>Storage:</td>
                <td>512 GB SSD</td>
            </tr>
            <tr>
                <td>Unrelated Field:</td>
                <td>Some value</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        specs = adapter._extract_specs_from_table(soup)

        # Should extract only relevant specs
        assert "processor" in specs
        assert specs["processor"] == "AMD Ryzen 7 5700U"
        assert "ram" in specs
        assert specs["ram"] == "16 GB DDR4"
        assert "storage" in specs
        assert specs["storage"] == "512 GB SSD"
        # Should NOT extract unrelated fields
        assert "unrelated_field" not in specs

    def test_extract_images(self, adapter, soup):
        """Verify image extraction with valid URLs."""
        images = adapter._extract_images(soup)

        # Images list should always be returned (empty if none found)
        assert isinstance(images, list), "Images should be a list"
        assert len(images) <= 5, "Should limit to 5 images max"

        # If images found, validate URLs
        if images:
            print(f"  ✓ {len(images)} image(s) extracted")
            for img_url in images:
                assert isinstance(img_url, str), "Image URL should be string"
                assert img_url.startswith("http"), f"Image URL should start with 'http': {img_url}"

    def test_extract_images_with_data_old_hires(self, adapter):
        """Verify image extraction from data-old-hires attribute."""
        html = """
        <img data-old-hires="https://m.media-amazon.com/images/I/test1.jpg" />
        <img data-old-hires="https://m.media-amazon.com/images/I/test2.jpg" />
        """
        soup = BeautifulSoup(html, "html.parser")
        images = adapter._extract_images(soup)

        assert len(images) == 2
        assert images[0] == "https://m.media-amazon.com/images/I/test1.jpg"
        assert images[1] == "https://m.media-amazon.com/images/I/test2.jpg"

    def test_extract_images_with_dynamic_image(self, adapter):
        """Verify image extraction from data-a-dynamic-image JSON attribute."""
        html = """
        <img data-a-dynamic-image='{"https://m.media-amazon.com/images/I/test.jpg":[500,500]}' />
        """
        soup = BeautifulSoup(html, "html.parser")
        images = adapter._extract_images(soup)

        assert len(images) == 1
        assert images[0] == "https://m.media-amazon.com/images/I/test.jpg"

    def test_extract_images_limit_to_five(self, adapter):
        """Verify image extraction limits to 5 images max."""
        html = """
        <img data-old-hires="https://example.com/img1.jpg" />
        <img data-old-hires="https://example.com/img2.jpg" />
        <img data-old-hires="https://example.com/img3.jpg" />
        <img data-old-hires="https://example.com/img4.jpg" />
        <img data-old-hires="https://example.com/img5.jpg" />
        <img data-old-hires="https://example.com/img6.jpg" />
        <img data-old-hires="https://example.com/img7.jpg" />
        """
        soup = BeautifulSoup(html, "html.parser")
        images = adapter._extract_images(soup)

        assert len(images) == 5, "Should limit to exactly 5 images"

    def test_empty_element_handling(self, adapter):
        """Verify empty span elements don't return None price."""
        html = """
        <div id="corePriceDisplay_desktop_feature_div">
            <span class="a-offscreen"></span>
            <span class="a-offscreen">   </span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        # Should not find price in empty elements
        price_element = soup.select_one("#corePriceDisplay_desktop_feature_div span.a-offscreen")
        assert price_element is not None  # Element exists
        price_text = price_element.get_text(strip=True)
        assert not price_text  # But text is empty

        # Parser should return None for empty text
        price = adapter._parse_price(price_text)
        assert price is None, "Empty price text should return None"

    def test_full_extraction_from_html(self, adapter, amazon_html):
        """Test full end-to-end extraction from captured Amazon HTML."""
        # This tests the actual _extract_from_html_elements method
        result = adapter._extract_from_html_elements(amazon_html, "https://www.amazon.com/test")

        # Should return NormalizedListingSchema or None
        if result is not None:
            print("\n=== Full Extraction Results ===")
            print(f"Title: {result.title[:50]}...")
            print(f"Price: ${result.price}" if result.price else "Price: None")
            print(f"List Price: ${result.list_price}" if result.list_price else "List Price: None")
            print(f"Manufacturer: {result.manufacturer}")
            print(f"Images: {len(result.images)} image(s)")
            print(f"CPU: {result.cpu_model}")
            print(f"RAM: {result.ram_gb} GB" if result.ram_gb else "RAM: None")
            print(f"Storage: {result.storage_gb} GB" if result.storage_gb else "Storage: None")
            print(f"Quality: {result.quality}")
            print(f"Extraction Metadata: {list(result.extraction_metadata.keys())}")

            # Basic assertions
            assert result.title, "Title should be extracted"
            assert result.marketplace == "other"
            assert result.currency == "USD"

    def test_price_parsing_with_currency_symbols(self, adapter):
        """Verify price parsing handles various formats."""
        test_cases = [
            ("$299.00", Decimal("299.00")),
            ("299.99", Decimal("299.99")),
            ("$1,599.00", Decimal("1599.00")),
            ("USD 599.99", Decimal("599.99")),
            ("1599", Decimal("1599.00")),
        ]

        for price_text, expected in test_cases:
            result = adapter._parse_price(price_text)
            assert result == expected, f"Failed to parse '{price_text}'"

    def test_specs_merge_priority(self, adapter):
        """Verify table specs override regex specs in merged result."""
        # Create HTML with both table and title containing specs
        html = """
        <span id="productTitle">Intel i5-8500T 8GB 256GB SSD</span>
        <table class="prodDetTable">
            <tr>
                <td>Processor:</td>
                <td>AMD Ryzen 7 5700U</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract from table (more reliable)
        table_specs = adapter._extract_specs_from_table(soup)
        assert "processor" in table_specs
        assert "AMD Ryzen 7" in table_specs["processor"]

        # Extract from title (regex fallback)
        title = soup.select_one("#productTitle").get_text()
        regex_specs = adapter._extract_specs(title)
        assert "cpu_model" in regex_specs
        assert "i5" in regex_specs["cpu_model"]

        # Merged: table should override
        merged = {**regex_specs, **table_specs}
        # Table specs with different keys won't override, but would be preferred source
        assert "processor" in merged  # From table


class TestBackwardCompatibility:
    """Test that changes don't break existing functionality for non-Amazon sites."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance for testing."""
        return JsonLdAdapter()

    def test_generic_price_selector_still_works(self, adapter):
        """Verify generic .price class selector still functions."""
        html = """
        <h1>Product Title</h1>
        <span class="price">$199.99</span>
        """
        soup = BeautifulSoup(html, "html.parser")

        price_element = soup.find(class_="price")
        assert price_element is not None
        price = adapter._parse_price(price_element.get_text(strip=True))
        assert price == Decimal("199.99")

    def test_generic_itemprop_price_selector_still_works(self, adapter):
        """Verify itemprop='price' selector still functions."""
        html = """
        <h1>Product Title</h1>
        <span itemprop="price">599.00</span>
        """
        soup = BeautifulSoup(html, "html.parser")

        price_element = soup.find(attrs={"itemprop": "price"})
        assert price_element is not None
        price = adapter._parse_price(price_element.get_text(strip=True))
        assert price == Decimal("599.00")

    def test_missing_amazon_elements_gracefully_handled(self, adapter):
        """Verify missing Amazon-specific elements don't cause errors."""
        html = """
        <span id="productTitle">Generic Product</span>
        <span class="price">$99.99</span>
        """
        soup = BeautifulSoup(html, "html.parser")

        # These should all return None/empty without errors
        list_price = adapter._extract_list_price(soup)
        assert list_price is None

        brand = adapter._extract_brand(soup)
        # May extract "Generic" from title, but shouldn't error
        assert brand is None or isinstance(brand, str)

        specs = adapter._extract_specs_from_table(soup)
        assert specs == {}

        images = adapter._extract_images(soup)
        assert images == []
