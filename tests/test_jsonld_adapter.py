"""Tests for JSON-LD/Microdata adapter."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_api.adapters.jsonld import JsonLdAdapter


class TestJsonLdAdapter:
    """Test suite for JsonLdAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance."""
        return JsonLdAdapter()

    def test_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.name == "jsonld"
        assert adapter.supported_domains == ["*"]
        assert adapter.priority == 5
        assert adapter.timeout_s > 0
        assert adapter.retry_config.max_retries >= 0

    def test_supports_url(self, adapter):
        """Test that adapter supports all URLs (wildcard)."""
        assert adapter.supports_url("https://example.com/product")
        assert adapter.supports_url("https://retailer.com/item/123")
        assert adapter.supports_url("https://anything.com")

    @pytest.mark.asyncio
    async def test_extract_from_jsonld(self, adapter):
        """Test extraction from JSON-LD Product schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": "Gaming PC Intel i7-12700K 16GB 512GB SSD",
                "description": "High-performance gaming desktop with Intel Core i7-12700K processor, 16GB DDR4 RAM, and 512GB NVMe SSD storage",
                "image": "https://example.com/pc.jpg",
                "offers": {
                    "@type": "Offer",
                    "price": "599.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                    "seller": {
                        "@type": "Organization",
                        "name": "TechStore"
                    }
                }
            }
            </script>
        </head>
        <body><h1>Product Page</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Gaming PC Intel i7-12700K 16GB 512GB SSD"
        assert result.price == Decimal("599.99")
        assert result.currency == "USD"
        assert result.condition == "new"
        assert result.images == ["https://example.com/pc.jpg"]
        assert result.seller == "TechStore"
        assert result.marketplace == "other"
        assert result.cpu_model == "Intel Core i7-12700K"
        assert result.ram_gb == 16
        assert result.storage_gb == 512

    @pytest.mark.asyncio
    async def test_extract_from_microdata(self, adapter):
        """Test fallback to Microdata when JSON-LD absent."""
        html = """
        <html>
        <body>
            <div itemscope itemtype="http://schema.org/Product">
                <span itemprop="name">Gaming PC AMD Ryzen 7 5800X 32GB 1TB</span>
                <span itemprop="description">Desktop PC with AMD Ryzen 7 5800X, 32GB RAM, 1TB SSD</span>
                <div itemprop="offers" itemscope itemtype="http://schema.org/Offer">
                    <span itemprop="price">899.99</span>
                    <meta itemprop="priceCurrency" content="USD" />
                </div>
            </div>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Gaming PC AMD Ryzen 7 5800X 32GB 1TB"
        assert result.price == Decimal("899.99")
        assert result.currency == "USD"
        assert result.condition == "new"
        assert result.marketplace == "other"

    @pytest.mark.asyncio
    async def test_nested_offers_takes_lowest(self, adapter):
        """Test handling of multiple offers - take lowest price."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Gaming PC",
            "offers": [
                {
                    "@type": "Offer",
                    "price": "699.99",
                    "priceCurrency": "USD",
                    "seller": {"name": "Seller A"}
                },
                {
                    "@type": "Offer",
                    "price": "599.99",
                    "priceCurrency": "USD",
                    "seller": {"name": "Seller B"}
                },
                {
                    "@type": "Offer",
                    "price": "749.99",
                    "priceCurrency": "USD",
                    "seller": {"name": "Seller C"}
                }
            ]
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.price == Decimal("599.99")
        assert result.seller == "Seller A"  # First seller

    @pytest.mark.asyncio
    async def test_no_structured_data(self, adapter):
        """Test error when no Product schema found."""
        html = """
        <html>
        <body>
            <h1>Product Page</h1>
            <p>No structured data here</p>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA

    @pytest.mark.asyncio
    async def test_missing_required_title(self, adapter):
        """Test error when Product schema missing title/name."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "offers": {
                "price": "599.99",
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.INVALID_SCHEMA
            assert "name" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_missing_required_offers(self, adapter):
        """Test error when Product schema missing offers."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Gaming PC"
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.INVALID_SCHEMA
            assert "offers" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_missing_price_in_offers(self, adapter):
        """Test error when offers missing price."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Gaming PC",
            "offers": {
                "@type": "Offer",
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.INVALID_SCHEMA

    def test_parse_price_string_decimal(self, adapter):
        """Test price parsing from decimal string."""
        assert adapter._parse_price("599.99") == Decimal("599.99")
        assert adapter._parse_price("1299.00") == Decimal("1299.00")
        assert adapter._parse_price("49.95") == Decimal("49.95")

    def test_parse_price_string_with_dollar_sign(self, adapter):
        """Test price parsing with dollar sign."""
        assert adapter._parse_price("$599.99") == Decimal("599.99")
        assert adapter._parse_price("$1,299.00") == Decimal("1299.00")
        assert adapter._parse_price("$ 599") == Decimal("599")

    def test_parse_price_string_with_currency_code(self, adapter):
        """Test price parsing with currency code prefix."""
        assert adapter._parse_price("USD 599.99") == Decimal("599.99")
        assert adapter._parse_price("EUR 1299") == Decimal("1299")
        assert adapter._parse_price("GBP 49.95") == Decimal("49.95")

    def test_parse_price_number(self, adapter):
        """Test price parsing from numeric types."""
        assert adapter._parse_price(599.99) == Decimal("599.99")
        assert adapter._parse_price(1299) == Decimal("1299")
        assert adapter._parse_price(49.95) == Decimal("49.95")

    def test_parse_price_with_thousands_separator(self, adapter):
        """Test price parsing with comma separators."""
        assert adapter._parse_price("1,599.99") == Decimal("1599.99")
        assert adapter._parse_price("12,999.00") == Decimal("12999.00")
        assert adapter._parse_price("$2,499") == Decimal("2499")

    def test_parse_price_invalid(self, adapter):
        """Test price parsing with invalid inputs."""
        assert adapter._parse_price(None) is None
        assert adapter._parse_price("") is None
        assert adapter._parse_price("invalid") is None
        assert adapter._parse_price("N/A") is None

    def test_extract_cpu_intel(self, adapter):
        """Test CPU extraction for Intel processors."""
        text = "Gaming PC with Intel Core i7-12700K processor"
        specs = adapter._extract_specs(text)
        assert "cpu_model" in specs
        assert "i7" in specs["cpu_model"].lower()
        assert "12700k" in specs["cpu_model"].lower()

    def test_extract_cpu_amd(self, adapter):
        """Test CPU extraction for AMD processors."""
        text = "Desktop PC featuring AMD Ryzen 7 5800X CPU"
        specs = adapter._extract_specs(text)
        assert "cpu_model" in specs
        assert "ryzen" in specs["cpu_model"].lower()

    def test_extract_cpu_without_brand(self, adapter):
        """Test CPU extraction without brand prefix."""
        text = "PC with i5-11400 processor"
        specs = adapter._extract_specs(text)
        assert "cpu_model" in specs
        assert "i5" in specs["cpu_model"].lower()

    def test_extract_ram_standard(self, adapter):
        """Test RAM extraction from standard formats."""
        text1 = "Features 16GB RAM"
        assert adapter._extract_specs(text1)["ram_gb"] == 16

        text2 = "32 GB DDR4 Memory"
        assert adapter._extract_specs(text2)["ram_gb"] == 32

        text3 = "8GB of RAM"
        assert adapter._extract_specs(text3)["ram_gb"] == 8

    def test_extract_ram_no_space(self, adapter):
        """Test RAM extraction without space."""
        text = "Includes 16GB DDR4"
        assert adapter._extract_specs(text)["ram_gb"] == 16

    def test_extract_storage_gb(self, adapter):
        """Test storage extraction in GB."""
        text1 = "512GB NVMe SSD"
        assert adapter._extract_specs(text1)["storage_gb"] == 512

        text2 = "256 GB SSD storage"
        assert adapter._extract_specs(text2)["storage_gb"] == 256

        text3 = "1000GB HDD"
        assert adapter._extract_specs(text3)["storage_gb"] == 1000

    def test_extract_storage_tb(self, adapter):
        """Test storage extraction in TB (converted to GB)."""
        text1 = "1TB SSD"
        assert adapter._extract_specs(text1)["storage_gb"] == 1024

        text2 = "2 TB NVMe"
        assert adapter._extract_specs(text2)["storage_gb"] == 2048

        text3 = "4TB HDD"
        assert adapter._extract_specs(text3)["storage_gb"] == 4096

    def test_extract_specs_combined(self, adapter):
        """Test extracting all specs from combined text."""
        text = "Gaming PC with Intel Core i7-12700K, 16GB DDR4 RAM, 512GB NVMe SSD"
        specs = adapter._extract_specs(text)

        assert "cpu_model" in specs
        assert "i7" in specs["cpu_model"].lower()
        assert specs["ram_gb"] == 16
        assert specs["storage_gb"] == 512

    def test_extract_specs_no_match(self, adapter):
        """Test spec extraction with no matches."""
        text = "A nice product for sale"
        specs = adapter._extract_specs(text)

        assert "cpu_model" not in specs
        assert "ram_gb" not in specs
        assert "storage_gb" not in specs

    def test_extract_specs_empty_text(self, adapter):
        """Test spec extraction with empty text."""
        specs = adapter._extract_specs("")
        assert specs == {}

        specs = adapter._extract_specs(None)
        assert specs == {}

    @pytest.mark.asyncio
    async def test_full_extraction_with_brand(self, adapter):
        """Test complete extraction with brand as seller."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Professional Workstation",
            "description": "Intel Core i9-12900K, 64GB RAM, 2TB SSD",
            "brand": {
                "@type": "Brand",
                "name": "Dell"
            },
            "offers": {
                "price": 1999.99,
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.seller == "Dell"
        assert result.cpu_model is not None
        assert "i9" in result.cpu_model.lower()
        assert result.ram_gb == 64
        assert result.storage_gb == 2048

    @pytest.mark.asyncio
    async def test_extract_with_multiple_images(self, adapter):
        """Test image extraction when multiple images present."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Product",
            "image": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg",
                "https://example.com/image3.jpg"
            ],
            "offers": {
                "price": "599.99"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should only extract first image
        assert len(result.images) == 1
        assert result.images[0] == "https://example.com/image1.jpg"

    @pytest.mark.asyncio
    async def test_condition_refurbished(self, adapter):
        """Test condition extraction for refurbished items."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Refurbished PC",
            "offers": {
                "price": "399.99",
                "availability": "https://schema.org/RefurbishedCondition"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.condition == "refurb"

    @pytest.mark.asyncio
    async def test_condition_used_from_item_condition(self, adapter):
        """Test condition extraction from itemCondition field."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Used PC",
            "offers": {
                "price": "299.99",
                "itemCondition": "https://schema.org/UsedCondition"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.condition == "used"

    @pytest.mark.asyncio
    async def test_network_timeout(self, adapter):
        """Test handling of network timeout."""
        with patch.object(
            adapter,
            "_fetch_html",
            side_effect=AdapterException(AdapterError.TIMEOUT, "Request timed out"),
        ):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.TIMEOUT

    @pytest.mark.asyncio
    async def test_404_not_found(self, adapter):
        """Test handling of 404 errors."""
        with patch.object(
            adapter,
            "_fetch_html",
            side_effect=AdapterException(AdapterError.ITEM_NOT_FOUND, "Page not found"),
        ):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.ITEM_NOT_FOUND

    def test_is_product_schema_jsonld(self, adapter):
        """Test product schema detection for JSON-LD."""
        assert adapter._is_product_schema({"@type": "Product"})
        assert adapter._is_product_schema({"@type": "product"})  # Case insensitive
        assert adapter._is_product_schema({"@type": ["Product", "Thing"]})
        assert not adapter._is_product_schema({"@type": "Organization"})
        assert not adapter._is_product_schema({})

    def test_is_product_schema_microdata(self, adapter):
        """Test product schema detection for Microdata."""
        assert adapter._is_product_schema({"type": "http://schema.org/Product"})
        assert adapter._is_product_schema({"type": "https://schema.org/Product"})
        assert adapter._is_product_schema({"type": "Product"})
        assert not adapter._is_product_schema({"type": "Organization"})

    def test_normalize_offers_single(self, adapter):
        """Test normalizing single offer to list."""
        offer = {"price": "599.99"}
        result = adapter._normalize_offers(offer)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == offer

    def test_normalize_offers_list(self, adapter):
        """Test normalizing offer list."""
        offers = [{"price": "599.99"}, {"price": "699.99"}]
        result = adapter._normalize_offers(offers)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result == offers

    def test_extract_images_single_string(self, adapter):
        """Test image extraction from single string."""
        product = {"image": "https://example.com/img.jpg"}
        images = adapter._extract_images(product)
        assert images == ["https://example.com/img.jpg"]

    def test_extract_images_list(self, adapter):
        """Test image extraction from list (takes first)."""
        product = {"images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]}
        images = adapter._extract_images(product)
        assert len(images) == 1
        assert images[0] == "https://example.com/img1.jpg"

    def test_extract_images_object_with_url(self, adapter):
        """Test image extraction from object with url field."""
        product = {"image": {"url": "https://example.com/img.jpg", "width": 800}}
        images = adapter._extract_images(product)
        assert images == ["https://example.com/img.jpg"]

    def test_extract_images_none(self, adapter):
        """Test image extraction when no images present."""
        product = {"name": "Product"}
        images = adapter._extract_images(product)
        assert images == []

    @pytest.mark.asyncio
    async def test_extract_with_minimal_schema(self, adapter):
        """Test extraction with minimal valid schema."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Basic PC",
            "offers": {
                "price": 299.99
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Basic PC"
        assert result.price == Decimal("299.99")
        assert result.currency == "USD"  # Default
        assert result.condition == "new"  # Default
        assert result.marketplace == "other"
        assert result.seller is None
        assert result.images == []


class TestJsonLdAdapterIntegration:
    """Integration tests for JsonLdAdapter with real HTML patterns."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance."""
        return JsonLdAdapter()

    @pytest.mark.asyncio
    async def test_real_world_product_page(self, adapter):
        """Test with realistic product page structure."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gaming Desktop PC - TechStore</title>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": "Custom Gaming Desktop PC",
                "description": "Powerful gaming desktop featuring Intel Core i7-12700K processor (12-core, 3.6GHz base), 16GB DDR4-3200 RAM, 512GB NVMe M.2 SSD, and Windows 11 Pro. Perfect for gaming, streaming, and content creation.",
                "image": "https://cdn.techstore.com/products/gaming-pc-001.jpg",
                "brand": {
                    "@type": "Brand",
                    "name": "TechBuilder"
                },
                "offers": {
                    "@type": "Offer",
                    "price": "1299.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock",
                    "seller": {
                        "@type": "Organization",
                        "name": "TechStore Inc."
                    },
                    "priceValidUntil": "2025-12-31"
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.8",
                    "reviewCount": "127"
                }
            }
            </script>
        </head>
        <body>
            <h1>Gaming Desktop PC</h1>
            <p>High-performance gaming system</p>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://techstore.com/products/gaming-pc-001")

        assert result.title == "Custom Gaming Desktop PC"
        assert result.price == Decimal("1299.99")
        assert result.currency == "USD"
        assert result.condition == "new"
        assert result.seller == "TechStore Inc."
        assert result.marketplace == "other"
        assert result.images == ["https://cdn.techstore.com/products/gaming-pc-001.jpg"]

        # Verify spec extraction from description
        assert result.cpu_model is not None
        assert "i7-12700k" in result.cpu_model.lower()
        assert result.ram_gb == 16
        assert result.storage_gb == 512

    @pytest.mark.asyncio
    async def test_marketplace_listing_multiple_sellers(self, adapter):
        """Test marketplace page with multiple seller offers."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Refurbished Dell OptiPlex i5 8GB 256GB",
            "offers": [
                {
                    "@type": "Offer",
                    "price": "349.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/RefurbishedCondition",
                    "seller": {"name": "Certified Refurbisher A"}
                },
                {
                    "@type": "Offer",
                    "price": "329.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/RefurbishedCondition",
                    "seller": {"name": "Certified Refurbisher B"}
                },
                {
                    "@type": "Offer",
                    "price": "369.99",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/RefurbishedCondition",
                    "seller": {"name": "Certified Refurbisher C"}
                }
            ]
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://marketplace.com/product/123")

        # Should take lowest price
        assert result.price == Decimal("329.99")
        assert result.condition == "refurb"
        # Should take first seller
        assert result.seller == "Certified Refurbisher A"
