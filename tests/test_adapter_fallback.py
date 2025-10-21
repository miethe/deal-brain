"""Integration tests for adapter fallback chain mechanism.

Tests the automatic fallback behavior when primary adapters fail.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_api.adapters.router import AdapterRouter
from dealbrain_api.adapters.ebay import EbayAdapter
from dealbrain_api.adapters.jsonld import JsonLdAdapter
from packages.core.dealbrain_core.schemas.ingestion import NormalizedListingSchema
from decimal import Decimal


class TestFallbackChain:
    """Test fallback mechanism when primary adapter fails."""

    @pytest.mark.asyncio
    async def test_ebay_url_falls_back_to_jsonld_when_no_api_key(self):
        """Test eBay URL uses JSON-LD when API key is missing."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            # Configure eBay adapter without API key
            mock_settings.return_value.ingestion.ebay.api_key = None
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock JSON-LD adapter to succeed
            expected_result = NormalizedListingSchema(
                title="Test PC",
                price=Decimal("100.00"),
                currency="USD",
                condition="used",
                marketplace="ebay",
                images=["https://example.com/image.jpg"],
            )

            with patch.object(
                JsonLdAdapter, "extract", AsyncMock(return_value=expected_result)
            ):
                router = AdapterRouter()
                result = await router.extract(url)

                # Should succeed with JSON-LD fallback
                assert result == expected_result
                assert result.title == "Test PC"

    @pytest.mark.asyncio
    async def test_fallback_chain_logs_attempts(self, caplog):
        """Test that fallback attempts are logged."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            # Configure eBay adapter without API key
            mock_settings.return_value.ingestion.ebay.api_key = None
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock JSON-LD to succeed
            expected_result = NormalizedListingSchema(
                title="Test PC",
                price=Decimal("100.00"),
                currency="USD",
                condition="used",
                marketplace="ebay",
                images=[],
            )

            with patch.object(
                JsonLdAdapter, "extract", AsyncMock(return_value=expected_result)
            ):
                router = AdapterRouter()

                with caplog.at_level("INFO"):
                    await router.extract(url)

                # Check logs show both adapter attempts
                assert any("Trying adapter ebay" in record.message for record in caplog.records)
                assert any("ebay adapter failed" in record.message for record in caplog.records)
                assert any("Trying adapter jsonld" in record.message for record in caplog.records)
                assert any("Success with jsonld" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_fast_fail_for_item_not_found(self):
        """Test that ITEM_NOT_FOUND errors don't trigger fallback."""
        url = "https://www.ebay.com/itm/999999999999"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            # Configure eBay adapter with API key
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True

            # Mock eBay adapter to return 404
            with patch.object(
                EbayAdapter,
                "extract",
                AsyncMock(
                    side_effect=AdapterException(
                        AdapterError.ITEM_NOT_FOUND,
                        "Item not found",
                        metadata={"url": url},
                    )
                ),
            ):
                router = AdapterRouter()

                with pytest.raises(AdapterException) as exc:
                    await router.extract(url)

                # Should fast-fail, not try other adapters
                assert exc.value.error_type == AdapterError.ITEM_NOT_FOUND

    @pytest.mark.asyncio
    async def test_fast_fail_for_disabled_adapter(self):
        """Test that ADAPTER_DISABLED errors don't trigger fallback."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            # Disable eBay adapter
            mock_settings.return_value.ingestion.ebay.enabled = False

            router = AdapterRouter()

            with pytest.raises(AdapterException) as exc:
                await router.extract(url)

            # Should fast-fail when adapter is disabled
            assert exc.value.error_type == AdapterError.ADAPTER_DISABLED

    @pytest.mark.asyncio
    async def test_all_adapters_failed_error(self):
        """Test that ALL_ADAPTERS_FAILED is raised when all adapters fail."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            # Configure both adapters to fail
            mock_settings.return_value.ingestion.ebay.api_key = None
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock JSON-LD to also fail
            with patch.object(
                JsonLdAdapter,
                "extract",
                AsyncMock(
                    side_effect=AdapterException(
                        AdapterError.PARSE_ERROR,
                        "Failed to parse JSON-LD",
                    )
                ),
            ):
                router = AdapterRouter()

                with pytest.raises(AdapterException) as exc:
                    await router.extract(url)

                # Should raise ALL_ADAPTERS_FAILED
                assert exc.value.error_type == AdapterError.ALL_ADAPTERS_FAILED
                assert "2 adapters failed" in exc.value.message

                # Should include details about attempted adapters
                assert "attempted_adapters" in exc.value.metadata
                assert "ebay" in exc.value.metadata["attempted_adapters"]
                assert "jsonld" in exc.value.metadata["attempted_adapters"]


class TestPriorityOrdering:
    """Test that adapters are tried in correct priority order."""

    @pytest.mark.asyncio
    async def test_higher_priority_adapter_tried_first(self):
        """Test that EbayAdapter (priority 1) is tried before JsonLdAdapter (priority 5)."""
        url = "https://www.ebay.com/itm/123456789012"
        attempts = []

        def track_ebay_attempt(*args, **kwargs):
            attempts.append("ebay")
            raise AdapterException(
                AdapterError.CONFIGURATION_ERROR,
                "No API key",
            )

        def track_jsonld_attempt(*args, **kwargs):
            attempts.append("jsonld")
            return NormalizedListingSchema(
                title="Test",
                price=Decimal("100.00"),
                currency="USD",
                condition="used",
                marketplace="ebay",
                images=[],
            )

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = None
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            with patch.object(EbayAdapter, "extract", AsyncMock(side_effect=track_ebay_attempt)):
                with patch.object(JsonLdAdapter, "extract", AsyncMock(side_effect=track_jsonld_attempt)):
                    router = AdapterRouter()
                    await router.extract(url)

                    # eBay should be tried first, then JSON-LD
                    assert attempts == ["ebay", "jsonld"]

    @pytest.mark.asyncio
    async def test_fallback_stops_at_first_success(self):
        """Test that fallback stops after first successful adapter."""
        url = "https://www.bestbuy.com/product/123"
        attempts = []

        def track_jsonld_attempt(*args, **kwargs):
            attempts.append("jsonld")
            return NormalizedListingSchema(
                title="Test",
                price=Decimal("100.00"),
                currency="USD",
                condition="new",
                marketplace="other",
                images=[],
            )

        with patch.object(JsonLdAdapter, "extract", AsyncMock(side_effect=track_jsonld_attempt)):
            router = AdapterRouter()
            result = await router.extract(url)

            # Only JSON-LD should be tried (it succeeds)
            assert len(attempts) == 1
            assert attempts == ["jsonld"]
            assert result.title == "Test"


class TestErrorPropagation:
    """Test that different error types are handled correctly."""

    @pytest.mark.asyncio
    async def test_timeout_error_triggers_fallback(self):
        """Test that TIMEOUT errors trigger fallback to next adapter."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to timeout
            with patch.object(
                EbayAdapter,
                "extract",
                AsyncMock(
                    side_effect=AdapterException(
                        AdapterError.TIMEOUT,
                        "Request timed out",
                    )
                ),
            ):
                # Mock JSON-LD to succeed
                expected_result = NormalizedListingSchema(
                    title="Fallback PC",
                    price=Decimal("200.00"),
                    currency="USD",
                    condition="used",
                    marketplace="ebay",
                    images=[],
                )

                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=expected_result)):
                    router = AdapterRouter()
                    result = await router.extract(url)

                    # Should succeed with JSON-LD fallback
                    assert result.title == "Fallback PC"

    @pytest.mark.asyncio
    async def test_network_error_triggers_fallback(self):
        """Test that NETWORK_ERROR errors trigger fallback."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to have network error
            with patch.object(
                EbayAdapter,
                "extract",
                AsyncMock(
                    side_effect=AdapterException(
                        AdapterError.NETWORK_ERROR,
                        "Connection failed",
                    )
                ),
            ):
                # Mock JSON-LD to succeed
                expected_result = NormalizedListingSchema(
                    title="Network Fallback",
                    price=Decimal("300.00"),
                    currency="USD",
                    condition="new",
                    marketplace="ebay",
                    images=[],
                )

                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=expected_result)):
                    router = AdapterRouter()
                    result = await router.extract(url)

                    # Should succeed with JSON-LD fallback
                    assert result.title == "Network Fallback"


class TestBackwardCompatibility:
    """Test that existing select_adapter() method still works."""

    def test_select_adapter_still_works(self):
        """Test that select_adapter() method is preserved."""
        router = AdapterRouter()
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True

            adapter = router.select_adapter(url)

            # Should return EbayAdapter instance
            assert isinstance(adapter, EbayAdapter)
            assert adapter.name == "ebay"

    def test_select_adapter_respects_priority(self):
        """Test that select_adapter() returns highest priority adapter."""
        router = AdapterRouter()

        # For eBay URL, should return EbayAdapter (priority 1) not JsonLdAdapter (priority 5)
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            adapter = router.select_adapter(url)
            assert isinstance(adapter, EbayAdapter)

        # For generic URL, should return JsonLdAdapter
        url = "https://www.bestbuy.com/product/123"
        adapter = router.select_adapter(url)
        assert isinstance(adapter, JsonLdAdapter)
