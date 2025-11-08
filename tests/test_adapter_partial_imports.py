"""Tests for adapter partial import support.

This test suite verifies that adapters can handle listings where price extraction
fails (partial imports) while still creating valid listing records with quality
indicators and extraction metadata.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from dealbrain_api.adapters.base import AdapterError, AdapterException, BaseAdapter
from dealbrain_api.adapters.ebay import EbayAdapter
from dealbrain_api.adapters.jsonld import JsonLdAdapter
from dealbrain_core.schemas.ingestion import NormalizedListingSchema


@pytest.fixture
def mock_ebay_settings():
    """Mock settings for eBay adapter."""
    with patch("dealbrain_api.adapters.ebay.get_settings") as mock:
        settings = MagicMock()
        settings.ingestion.ebay.timeout_s = 6
        settings.ingestion.ebay.retries = 2
        settings.ingestion.ebay.api_key = "test_api_key_12345"
        mock.return_value = settings
        yield mock


@pytest.fixture
def mock_jsonld_settings():
    """Mock settings for JSON-LD adapter."""
    with patch("dealbrain_api.adapters.jsonld.get_settings") as mock:
        settings = MagicMock()
        settings.ingestion.jsonld.timeout_s = 8
        settings.ingestion.jsonld.retries = 2
        mock.return_value = settings
        yield mock


@pytest.fixture
def ebay_adapter(mock_ebay_settings):
    """Create EbayAdapter instance with mocked settings."""
    return EbayAdapter()


@pytest.fixture
def jsonld_adapter(mock_jsonld_settings):
    """Create JsonLdAdapter instance with mocked settings."""
    return JsonLdAdapter()


class TestBaseAdapterValidation:
    """Test BaseAdapter._validate_response() with partial import support."""

    @pytest.fixture
    def base_adapter_instance(self):
        """Create a concrete BaseAdapter instance for testing."""

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__(
                    name="test",
                    supported_domains=["test.com"],
                    priority=10,
                )

            async def extract(self, url: str) -> NormalizedListingSchema:
                # Not used in these tests
                raise NotImplementedError

        return TestAdapter()

    def test_validate_with_title_only_marks_partial(self, base_adapter_instance):
        """Test that data with title only is marked as partial."""
        data = {
            "title": "Test Product",
            "condition": "new",
            "marketplace": "test",
        }

        base_adapter_instance._validate_response(data)

        assert data["quality"] == "partial"
        assert data["missing_fields"] == ["price"]
        assert "title" in data["extraction_metadata"]
        assert data["extraction_metadata"]["title"] == "extracted"
        assert data["extraction_metadata"]["price"] == "extraction_failed"

    def test_validate_with_title_and_price_marks_full(self, base_adapter_instance):
        """Test that data with title and price is marked as full."""
        data = {
            "title": "Test Product",
            "price": Decimal("599.99"),
            "condition": "new",
            "marketplace": "test",
        }

        base_adapter_instance._validate_response(data)

        assert data["quality"] == "full"
        assert data["missing_fields"] == []
        assert "title" in data["extraction_metadata"]
        assert "price" in data["extraction_metadata"]
        assert data["extraction_metadata"]["title"] == "extracted"
        assert data["extraction_metadata"]["price"] == "extracted"
        assert "extraction_failed" not in data["extraction_metadata"].values()

    def test_validate_rejects_missing_title(self, base_adapter_instance):
        """Test that missing title raises exception even if price present."""
        data = {
            "price": Decimal("599.99"),
            "condition": "new",
            "marketplace": "test",
        }

        with pytest.raises(AdapterException) as exc_info:
            base_adapter_instance._validate_response(data)

        assert exc_info.value.error_type == AdapterError.INVALID_SCHEMA
        assert "title" in str(exc_info.value).lower()

    def test_validate_tracks_all_extracted_fields(self, base_adapter_instance):
        """Test that extraction_metadata tracks all present fields."""
        data = {
            "title": "Test Product",
            "condition": "new",
            "marketplace": "test",
            "seller": "TestSeller",
            "description": "Test description",
        }

        base_adapter_instance._validate_response(data)

        assert data["extraction_metadata"]["title"] == "extracted"
        assert data["extraction_metadata"]["condition"] == "extracted"
        assert data["extraction_metadata"]["marketplace"] == "extracted"
        assert data["extraction_metadata"]["seller"] == "extracted"
        assert data["extraction_metadata"]["description"] == "extracted"
        assert data["extraction_metadata"]["price"] == "extraction_failed"


class TestEbayAdapterPartialImports:
    """Test EbayAdapter partial import handling."""

    def test_map_to_schema_with_missing_price(self, ebay_adapter):
        """Test eBay adapter handles missing price gracefully."""
        item_data = {
            "itemId": "v1|123456789012|0",
            "title": "Gaming PC Intel Core i7",
            # price is missing
            "condition": "Used",
            "seller": {"username": "testseller"},
            "image": {"imageUrl": "https://example.com/image.jpg"},
        }

        result = ebay_adapter._map_to_schema(item_data)

        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price is None
        assert result.quality == "partial"
        assert result.missing_fields == ["price"]
        assert result.extraction_metadata["title"] == "extracted"
        assert result.extraction_metadata["price"] == "extraction_failed"

    def test_map_to_schema_with_complete_data(self, ebay_adapter):
        """Test eBay adapter marks complete data as full quality."""
        item_data = {
            "itemId": "v1|123456789012|0",
            "title": "Gaming PC Intel Core i7",
            "price": {"value": "599.99", "currency": "USD"},
            "condition": "Used",
            "seller": {"username": "testseller"},
            "image": {"imageUrl": "https://example.com/image.jpg"},
        }

        result = ebay_adapter._map_to_schema(item_data)

        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price == Decimal("599.99")
        assert result.quality == "full"
        assert result.missing_fields == []
        assert result.extraction_metadata["title"] == "extracted"
        assert result.extraction_metadata["price"] == "extracted"
        assert "extraction_failed" not in result.extraction_metadata.values()

    def test_map_to_schema_rejects_missing_title(self, ebay_adapter):
        """Test eBay adapter rejects data without title."""
        item_data = {
            "itemId": "v1|123456789012|0",
            # title is missing
            "price": {"value": "599.99", "currency": "USD"},
            "condition": "Used",
        }

        with pytest.raises(AdapterException) as exc_info:
            ebay_adapter._map_to_schema(item_data)

        assert exc_info.value.error_type == AdapterError.INVALID_SCHEMA
        assert "title" in str(exc_info.value).lower()

    def test_map_to_schema_tracks_optional_fields(self, ebay_adapter):
        """Test eBay adapter tracks extraction of optional fields."""
        item_data = {
            "itemId": "v1|123456789012|0",
            "title": "Gaming PC Intel Core i7",
            "condition": "Used",
            "seller": {"username": "testseller"},
            "shortDescription": "A great gaming PC",
            "localizedAspects": [
                {"name": "Processor", "value": "Intel Core i7-12700K"},
                {"name": "RAM Size", "value": "16 GB"},
                {"name": "SSD Capacity", "value": "512 GB"},
            ],
        }

        result = ebay_adapter._map_to_schema(item_data)

        assert result.extraction_metadata["seller"] == "extracted"
        assert result.extraction_metadata["description"] == "extracted"
        assert result.extraction_metadata["cpu_model"] == "extracted"
        assert result.extraction_metadata["ram_gb"] == "extracted"
        assert result.extraction_metadata["storage_gb"] == "extracted"


class TestJsonLdAdapterPartialImports:
    """Test JsonLdAdapter partial import handling."""

    def test_map_to_schema_with_missing_price(self, jsonld_adapter):
        """Test JSON-LD adapter handles missing price gracefully."""
        product_data = {
            "@type": "Product",
            "name": "Gaming PC Intel Core i7",
            "description": "A powerful gaming PC",
            "image": "https://example.com/image.jpg",
            # No offers/price
        }

        result = jsonld_adapter._map_to_schema(product_data, "https://test.com/product")

        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price is None
        assert result.quality == "partial"
        assert result.missing_fields == ["price"]
        assert result.extraction_metadata["title"] == "extracted"
        assert result.extraction_metadata["price"] == "extraction_failed"

    def test_map_to_schema_with_complete_data(self, jsonld_adapter):
        """Test JSON-LD adapter marks complete data as full quality."""
        product_data = {
            "@type": "Product",
            "name": "Gaming PC Intel Core i7",
            "description": "A powerful gaming PC",
            "image": "https://example.com/image.jpg",
            "offers": {
                "@type": "Offer",
                "price": "599.99",
                "priceCurrency": "USD",
            },
        }

        result = jsonld_adapter._map_to_schema(product_data, "https://test.com/product")

        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price == Decimal("599.99")
        assert result.quality == "full"
        assert result.missing_fields == []
        assert result.extraction_metadata["title"] == "extracted"
        assert result.extraction_metadata["price"] == "extracted"
        assert "extraction_failed" not in result.extraction_metadata.values()

    def test_map_to_schema_rejects_missing_title(self, jsonld_adapter):
        """Test JSON-LD adapter rejects data without title."""
        product_data = {
            "@type": "Product",
            # name is missing
            "description": "A product description",
            "offers": {
                "@type": "Offer",
                "price": "599.99",
            },
        }

        with pytest.raises(AdapterException) as exc_info:
            jsonld_adapter._map_to_schema(product_data, "https://test.com/product")

        assert exc_info.value.error_type == AdapterError.INVALID_SCHEMA
        assert "name" in str(exc_info.value).lower()

    def test_extract_from_meta_tags_partial(self, jsonld_adapter):
        """Test meta tag extraction creates partial import when price missing."""
        html = """
        <html>
        <head>
            <title>Gaming PC</title>
            <meta property="og:title" content="Gaming PC Intel Core i7" />
            <meta property="og:description" content="Great gaming PC" />
            <meta property="og:image" content="https://example.com/image.jpg" />
            <!-- No price meta tags -->
        </head>
        </html>
        """

        result = jsonld_adapter._extract_from_meta_tags(html, "https://test.com/product")

        assert result is not None
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price is None
        assert result.quality == "partial"
        assert result.missing_fields == ["price"]
        assert result.extraction_metadata["price"] == "extraction_failed"

    def test_extract_from_meta_tags_full(self, jsonld_adapter):
        """Test meta tag extraction creates full import when price present."""
        html = """
        <html>
        <head>
            <title>Gaming PC</title>
            <meta property="og:title" content="Gaming PC Intel Core i7" />
            <meta property="og:price:amount" content="599.99" />
            <meta property="og:price:currency" content="USD" />
        </head>
        </html>
        """

        result = jsonld_adapter._extract_from_meta_tags(html, "https://test.com/product")

        assert result is not None
        assert result.price == Decimal("599.99")
        assert result.quality == "full"
        assert result.missing_fields == []
        assert result.extraction_metadata["price"] == "extracted"

    def test_extract_from_html_elements_partial(self, jsonld_adapter):
        """Test HTML element extraction creates partial import when price missing."""
        html = """
        <html>
        <head><title>Gaming PC</title></head>
        <body>
            <h1 id="productTitle">Gaming PC Intel Core i7</h1>
            <!-- No price elements -->
        </body>
        </html>
        """

        result = jsonld_adapter._extract_from_html_elements(html, "https://test.com/product")

        assert result is not None
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price is None
        assert result.quality == "partial"
        assert result.missing_fields == ["price"]
        assert result.extraction_metadata["price"] == "extraction_failed"

    def test_extract_from_html_elements_full(self, jsonld_adapter):
        """Test HTML element extraction creates full import when price present."""
        html = """
        <html>
        <head><title>Gaming PC</title></head>
        <body>
            <h1 id="productTitle">Gaming PC Intel Core i7</h1>
            <div class="price">$599.99</div>
        </body>
        </html>
        """

        result = jsonld_adapter._extract_from_html_elements(html, "https://test.com/product")

        assert result is not None
        assert result.price == Decimal("599.99")
        assert result.quality == "full"
        assert result.missing_fields == []
        assert result.extraction_metadata["price"] == "extracted"


class TestExtractionMetadataTracking:
    """Test extraction metadata tracking across all adapters."""

    def test_ebay_tracks_all_extracted_fields(self, ebay_adapter):
        """Test eBay adapter tracks all successfully extracted fields."""
        item_data = {
            "itemId": "v1|123456789012|0",
            "title": "Gaming PC",
            "price": {"value": "599.99", "currency": "USD"},
            "condition": "Used",
            "seller": {"username": "testseller"},
            "image": {"imageUrl": "https://example.com/image.jpg"},
            "shortDescription": "Description",
            "localizedAspects": [
                {"name": "Processor", "value": "Intel Core i7"},
                {"name": "RAM Size", "value": "16 GB"},
            ],
        }

        result = ebay_adapter._map_to_schema(item_data)

        # Verify all fields marked as extracted
        expected_fields = [
            "title",
            "price",
            "condition",
            "marketplace",
            "currency",
            "vendor_item_id",
            "images",
            "seller",
            "description",
            "cpu_model",
            "ram_gb",
        ]
        for field in expected_fields:
            assert result.extraction_metadata[field] == "extracted"

    def test_jsonld_tracks_all_extracted_fields(self, jsonld_adapter):
        """Test JSON-LD adapter tracks all successfully extracted fields."""
        product_data = {
            "@type": "Product",
            "name": "Gaming PC",
            "description": "Intel Core i7-12700K, 16GB RAM",
            "image": "https://example.com/image.jpg",
            "offers": {
                "@type": "Offer",
                "price": "599.99",
                "priceCurrency": "USD",
                "seller": {"name": "TestSeller"},
            },
        }

        result = jsonld_adapter._map_to_schema(product_data, "https://test.com/product")

        # Verify all fields marked as extracted
        expected_fields = [
            "title",
            "price",
            "condition",
            "marketplace",
            "currency",
            "images",
            "seller",
            "description",
            "cpu_model",
            "ram_gb",
        ]
        for field in expected_fields:
            assert result.extraction_metadata[field] == "extracted"

    def test_extraction_failed_only_for_missing_price(self, ebay_adapter):
        """Test extraction_failed is only set for price when missing."""
        item_data = {
            "itemId": "v1|123456789012|0",
            "title": "Gaming PC",
            # No price
            "condition": "Used",
        }

        result = ebay_adapter._map_to_schema(item_data)

        # Only price should be marked as extraction_failed
        extraction_failed_fields = [
            k for k, v in result.extraction_metadata.items() if v == "extraction_failed"
        ]
        assert extraction_failed_fields == ["price"]
