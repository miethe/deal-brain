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


class TestJsonLdAdapterEdgeCases:
    """Edge case tests to improve coverage."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance."""
        return JsonLdAdapter()

    @pytest.mark.asyncio
    async def test_malformed_json_handled_gracefully(self, adapter):
        """Test handling of empty JSON-LD (no Product schema)."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "WebPage",
                "name": "Some Page"
            }
            </script>
        </head>
        <body>
            <h1>Product Page</h1>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            # Should fail when no Product schema found
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA

    @pytest.mark.asyncio
    async def test_multiple_jsonld_scripts_first_not_product(self, adapter):
        """Test handling multiple JSON-LD scripts where first is not Product."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Organization",
            "name": "TechStore"
        }
        </script>
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "Gaming PC",
            "offers": {
                "price": "599.99"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Gaming PC"
        assert result.price == Decimal("599.99")

    @pytest.mark.asyncio
    async def test_price_as_float_not_string(self, adapter):
        """Test price handling when provided as float instead of string."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "offers": {
                "price": 599.99
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.price == Decimal("599.99")

    @pytest.mark.asyncio
    async def test_missing_pricecurrency_defaults_to_usd(self, adapter):
        """Test that missing priceCurrency defaults to USD."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "offers": {
                "price": "599.99"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_offers_as_aggregate_offer(self, adapter):
        """Test handling of AggregateOffer with lowPrice."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "offers": {
                "@type": "AggregateOffer",
                "price": "549.99",
                "lowPrice": "549.99",
                "highPrice": "699.99",
                "priceCurrency": "USD"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should extract price
        assert result.price == Decimal("549.99")

    @pytest.mark.asyncio
    async def test_empty_offers_array(self, adapter):
        """Test error when offers array is empty."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "offers": []
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.INVALID_SCHEMA

    def test_extract_cpu_with_unusual_formats(self, adapter):
        """Test CPU extraction with unusual formats."""
        # Intel Core should work
        text1 = "PC with Intel Core i7-12700K processor"
        specs1 = adapter._extract_specs(text1)
        assert "cpu_model" in specs1

        # AMD Ryzen should work
        text2 = "Workstation with AMD Ryzen 9 5950X"
        specs2 = adapter._extract_specs(text2)
        assert "cpu_model" in specs2
        assert "ryzen" in specs2["cpu_model"].lower()

    def test_extract_ram_from_title_when_missing_in_description(self, adapter):
        """Test RAM extraction from combined title+description."""
        text = "Gaming PC i7 32GB 1TB SSD"
        specs = adapter._extract_specs(text)
        assert specs["ram_gb"] == 32
        assert specs["storage_gb"] == 1024

    def test_extract_storage_with_multiple_values(self, adapter):
        """Test storage extraction when multiple storage values present."""
        # Should extract first match
        text = "PC with 256GB SSD + 1TB HDD"
        specs = adapter._extract_specs(text)
        # Should find 256GB first
        assert specs["storage_gb"] == 256

    def test_extract_specs_with_mixed_units(self, adapter):
        """Test spec extraction with mixed storage units."""
        text = "Desktop: 512GB NVMe, 2TB HDD, 16GB DDR4 RAM"
        specs = adapter._extract_specs(text)
        # RAM extraction should find 16GB
        assert specs.get("ram_gb") is not None
        # Storage extraction should find some value
        assert specs.get("storage_gb") is not None
        assert specs["storage_gb"] > 0

    @pytest.mark.asyncio
    async def test_seller_from_nested_organization(self, adapter):
        """Test extracting seller from nested organization structure."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "offers": {
                "price": "599.99",
                "seller": {
                    "@type": "Organization",
                    "name": "TechStore Inc.",
                    "url": "https://techstore.com"
                }
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.seller == "TechStore Inc."

    @pytest.mark.asyncio
    async def test_image_as_object_with_url(self, adapter):
        """Test image extraction when image is object with url field."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "image": {
                "url": "https://example.com/img.jpg",
                "width": 800,
                "height": 600
            },
            "offers": {
                "price": "599.99"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should extract image URL from object
        assert len(result.images) > 0

    @pytest.mark.asyncio
    async def test_description_with_html_tags(self, adapter):
        """Test description extraction when containing HTML tags."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "description": "Gaming PC with <b>Intel i7</b>, <i>16GB RAM</i>, 512GB SSD",
            "offers": {
                "price": "599.99"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should still extract specs from description with HTML tags
        assert result.ram_gb == 16
        assert result.storage_gb == 512

    @pytest.mark.asyncio
    async def test_condition_from_text_in_offers(self, adapter):
        """Test condition detection from offer text fields."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "PC",
            "offers": {
                "price": "399.99",
                "availability": "https://schema.org/InStock",
                "itemCondition": "Refurbished"
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.condition == "refurb"

    @pytest.mark.asyncio
    async def test_microdata_extraction(self, adapter):
        """Test microdata extraction with offer structure."""
        html = """
        <div itemscope itemtype="http://schema.org/Product">
            <span itemprop="name">Gaming Desktop PC</span>
            <div itemprop="offers" itemscope itemtype="http://schema.org/Offer">
                <span itemprop="price">899.99</span>
                <meta itemprop="priceCurrency" content="USD" />
            </div>
        </div>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Gaming Desktop PC"
        assert result.price == Decimal("899.99")

    def test_parse_price_with_euro_symbol(self, adapter):
        """Test price parsing with Euro symbol."""
        assert adapter._parse_price("€599.99") == Decimal("599.99")
        assert adapter._parse_price("599.99€") == Decimal("599.99")

    def test_parse_price_with_pound_symbol(self, adapter):
        """Test price parsing with British pound symbol."""
        assert adapter._parse_price("£599.99") == Decimal("599.99")
        assert adapter._parse_price("599.99£") == Decimal("599.99")

    def test_parse_price_zero(self, adapter):
        """Test price parsing with zero value."""
        assert adapter._parse_price("0") == Decimal("0")
        assert adapter._parse_price("0.00") == Decimal("0.00")

    def test_parse_price_very_large_number(self, adapter):
        """Test price parsing with very large numbers."""
        assert adapter._parse_price("99,999.99") == Decimal("99999.99")
        assert adapter._parse_price("1,234,567.89") == Decimal("1234567.89")

    @pytest.mark.asyncio
    async def test_extract_with_whitespace_in_fields(self, adapter):
        """Test extraction with excessive whitespace in fields."""
        html = """
        <script type="application/ld+json">
        {
            "@type": "Product",
            "name": "  Gaming  PC  ",
            "description": "  Intel i7  16GB  512GB  ",
            "offers": {
                "price": "  599.99  "
            }
        }
        </script>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should handle whitespace correctly
        assert result.title.strip() == "Gaming  PC"
        assert result.price == Decimal("599.99")


class TestJsonLdAdapterMetaTagFallback:
    """Test suite for meta tag fallback extraction."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance."""
        return JsonLdAdapter()

    @pytest.mark.asyncio
    async def test_extract_from_opengraph_meta_tags(self, adapter):
        """Test extraction from OpenGraph meta tags when Schema.org absent."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="MINISFORUM UM690S Gaming PC AMD Ryzen 9 6900HX 16GB DDR5 512GB SSD">
            <meta property="og:price:amount" content="599.99">
            <meta property="og:price:currency" content="USD">
            <meta property="og:image" content="https://example.com/product.jpg">
            <meta property="og:description" content="Powerful mini PC with AMD Ryzen 9 6900HX processor, 16GB DDR5 RAM, and 512GB NVMe SSD">
            <meta property="og:site_name" content="Amazon">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Verify core fields
        assert result.title == "MINISFORUM UM690S Gaming PC AMD Ryzen 9 6900HX 16GB DDR5 512GB SSD"
        assert result.price == Decimal("599.99")
        assert result.currency == "USD"
        assert result.images == ["https://example.com/product.jpg"]
        assert result.description == "Powerful mini PC with AMD Ryzen 9 6900HX processor, 16GB DDR5 RAM, and 512GB NVMe SSD"
        assert result.seller == "Amazon"

        # Verify extracted specs from title and description
        assert result.cpu_model is not None
        assert "ryzen 9 6900hx" in result.cpu_model.lower()
        assert result.ram_gb == 16
        assert result.storage_gb == 512

        # Verify defaults
        assert result.marketplace == "other"
        assert result.condition == "new"  # Default

    @pytest.mark.asyncio
    async def test_extract_from_twitter_card_meta_tags(self, adapter):
        """Test extraction from Twitter Card meta tags."""
        html = """
        <html>
        <head>
            <meta name="twitter:title" content="Gaming Desktop Intel Core i7-12700K 32GB 1TB">
            <meta name="twitter:image" content="https://example.com/pc.jpg">
            <meta name="twitter:description" content="High-performance gaming PC with Intel Core i7-12700K, 32GB DDR4, 1TB SSD">
            <meta itemprop="price" content="899.99">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Verify core fields
        assert result.title == "Gaming Desktop Intel Core i7-12700K 32GB 1TB"
        assert result.price == Decimal("899.99")
        assert result.images == ["https://example.com/pc.jpg"]
        assert result.description == "High-performance gaming PC with Intel Core i7-12700K, 32GB DDR4, 1TB SSD"

        # Verify extracted specs
        assert result.cpu_model is not None
        assert "i7-12700k" in result.cpu_model.lower()
        assert result.ram_gb == 32
        assert result.storage_gb == 1024  # 1TB converted to GB

        # Verify defaults
        assert result.currency == "USD"  # Default
        assert result.marketplace == "other"

    @pytest.mark.asyncio
    async def test_fallback_to_meta_tags_when_no_structured_data(self, adapter):
        """Test fallback from Schema.org to meta tags when no Product schema."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Example Store"
            }
            </script>
            <meta property="og:title" content="Mini PC AMD Ryzen 7 5800H 16GB 512GB SSD">
            <meta property="og:price:amount" content="449.99">
            <meta property="og:image" content="https://example.com/mini-pc.jpg">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should successfully extract from meta tags
        assert result.title == "Mini PC AMD Ryzen 7 5800H 16GB 512GB SSD"
        assert result.price == Decimal("449.99")
        assert result.images == ["https://example.com/mini-pc.jpg"]

        # Verify specs extracted from title
        assert result.cpu_model is not None
        assert "ryzen 7 5800h" in result.cpu_model.lower()
        assert result.ram_gb == 16
        assert result.storage_gb == 512

    @pytest.mark.asyncio
    async def test_meta_tags_without_required_fields(self, adapter):
        """Test error when meta tags missing required fields (title or price)."""
        html = """
        <html>
        <head>
            <meta property="og:image" content="https://example.com/product.jpg">
            <meta property="og:description" content="Some description">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA
            assert "no schema.org product data, extractable meta tags, or html elements" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_meta_tag_price_formats(self, adapter):
        """Test price parsing from various meta tag formats."""
        test_cases = [
            ("599.99", Decimal("599.99")),
            ("$599.99", Decimal("599.99")),
            ("1,299.99", Decimal("1299.99")),
            ("€599.99", Decimal("599.99")),
            ("£1,599", Decimal("1599")),
            ("1299.00", Decimal("1299.00")),
        ]

        for price_str, expected_price in test_cases:
            html = f"""
            <html>
            <head>
                <meta property="og:title" content="Test Product">
                <meta property="og:price:amount" content="{price_str}">
            </head>
            <body><h1>Product</h1></body>
            </html>
            """

            with patch.object(adapter, "_fetch_html", return_value=html):
                result = await adapter.extract("https://example.com/product")

            assert result.price == expected_price, f"Failed to parse price '{price_str}'"
            assert result.title == "Test Product"

    @pytest.mark.asyncio
    async def test_multiple_image_meta_tags(self, adapter):
        """Test image extraction with multiple og:image tags."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Gaming PC">
            <meta property="og:price:amount" content="599.99">
            <meta property="og:image" content="https://example.com/image1.jpg">
            <meta property="og:image" content="https://example.com/image2.jpg">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # BeautifulSoup overwrites duplicate meta tags, so last one wins
        assert len(result.images) == 1
        assert result.images[0] == "https://example.com/image2.jpg"

    @pytest.mark.asyncio
    async def test_meta_tags_with_title_tag_fallback(self, adapter):
        """Test fallback to HTML <title> tag when no meta title."""
        html = """
        <html>
        <head>
            <title>Product Title from Title Tag</title>
            <meta itemprop="price" content="399.99">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Product Title from Title Tag"
        assert result.price == Decimal("399.99")

    @pytest.mark.asyncio
    async def test_meta_tags_spec_extraction_from_combined_fields(self, adapter):
        """Test spec extraction from combined title + description."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Gaming PC Intel i5-11400">
            <meta property="og:price:amount" content="499.99">
            <meta property="og:description" content="Desktop computer with 16GB RAM and 512GB SSD storage">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Specs should be extracted from both title and description
        assert result.cpu_model is not None
        assert "i5-11400" in result.cpu_model.lower()
        assert result.ram_gb == 16  # From description
        assert result.storage_gb == 512  # From description

    @pytest.mark.asyncio
    async def test_meta_tags_with_seller_extraction(self, adapter):
        """Test seller extraction from various meta tag sources."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Test Product">
            <meta property="og:price:amount" content="299.99">
            <meta property="og:site_name" content="TechStore">
            <meta name="twitter:site" content="@techstore">
            <meta name="author" content="TechStore Inc.">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should prioritize og:site_name
        assert result.seller == "TechStore"

    @pytest.mark.asyncio
    async def test_meta_tags_with_generic_price_meta(self, adapter):
        """Test price extraction from generic price meta tag."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Mini PC">
            <meta name="price" content="349.99">
            <meta name="currency" content="EUR">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.price == Decimal("349.99")
        assert result.currency == "EUR"

    @pytest.mark.asyncio
    async def test_meta_tags_without_description(self, adapter):
        """Test extraction when no description meta tag present."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Desktop PC Intel Core i7-12700K 32GB 1TB SSD">
            <meta property="og:price:amount" content="799.99">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should still extract specs from title
        assert result.cpu_model is not None
        assert "i7-12700k" in result.cpu_model.lower()
        assert result.ram_gb == 32
        assert result.storage_gb == 1024
        assert result.description is None

    @pytest.mark.asyncio
    async def test_meta_tags_with_unparseable_price(self, adapter):
        """Test error when meta tag price cannot be parsed."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Test Product">
            <meta property="og:price:amount" content="Contact for price">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA

    @pytest.mark.asyncio
    async def test_meta_tags_priority_opengraph_over_twitter(self, adapter):
        """Test that OpenGraph tags take priority over Twitter Card tags."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="OpenGraph Title">
            <meta name="twitter:title" content="Twitter Title">
            <meta property="og:price:amount" content="599.99">
            <meta itemprop="price" content="699.99">
            <meta property="og:image" content="https://example.com/og-image.jpg">
            <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should prioritize OpenGraph values
        assert result.title == "OpenGraph Title"
        assert result.price == Decimal("599.99")
        assert result.images == ["https://example.com/og-image.jpg"]

    @pytest.mark.asyncio
    async def test_meta_tags_with_only_title_no_price(self, adapter):
        """Test that extraction fails when price is missing."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Product Without Price">
            <meta property="og:description" content="Great product">
            <meta property="og:image" content="https://example.com/image.jpg">
        </head>
        <body><h1>Product</h1></body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA


class TestJsonLdAdapterHtmlElementFallback:
    """Test suite for HTML element extraction fallback (Amazon-style)."""

    @pytest.fixture
    def adapter(self):
        """Create JsonLdAdapter instance."""
        return JsonLdAdapter()

    @pytest.mark.asyncio
    async def test_extract_from_amazon_style_html_elements(self, adapter):
        """Test extraction from Amazon-style HTML elements when no meta tags."""
        html = """
        <html>
        <head>
            <meta name="description" content="High performance mini PC for gaming">
            <title>Amazon.com Product Page</title>
        </head>
        <body>
            <span id="productTitle">MINISFORUM UM690S Gaming PC AMD Ryzen 9 6900HX 16GB DDR5 512GB SSD</span>
            <span class="a-price">
                <span class="a-offscreen">$599.99</span>
            </span>
            <img data-old-hires="https://example.com/product-hires.jpg" src="https://example.com/product-lowres.jpg">
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://amazon.com/product")

        # Verify core fields
        assert result.title == "MINISFORUM UM690S Gaming PC AMD Ryzen 9 6900HX 16GB DDR5 512GB SSD"
        assert result.price == Decimal("599.99")
        assert result.currency == "USD"  # Default
        assert result.condition == "new"  # Default
        assert len(result.images) == 1
        assert result.images[0] == "https://example.com/product-hires.jpg"  # data-old-hires priority

        # Verify extracted specs
        assert result.cpu_model is not None
        assert "ryzen 9 6900hx" in result.cpu_model.lower()
        assert result.ram_gb == 16
        assert result.storage_gb == 512

        # Verify defaults
        assert result.marketplace == "other"
        assert result.seller is None

    @pytest.mark.asyncio
    async def test_extract_with_generic_html_patterns(self, adapter):
        """Test extraction using generic HTML class patterns."""
        html = """
        <html>
        <head>
            <meta name="description" content="Desktop computer with AMD processor">
        </head>
        <body>
            <h1 class="product-title">Gaming Desktop AMD Ryzen 7 5800X 32GB 1TB SSD</h1>
            <span class="price">$899.99</span>
            <img class="product-image" src="https://example.com/pc.jpg">
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://retailer.com/product")

        assert result.title == "Gaming Desktop AMD Ryzen 7 5800X 32GB 1TB SSD"
        assert result.price == Decimal("899.99")
        assert result.images == ["https://example.com/pc.jpg"]

        # Verify spec extraction from title
        assert result.cpu_model is not None
        assert "ryzen 7 5800x" in result.cpu_model.lower()
        assert result.ram_gb == 32
        assert result.storage_gb == 1024

    @pytest.mark.asyncio
    async def test_html_elements_fallback_after_meta_tags_fail(self, adapter):
        """Test that HTML elements are tried after meta tags fail."""
        html = """
        <html>
        <head>
            <meta property="og:image" content="https://example.com/image.jpg">
            <meta name="description" content="Great product description">
            <!-- No title or price in meta tags -->
        </head>
        <body>
            <h1 id="productTitle">Intel Core i7-12700K Gaming PC 16GB 512GB</h1>
            <span itemprop="price">799.99</span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should successfully extract from HTML elements
        assert result.title == "Intel Core i7-12700K Gaming PC 16GB 512GB"
        assert result.price == Decimal("799.99")
        assert result.description == "Great product description"

    @pytest.mark.asyncio
    async def test_html_elements_title_fallback_to_h1(self, adapter):
        """Test fallback to first h1 tag when no specific title selector."""
        html = """
        <html>
        <body>
            <h1>AMD Ryzen 5 5600X Desktop PC 16GB 256GB</h1>
            <span class="price">$449.99</span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "AMD Ryzen 5 5600X Desktop PC 16GB 256GB"
        assert result.price == Decimal("449.99")

    @pytest.mark.asyncio
    async def test_html_elements_price_with_dollar_sign(self, adapter):
        """Test price extraction with dollar sign in HTML element."""
        html = """
        <html>
        <body>
            <span id="productTitle">Test Product</span>
            <span class="a-price">
                <span class="a-offscreen">$1,299.99</span>
            </span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.price == Decimal("1299.99")

    @pytest.mark.asyncio
    async def test_html_elements_image_data_attributes(self, adapter):
        """Test image extraction from various data attributes."""
        html = """
        <html>
        <body>
            <span id="productTitle">Product</span>
            <span class="price">599.99</span>
            <img data-a-image-source="https://example.com/large.jpg" src="https://example.com/thumb.jpg">
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.images == ["https://example.com/large.jpg"]

    @pytest.mark.asyncio
    async def test_html_elements_skip_1x1_pixel_images(self, adapter):
        """Test that 1x1 pixel tracking images are skipped."""
        html = """
        <html>
        <body>
            <span id="productTitle">Product</span>
            <span class="price">599.99</span>
            <img src="https://example.com/1x1.gif">
            <img src="https://example.com/pixel.png">
            <img src="https://example.com/product.jpg">
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # Should skip 1x1 and pixel images, take product.jpg
        assert result.images == ["https://example.com/product.jpg"]

    @pytest.mark.asyncio
    async def test_html_elements_no_title_found(self, adapter):
        """Test error when no title can be found in HTML elements."""
        html = """
        <html>
        <body>
            <p>Some content without title</p>
            <span class="price">599.99</span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA
            assert "no schema.org product data, extractable meta tags, or html elements" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_html_elements_no_price_found(self, adapter):
        """Test error when no price can be found in HTML elements."""
        html = """
        <html>
        <body>
            <span id="productTitle">Test Product</span>
            <p>No price available</p>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA

    @pytest.mark.asyncio
    async def test_html_elements_with_itemprop_name(self, adapter):
        """Test title extraction from itemprop="name" attribute."""
        html = """
        <html>
        <body>
            <div itemprop="name">Desktop PC Intel i7 16GB 512GB</div>
            <span itemprop="price">699.99</span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.title == "Desktop PC Intel i7 16GB 512GB"
        assert result.price == Decimal("699.99")

    @pytest.mark.asyncio
    async def test_html_elements_description_from_meta(self, adapter):
        """Test description extraction from meta description tag."""
        html = """
        <html>
        <head>
            <meta name="description" content="Gaming PC with Intel Core i5-11400, 16GB RAM, 512GB SSD">
        </head>
        <body>
            <h1>Gaming Desktop PC</h1>
            <span class="price">$549.99</span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.description == "Gaming PC with Intel Core i5-11400, 16GB RAM, 512GB SSD"
        # Should extract specs from both title and description
        assert result.cpu_model is not None
        assert "i5-11400" in result.cpu_model.lower()
        assert result.ram_gb == 16
        assert result.storage_gb == 512

    @pytest.mark.asyncio
    async def test_html_elements_combined_specs_from_title_and_description(self, adapter):
        """Test spec extraction from combined title and description."""
        html = """
        <html>
        <head>
            <meta name="description" content="Desktop with 32GB DDR4 RAM and 1TB NVMe storage">
        </head>
        <body>
            <span id="productTitle">Intel Core i9-12900K Gaming PC</span>
            <span class="a-price"><span class="a-offscreen">$1499.99</span></span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        # CPU from title, RAM and storage from description
        assert result.cpu_model is not None
        assert "i9-12900k" in result.cpu_model.lower()
        assert result.ram_gb == 32
        assert result.storage_gb == 1024

    @pytest.mark.asyncio
    async def test_html_elements_with_no_images(self, adapter):
        """Test extraction when no images found."""
        html = """
        <html>
        <body>
            <span id="productTitle">Test Product</span>
            <span class="price">299.99</span>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            result = await adapter.extract("https://example.com/product")

        assert result.images == []
        assert result.title == "Test Product"
        assert result.price == Decimal("299.99")

    @pytest.mark.asyncio
    async def test_all_three_fallbacks_exhausted(self, adapter):
        """Test error when all three extraction methods fail."""
        html = """
        <html>
        <head>
            <title>Page Title</title>
        </head>
        <body>
            <p>Some content without structured data, meta tags, or HTML element patterns</p>
        </body>
        </html>
        """

        with patch.object(adapter, "_fetch_html", return_value=html):
            with pytest.raises(AdapterException) as exc:
                await adapter.extract("https://example.com/product")

            assert exc.value.error_type == AdapterError.NO_STRUCTURED_DATA
            assert "no schema.org product data, extractable meta tags, or html elements found" in exc.value.message.lower()
