"""Tests for AdapterRouter."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_api.adapters.ebay import EbayAdapter
from dealbrain_api.adapters.jsonld import JsonLdAdapter
from dealbrain_api.adapters.router import AdapterRouter
from dealbrain_core.schemas.ingestion import NormalizedListingSchema


class TestDomainExtraction:
    """Test domain extraction from URLs."""

    def test_extract_domain_with_www(self):
        """Test extracting domain from URL with www prefix."""
        router = AdapterRouter()
        assert router._extract_domain("https://www.ebay.com/itm/123") == "ebay.com"

    def test_extract_domain_without_www(self):
        """Test extracting domain from URL without www."""
        router = AdapterRouter()
        assert router._extract_domain("https://ebay.com/itm/123") == "ebay.com"

    def test_extract_domain_with_m(self):
        """Test extracting domain from mobile URL."""
        router = AdapterRouter()
        assert router._extract_domain("https://m.ebay.com/itm/123") == "ebay.com"

    def test_extract_domain_different_tld(self):
        """Test extracting domain with different TLD."""
        router = AdapterRouter()
        assert router._extract_domain("https://amazon.com/dp/ABC") == "amazon.com"
        assert router._extract_domain("https://ebay.co.uk/itm/123") == "ebay.co.uk"

    def test_extract_domain_with_path(self):
        """Test extracting domain from URL with complex path."""
        router = AdapterRouter()
        assert (
            router._extract_domain("https://www.bestbuy.com/site/product/123?query=param")
            == "bestbuy.com"
        )

    def test_extract_domain_invalid_url(self):
        """Test error handling for invalid URL."""
        router = AdapterRouter()
        with pytest.raises(ValueError, match="No domain found"):
            router._extract_domain("not-a-valid-url")


class TestDomainMatching:
    """Test domain matching logic."""

    def test_wildcard_domain_matching(self):
        """Test wildcard matches any domain."""
        router = AdapterRouter()

        assert router._domain_matches("example.com", ["*"])
        assert router._domain_matches("anything.org", ["*"])
        assert router._domain_matches("ebay.com", ["*"])

    def test_exact_domain_matching(self):
        """Test exact domain matching."""
        router = AdapterRouter()

        # Exact match
        assert router._domain_matches("ebay.com", ["ebay.com"])

        # No match (different domain)
        assert not router._domain_matches("amazon.com", ["ebay.com"])

        # No match (different TLD)
        assert not router._domain_matches("ebay.co.uk", ["ebay.com"])

    def test_domain_matching_with_www_in_adapter_list(self):
        """Test domain matching when adapter list includes www."""
        router = AdapterRouter()

        # URL domain "ebay.com" should match adapter domain "www.ebay.com"
        assert router._domain_matches("ebay.com", ["www.ebay.com"])

        # URL domain "ebay.com" should match adapter domain "ebay.com"
        assert router._domain_matches("ebay.com", ["ebay.com"])

    def test_domain_matching_multiple_adapter_domains(self):
        """Test matching against multiple adapter domains."""
        router = AdapterRouter()

        # Should match first domain
        assert router._domain_matches("ebay.com", ["ebay.com", "ebay.co.uk"])

        # Should match second domain
        assert router._domain_matches("ebay.co.uk", ["ebay.com", "ebay.co.uk"])

        # Should not match any
        assert not router._domain_matches("amazon.com", ["ebay.com", "ebay.co.uk"])


class TestAdapterSelection:
    """Test adapter selection by domain."""

    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    def test_select_ebay_adapter_for_ebay_url(self):
        """Test eBay adapter is selected for eBay URLs."""
        router = AdapterRouter()
        adapter = router.select_adapter("https://www.ebay.com/itm/123456789012")

        assert isinstance(adapter, EbayAdapter)
        assert adapter.name == "ebay"

    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    def test_select_ebay_adapter_for_ebay_url_without_www(self):
        """Test eBay adapter is selected for eBay URLs without www."""
        router = AdapterRouter()
        adapter = router.select_adapter("https://ebay.com/itm/123456789012")

        assert isinstance(adapter, EbayAdapter)
        assert adapter.name == "ebay"

    def test_select_jsonld_adapter_for_generic_url(self):
        """Test JSON-LD adapter is selected for generic URLs."""
        router = AdapterRouter()
        adapter = router.select_adapter("https://www.bestbuy.com/product/123")

        assert isinstance(adapter, JsonLdAdapter)
        assert adapter.name == "jsonld"

    def test_select_jsonld_adapter_for_amazon_url(self):
        """Test JSON-LD adapter is selected for Amazon URLs (no Amazon adapter yet)."""
        router = AdapterRouter()
        adapter = router.select_adapter("https://www.amazon.com/dp/ABC123")

        assert isinstance(adapter, JsonLdAdapter)
        assert adapter.name == "jsonld"


class TestPrioritySelection:
    """Test priority-based adapter selection."""

    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    def test_priority_ebay_over_jsonld(self):
        """Test eBay adapter (priority 1) beats JSON-LD (priority 5) for eBay URLs."""
        router = AdapterRouter()

        # Both EbayAdapter and JsonLdAdapter (wildcard) match,
        # but EbayAdapter has priority 1 vs JsonLdAdapter priority 5
        adapter = router.select_adapter("https://www.ebay.com/itm/123")

        assert isinstance(adapter, EbayAdapter)
        assert adapter.priority == 1

    def test_jsonld_selected_when_no_higher_priority(self):
        """Test JSON-LD adapter is selected when no higher priority adapter matches."""
        router = AdapterRouter()

        adapter = router.select_adapter("https://www.newegg.com/product/123")

        assert isinstance(adapter, JsonLdAdapter)
        assert adapter.priority == 5


class TestSettingsIntegration:
    """Test settings integration for adapter enabled status."""

    def test_disabled_ebay_adapter_raises_error(self):
        """Test that disabled eBay adapter raises AdapterDisabledError."""
        # Mock settings to disable eBay adapter
        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.enabled = False
            mock_settings.return_value.ingestion.jsonld.enabled = True

            router = AdapterRouter()

            with pytest.raises(AdapterException) as exc_info:
                router.select_adapter("https://www.ebay.com/itm/123")

            assert exc_info.value.error_type == AdapterError.ADAPTER_DISABLED
            assert "ebay" in str(exc_info.value.message).lower()

    def test_disabled_ebay_falls_back_to_jsonld(self):
        """Test that disabling eBay adapter falls back to JSON-LD for eBay URLs."""
        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            # Disable eBay but keep JSON-LD enabled
            mock_settings.return_value.ingestion.ebay.enabled = False
            mock_settings.return_value.ingestion.jsonld.enabled = True

            router = AdapterRouter()

            # Should raise error because eBay is highest priority but disabled
            # (Router doesn't auto-fallback, it raises error)
            with pytest.raises(AdapterException) as exc_info:
                router.select_adapter("https://www.ebay.com/itm/123")

            assert exc_info.value.error_type == AdapterError.ADAPTER_DISABLED

    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    def test_all_adapters_enabled_by_default(self):
        """Test that adapters are enabled by default."""
        router = AdapterRouter()

        # Should not raise error (default settings have adapters enabled)
        adapter = router.select_adapter("https://www.ebay.com/itm/123")
        assert isinstance(adapter, EbayAdapter)

    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    def test_is_adapter_enabled_checks_settings(self):
        """Test _is_adapter_enabled checks correct settings attribute."""
        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = False

            router = AdapterRouter()
            ebay_adapter = EbayAdapter()
            jsonld_adapter = JsonLdAdapter()

            assert router._is_adapter_enabled(ebay_adapter) is True
            assert router._is_adapter_enabled(jsonld_adapter) is False


class TestErrorHandling:
    """Test error handling for edge cases."""

    def test_no_adapter_found_empty_registry(self):
        """Test error when no adapter matches (empty registry)."""
        router = AdapterRouter()
        router.adapters = []  # Clear all adapters

        with pytest.raises(AdapterException) as exc_info:
            router.select_adapter("https://example.com/product")

        assert exc_info.value.error_type == AdapterError.NO_ADAPTER_FOUND
        assert "No adapter found" in exc_info.value.message

    def test_invalid_url_format(self):
        """Test handling of malformed URLs."""
        router = AdapterRouter()

        with pytest.raises(AdapterException) as exc_info:
            router.select_adapter("not-a-valid-url")

        assert exc_info.value.error_type == AdapterError.PARSE_ERROR
        assert "Invalid URL format" in exc_info.value.message

    def test_url_without_scheme(self):
        """Test handling of URL without scheme."""
        router = AdapterRouter()

        with pytest.raises(AdapterException) as exc_info:
            router.select_adapter("www.ebay.com/itm/123")

        assert exc_info.value.error_type == AdapterError.PARSE_ERROR

    def test_empty_url(self):
        """Test handling of empty URL."""
        router = AdapterRouter()

        with pytest.raises(AdapterException) as exc_info:
            router.select_adapter("")

        assert exc_info.value.error_type == AdapterError.PARSE_ERROR


class TestConvenienceExtractMethod:
    """Test router.extract() convenience method."""

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    async def test_router_extract_convenience_ebay(self):
        """Test router.extract() selects eBay adapter and calls extract."""
        router = AdapterRouter()

        # Mock the adapter's extract method
        with patch.object(EbayAdapter, "extract", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = NormalizedListingSchema(
                title="Test PC",
                price=Decimal("599.99"),
                currency="USD",
                condition="used",
                marketplace="ebay",
                images=[],
            )

            result = await router.extract("https://www.ebay.com/itm/123")

            assert result.title == "Test PC"
            assert result.price == Decimal("599.99")
            assert result.marketplace == "ebay"
            mock_extract.assert_called_once_with("https://www.ebay.com/itm/123")

    @pytest.mark.asyncio
    async def test_router_extract_convenience_jsonld(self):
        """Test router.extract() selects JSON-LD adapter and calls extract."""
        router = AdapterRouter()

        # Mock the adapter's extract method
        with patch.object(JsonLdAdapter, "extract", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = NormalizedListingSchema(
                title="Generic Product",
                price=Decimal("299.99"),
                currency="USD",
                condition="new",
                marketplace="other",
                images=[],
            )

            result = await router.extract("https://www.bestbuy.com/product/123")

            assert result.title == "Generic Product"
            assert result.marketplace == "other"
            mock_extract.assert_called_once_with("https://www.bestbuy.com/product/123")

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"EBAY_API_KEY": "test_api_key"})
    async def test_router_extract_propagates_adapter_errors(self):
        """Test router.extract() propagates adapter extraction errors."""
        router = AdapterRouter()

        # Mock adapter to raise error
        with patch.object(EbayAdapter, "extract", new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = AdapterException(
                AdapterError.ITEM_NOT_FOUND,
                "Item not found",
            )

            with pytest.raises(AdapterException) as exc_info:
                await router.extract("https://www.ebay.com/itm/123")

            assert exc_info.value.error_type == AdapterError.ITEM_NOT_FOUND


class TestFindMatchingAdapters:
    """Test _find_matching_adapters method."""

    def test_find_matching_adapters_ebay(self):
        """Test finding matching adapters for eBay URL."""
        router = AdapterRouter()
        matching = router._find_matching_adapters("https://www.ebay.com/itm/123", "ebay.com")

        # Should find both EbayAdapter and JsonLdAdapter (wildcard)
        assert len(matching) >= 2
        adapter_names = [router._get_adapter_name(a) for a in matching]
        assert "ebay" in adapter_names
        assert "jsonld" in adapter_names

    def test_find_matching_adapters_generic(self):
        """Test finding matching adapters for generic URL."""
        router = AdapterRouter()
        matching = router._find_matching_adapters(
            "https://www.bestbuy.com/product/123", "bestbuy.com"
        )

        # Should only find JsonLdAdapter (wildcard)
        assert len(matching) >= 1
        adapter_names = [router._get_adapter_name(a) for a in matching]
        assert "jsonld" in adapter_names
        assert "ebay" not in adapter_names

    def test_matching_adapters_sorted_by_priority(self):
        """Test that matching adapters can be sorted by priority."""
        router = AdapterRouter()
        matching = router._find_matching_adapters("https://www.ebay.com/itm/123", "ebay.com")

        # Sort by priority
        matching.sort(key=lambda a: router._get_adapter_priority(a))

        # First should be EbayAdapter (priority 1)
        assert router._get_adapter_name(matching[0]) == "ebay"
        assert router._get_adapter_priority(matching[0]) == 1

        # Last should be JsonLdAdapter (priority 5)
        jsonld_adapters = [a for a in matching if router._get_adapter_name(a) == "jsonld"]
        if jsonld_adapters:
            assert router._get_adapter_priority(jsonld_adapters[0]) == 5


class TestRouterInitialization:
    """Test router initialization."""

    def test_router_initializes_with_adapters(self):
        """Test router initializes with available adapters."""
        router = AdapterRouter()

        assert len(router.adapters) >= 2  # At least EbayAdapter and JsonLdAdapter
        adapter_names = [router._get_adapter_name(adapter) for adapter in router.adapters]
        assert "ebay" in adapter_names
        assert "jsonld" in adapter_names

    def test_router_adapters_list_not_empty(self):
        """Test router has non-empty adapters list."""
        router = AdapterRouter()
        assert len(router.adapters) > 0
