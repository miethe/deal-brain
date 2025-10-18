"""Tests for eBay Browse API adapter."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_api.adapters.ebay import EbayAdapter

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"
EBAY_RESPONSES_FILE = FIXTURES_DIR / "ebay_responses.json"


@pytest.fixture
def ebay_responses():
    """Load eBay API response fixtures."""
    with open(EBAY_RESPONSES_FILE) as f:
        return json.load(f)


@pytest.fixture
def mock_settings():
    """Mock settings with eBay API configuration."""
    with patch("dealbrain_api.adapters.ebay.get_settings") as mock:
        settings = MagicMock()
        settings.ingestion.ebay.timeout_s = 6
        settings.ingestion.ebay.retries = 2
        settings.ingestion.ebay.api_key = "test_api_key_12345"
        mock.return_value = settings
        yield mock


@pytest.fixture
def adapter(mock_settings):
    """Create EbayAdapter instance with mocked settings."""
    return EbayAdapter()


class TestEbayAdapterInit:
    """Test EbayAdapter initialization."""

    def test_init_success(self, adapter):
        """Test successful adapter initialization."""
        assert adapter.name == "ebay"
        assert adapter.supported_domains == ["ebay.com", "www.ebay.com"]
        assert adapter.priority == 1
        assert adapter.timeout_s == 6
        assert adapter.retry_config.max_retries == 2
        assert adapter.api_key == "test_api_key_12345"
        assert adapter.api_base == "https://api.ebay.com/buy/browse/v1"

    def test_init_missing_api_key(self, mock_settings):
        """Test initialization fails without API key."""
        mock_settings.return_value.ingestion.ebay.api_key = None

        with pytest.raises(ValueError, match="eBay Browse API key not configured"):
            EbayAdapter()

    def test_supports_url(self, adapter):
        """Test URL domain matching."""
        assert adapter.supports_url("https://www.ebay.com/itm/123456789012")
        assert adapter.supports_url("https://ebay.com/itm/123456789012")
        assert not adapter.supports_url("https://amazon.com/dp/B08X123456")


class TestUrlParsing:
    """Test URL parsing and item ID extraction."""

    def test_parse_item_id_standard_format(self, adapter):
        """Test parsing standard eBay URL format."""
        url = "https://www.ebay.com/itm/123456789012"
        item_id = adapter._parse_item_id(url)
        assert item_id == "123456789012"

    def test_parse_item_id_with_product_name(self, adapter):
        """Test parsing URL with product name slug."""
        url = "https://www.ebay.com/itm/Gaming-PC-Intel-i7/123456789012"
        item_id = adapter._parse_item_id(url)
        assert item_id == "123456789012"

    def test_parse_item_id_with_query_params(self, adapter):
        """Test parsing URL with query parameters."""
        url = "https://ebay.com/itm/123456789012?hash=abc&_trkparms=xyz"
        item_id = adapter._parse_item_id(url)
        assert item_id == "123456789012"

    def test_parse_item_id_with_hash(self, adapter):
        """Test parsing URL with hash fragment."""
        url = "https://www.ebay.com/itm/123456789012#section-description"
        item_id = adapter._parse_item_id(url)
        assert item_id == "123456789012"

    def test_parse_item_id_short_domain(self, adapter):
        """Test parsing URL with ebay.com (no www)."""
        url = "https://ebay.com/itm/987654321098"
        item_id = adapter._parse_item_id(url)
        assert item_id == "987654321098"

    def test_parse_item_id_13_digits(self, adapter):
        """Test parsing 13-digit item ID."""
        url = "https://www.ebay.com/itm/1234567890123"
        item_id = adapter._parse_item_id(url)
        assert item_id == "1234567890123"

    def test_parse_item_id_invalid_url(self, adapter):
        """Test parsing fails on invalid URL format."""
        url = "https://www.ebay.com/some-other-page"
        with pytest.raises(AdapterException) as exc:
            adapter._parse_item_id(url)

        assert exc.value.error_type == AdapterError.PARSE_ERROR
        assert "Could not extract eBay item ID" in exc.value.message

    def test_parse_item_id_non_ebay_url(self, adapter):
        """Test parsing fails on non-eBay URL."""
        url = "https://www.amazon.com/dp/B08X123456"
        with pytest.raises(AdapterException) as exc:
            adapter._parse_item_id(url)

        assert exc.value.error_type == AdapterError.PARSE_ERROR


class TestConditionNormalization:
    """Test eBay condition normalization."""

    def test_normalize_condition_new(self, adapter):
        """Test 'New' condition normalization."""
        assert adapter._normalize_condition("New") == "new"
        assert adapter._normalize_condition("New other (see details)") == "new"
        assert adapter._normalize_condition("Brand New") == "new"

    def test_normalize_condition_refurb(self, adapter):
        """Test refurbished condition normalization."""
        assert adapter._normalize_condition("Seller refurbished") == "refurb"
        assert adapter._normalize_condition("Manufacturer refurbished") == "refurb"
        assert adapter._normalize_condition("Certified Refurbished") == "refurb"

    def test_normalize_condition_used(self, adapter):
        """Test 'Used' condition normalization."""
        assert adapter._normalize_condition("Used") == "used"
        assert adapter._normalize_condition("Pre-owned") == "used"
        assert adapter._normalize_condition("For parts or not working") == "used"


class TestSpecExtraction:
    """Test extraction of CPU, RAM, and storage from item aspects."""

    def test_extract_cpu_from_aspects(self, adapter):
        """Test CPU extraction from localizedAspects."""
        aspects = [
            {"name": "Processor", "value": "Intel Core i7-12700K"},
            {"name": "RAM Size", "value": "16 GB"},
        ]
        cpu = adapter._extract_cpu_from_aspects(aspects)
        assert cpu == "Intel Core i7-12700K"

    def test_extract_cpu_processor_type(self, adapter):
        """Test CPU extraction with 'Processor Type' field name."""
        aspects = [{"name": "Processor Type", "value": "Intel Core i5-7500"}]
        cpu = adapter._extract_cpu_from_aspects(aspects)
        assert cpu == "Intel Core i5-7500"

    def test_extract_cpu_not_found(self, adapter):
        """Test CPU extraction returns None when not found."""
        aspects = [{"name": "RAM Size", "value": "16 GB"}]
        cpu = adapter._extract_cpu_from_aspects(aspects)
        assert cpu is None

    def test_extract_ram_from_aspects(self, adapter):
        """Test RAM extraction from localizedAspects."""
        aspects = [{"name": "RAM Size", "value": "16 GB"}]
        ram = adapter._extract_ram_from_aspects(aspects)
        assert ram == 16

    def test_extract_ram_with_memory_field(self, adapter):
        """Test RAM extraction with 'Memory' field name."""
        aspects = [{"name": "Memory", "value": "32 GB DDR4"}]
        ram = adapter._extract_ram_from_aspects(aspects)
        assert ram == 32

    def test_extract_ram_no_space(self, adapter):
        """Test RAM extraction with no space (e.g., '16GB')."""
        aspects = [{"name": "RAM", "value": "8GB"}]
        ram = adapter._extract_ram_from_aspects(aspects)
        assert ram == 8

    def test_extract_ram_not_found(self, adapter):
        """Test RAM extraction returns None when not found."""
        aspects = [{"name": "Processor", "value": "Intel i7"}]
        ram = adapter._extract_ram_from_aspects(aspects)
        assert ram is None

    def test_extract_storage_gb(self, adapter):
        """Test storage extraction in GB."""
        aspects = [{"name": "SSD Capacity", "value": "512 GB"}]
        storage = adapter._extract_storage_from_aspects(aspects)
        assert storage == 512

    def test_extract_storage_tb(self, adapter):
        """Test storage extraction in TB (converted to GB)."""
        aspects = [{"name": "Storage", "value": "2 TB SSD"}]
        storage = adapter._extract_storage_from_aspects(aspects)
        assert storage == 2048

    def test_extract_storage_hard_drive(self, adapter):
        """Test storage extraction with 'Hard Drive Capacity'."""
        aspects = [{"name": "Hard Drive Capacity", "value": "256 GB"}]
        storage = adapter._extract_storage_from_aspects(aspects)
        assert storage == 256

    def test_extract_storage_not_found(self, adapter):
        """Test storage extraction returns None when not found."""
        aspects = [{"name": "Processor", "value": "Intel i7"}]
        storage = adapter._extract_storage_from_aspects(aspects)
        assert storage is None


class TestSchemaMapping:
    """Test mapping eBay API response to NormalizedListingSchema."""

    def test_map_to_schema_full_specs(self, adapter, ebay_responses):
        """Test mapping with full specifications."""
        item_data = ebay_responses["success_full_specs"]
        schema = adapter._map_to_schema(item_data)

        assert schema.title == "Gaming PC Intel Core i7-12700K 16GB RAM 512GB SSD Windows 11 Pro"
        assert schema.price == Decimal("599.99")
        assert schema.currency == "USD"
        assert schema.condition == "used"
        assert len(schema.images) == 1
        assert schema.images[0].startswith("https://i.ebayimg.com/")
        assert schema.seller == "techdeals123"
        assert schema.marketplace == "ebay"
        assert schema.vendor_item_id == "123456789012"  # Stripped v1| prefix
        assert schema.cpu_model == "Intel Core i7-12700K"
        assert schema.ram_gb == 16
        assert schema.storage_gb == 512
        assert "High-performance gaming PC" in schema.description

    def test_map_to_schema_minimal(self, adapter, ebay_responses):
        """Test mapping with minimal required fields."""
        item_data = ebay_responses["success_minimal"]
        schema = adapter._map_to_schema(item_data)

        assert schema.title == "Dell OptiPlex 7050 Mini PC"
        assert schema.price == Decimal("199.50")
        assert schema.currency == "USD"
        assert schema.condition == "new"
        assert schema.images == []
        assert schema.seller is None
        assert schema.marketplace == "ebay"
        assert schema.vendor_item_id == "987654321098"
        assert schema.cpu_model is None
        assert schema.ram_gb is None
        assert schema.storage_gb is None

    def test_map_to_schema_refurbished(self, adapter, ebay_responses):
        """Test mapping with refurbished condition."""
        item_data = ebay_responses["success_refurbished"]
        schema = adapter._map_to_schema(item_data)

        assert schema.condition == "refurb"
        assert schema.cpu_model == "Intel Core i5-7500"
        assert schema.ram_gb == 8
        assert schema.storage_gb == 256

    def test_map_to_schema_tb_storage(self, adapter, ebay_responses):
        """Test mapping with TB storage (converted to GB)."""
        item_data = ebay_responses["success_with_tb_storage"]
        schema = adapter._map_to_schema(item_data)

        assert schema.cpu_model == "Intel Xeon E-2286G"
        assert schema.ram_gb == 32
        assert schema.storage_gb == 2048  # 2TB -> 2048GB

    def test_map_to_schema_no_specs(self, adapter, ebay_responses):
        """Test mapping with no specs extracted."""
        item_data = ebay_responses["success_no_specs"]
        schema = adapter._map_to_schema(item_data)

        assert schema.title == "Generic Desktop Computer"
        assert schema.cpu_model is None
        assert schema.ram_gb is None
        assert schema.storage_gb is None

    def test_map_to_schema_itemspecifics_format(self, adapter, ebay_responses):
        """Test mapping with itemSpecifics instead of localizedAspects."""
        item_data = ebay_responses["success_itemspecifics_format"]
        schema = adapter._map_to_schema(item_data)

        assert schema.title == "Lenovo ThinkCentre M920q Tiny Desktop"
        assert schema.cpu_model == "Intel Core i7-9700T"
        assert schema.ram_gb == 16
        assert schema.storage_gb == 512
        assert schema.description == "Compact Lenovo desktop in excellent condition."

    def test_map_to_schema_missing_title(self, adapter, ebay_responses):
        """Test mapping fails when title is missing."""
        item_data = ebay_responses["error_missing_title"]

        with pytest.raises(AdapterException) as exc:
            adapter._map_to_schema(item_data)

        assert exc.value.error_type == AdapterError.INVALID_SCHEMA
        assert "Missing required field: title" in exc.value.message

    def test_map_to_schema_missing_price(self, adapter, ebay_responses):
        """Test mapping fails when price is missing."""
        item_data = ebay_responses["error_missing_price"]

        with pytest.raises(AdapterException) as exc:
            adapter._map_to_schema(item_data)

        assert exc.value.error_type == AdapterError.INVALID_SCHEMA
        assert "Missing required field: price.value" in exc.value.message


class TestApiFetching:
    """Test eBay API fetching with various scenarios."""

    @pytest.mark.asyncio
    async def test_fetch_item_success(self, adapter, ebay_responses):
        """Test successful item fetch from eBay API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ebay_responses["success_full_specs"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock rate limit check
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            result = await adapter._fetch_item("123456789012")

            assert result["title"] == "Gaming PC Intel Core i7-12700K 16GB RAM 512GB SSD Windows 11 Pro"
            assert result["itemId"] == "v1|123456789012|0"

    @pytest.mark.asyncio
    async def test_fetch_item_not_found(self, adapter):
        """Test handling of 404 item not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter._fetch_item("999999999999")

            assert exc.value.error_type == AdapterError.ITEM_NOT_FOUND
            assert "not found" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_fetch_item_unauthorized(self, adapter):
        """Test handling of 401 unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter._fetch_item("123456789012")

            assert exc.value.error_type == AdapterError.INVALID_SCHEMA
            assert "credentials" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_fetch_item_rate_limited(self, adapter):
        """Test handling of 429 rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter._fetch_item("123456789012")

            assert exc.value.error_type == AdapterError.RATE_LIMITED
            assert "rate limit" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_fetch_item_server_error(self, adapter):
        """Test handling of 500 server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter._fetch_item("123456789012")

            assert exc.value.error_type == AdapterError.NETWORK_ERROR
            assert "server error" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_fetch_item_timeout(self, adapter):
        """Test handling of request timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter._fetch_item("123456789012")

            assert exc.value.error_type == AdapterError.TIMEOUT
            assert "timed out" in exc.value.message.lower()

    @pytest.mark.asyncio
    async def test_fetch_item_network_error(self, adapter):
        """Test handling of network error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.NetworkError("Network unreachable")
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter._fetch_item("123456789012")

            assert exc.value.error_type == AdapterError.NETWORK_ERROR
            assert "Network error" in exc.value.message


class TestExtractEndToEnd:
    """Test end-to-end extraction workflow."""

    @pytest.mark.asyncio
    async def test_extract_success(self, adapter, ebay_responses):
        """Test successful end-to-end extraction."""
        url = "https://www.ebay.com/itm/123456789012"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ebay_responses["success_full_specs"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            result = await adapter.extract(url)

            assert isinstance(result, type(result))  # Check it's a NormalizedListingSchema
            assert result.title == "Gaming PC Intel Core i7-12700K 16GB RAM 512GB SSD Windows 11 Pro"
            assert result.price == Decimal("599.99")
            assert result.cpu_model == "Intel Core i7-12700K"
            assert result.ram_gb == 16
            assert result.storage_gb == 512

    @pytest.mark.asyncio
    async def test_extract_with_retry(self, adapter, ebay_responses):
        """Test extraction with retry on timeout."""
        url = "https://www.ebay.com/itm/123456789012"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ebay_responses["success_minimal"]

        # First call times out, second succeeds
        mock_get = AsyncMock(
            side_effect=[
                httpx.TimeoutException("Timeout"),
                mock_response,
            ]
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            # Mock sleep to avoid actual waiting in tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await adapter.extract(url)

            assert result.title == "Dell OptiPlex 7050 Mini PC"
            assert mock_get.call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_extract_invalid_url(self, adapter):
        """Test extraction fails on invalid URL."""
        url = "https://www.ebay.com/invalid-page"

        with pytest.raises(AdapterException) as exc:
            await adapter.extract(url)

        assert exc.value.error_type == AdapterError.PARSE_ERROR

    @pytest.mark.asyncio
    async def test_extract_item_not_found(self, adapter):
        """Test extraction fails on 404 (non-retryable)."""
        url = "https://www.ebay.com/itm/999999999999"
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            adapter.rate_limit_config.check_and_wait = AsyncMock()

            with pytest.raises(AdapterException) as exc:
                await adapter.extract(url)

            assert exc.value.error_type == AdapterError.ITEM_NOT_FOUND
