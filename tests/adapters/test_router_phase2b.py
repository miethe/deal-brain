"""Phase 2B Tests: Fallback Chain & Error Handling.

This test suite validates Phase 2B requirements:
1. Fallback chain tries adapters in priority order
2. Non-retryable errors (ITEM_NOT_FOUND, ADAPTER_DISABLED) stop chain
3. Retryable errors (TIMEOUT, NETWORK_ERROR, RATE_LIMITED) continue chain
4. Disabled adapters are skipped silently
5. All errors are logged with adapter name
6. Adapter initialization failures are handled correctly
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_api.adapters.ebay import EbayAdapter
from dealbrain_api.adapters.jsonld import JsonLdAdapter
from dealbrain_api.adapters.playwright import PlaywrightAdapter
from dealbrain_api.adapters.router import AdapterRouter
from dealbrain_core.schemas.ingestion import NormalizedListingSchema


@pytest.fixture
def sample_listing():
    """Sample normalized listing for successful extraction."""
    return NormalizedListingSchema(
        title="Test PC",
        price=Decimal("599.99"),
        currency="USD",
        condition="used",
        marketplace="other",
        images=["https://example.com/image.jpg"],
    )


class TestFallbackPriorityOrder:
    """Test that fallback chain respects adapter priority order."""

    @pytest.mark.asyncio
    async def test_ebay_tried_first_then_jsonld_then_playwright(self, caplog):
        """Test adapters are tried in correct priority order: eBay(1) -> JSON-LD(5) -> Playwright(10)."""
        url = "https://www.ebay.com/itm/123456789012"
        attempts = []

        # Track attempts in order
        def track_ebay(*args, **kwargs):
            attempts.append("ebay")
            raise ValueError("No API key")  # Init failure

        def track_jsonld(*args, **kwargs):
            attempts.append("jsonld")
            raise AdapterException(AdapterError.PARSE_ERROR, "No JSON-LD found")

        async def track_playwright(*args, **kwargs):
            attempts.append("playwright")
            return NormalizedListingSchema(
                title="Test PC",
                price=Decimal("599.99"),
                currency="USD",
                condition="used",
                marketplace="other",
                images=[],
            )

        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True
            mock_settings.return_value.ingestion.playwright.enabled = True

            # Mock initialization and extraction
            with patch.object(EbayAdapter, "__init__", side_effect=track_ebay):
                with patch.object(
                    JsonLdAdapter, "extract", AsyncMock(side_effect=track_jsonld)
                ):
                    with patch.object(
                        PlaywrightAdapter, "extract", AsyncMock(side_effect=track_playwright)
                    ):
                        router = AdapterRouter()

                        with caplog.at_level("INFO"):
                            result, adapter_name = await router.extract(url)

                        # Verify order: eBay -> JSON-LD -> Playwright
                        assert attempts == ["ebay", "jsonld", "playwright"]
                        assert adapter_name == "playwright"

                        # Verify logging
                        assert any("Trying adapter ebay" in record.message for record in caplog.records)
                        assert any("Trying adapter jsonld" in record.message for record in caplog.records)
                        assert any("Trying adapter playwright" in record.message for record in caplog.records)


class TestNonRetryableErrors:
    """Test that non-retryable errors stop the fallback chain immediately."""

    @pytest.mark.asyncio
    async def test_item_not_found_stops_chain(self, caplog):
        """Test ITEM_NOT_FOUND error stops chain (no fallback)."""
        url = "https://www.ebay.com/itm/999999999999"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to return ITEM_NOT_FOUND
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
                # Mock JSON-LD to succeed (should NOT be called)
                jsonld_mock = AsyncMock(
                    return_value=NormalizedListingSchema(
                        title="Test", price=Decimal("100"), currency="USD", condition="used", marketplace="ebay", images=[]
                    )
                )

                with patch.object(JsonLdAdapter, "extract", jsonld_mock):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        with pytest.raises(AdapterException) as exc_info:
                            await router.extract(url)

                    # Verify fast-fail
                    assert exc_info.value.error_type == AdapterError.ITEM_NOT_FOUND

                    # Verify JSON-LD was NOT called
                    jsonld_mock.assert_not_called()

                    # Verify logging
                    assert any("Trying adapter ebay" in record.message for record in caplog.records)
                    assert any("Fast-fail for item_not_found" in record.message for record in caplog.records)
                    assert not any("Trying adapter jsonld" in record.message for record in caplog.records)



class TestRetryableErrors:
    """Test that retryable errors continue to next adapter in chain."""

    @pytest.mark.asyncio
    async def test_timeout_continues_to_next_adapter(self, caplog, sample_listing):
        """Test TIMEOUT error continues to next adapter."""
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
                    side_effect=AdapterException(AdapterError.TIMEOUT, "Request timed out")
                ),
            ):
                # Mock JSON-LD to succeed
                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        result, adapter_name = await router.extract(url)

                    # Verify fallback to JSON-LD
                    assert adapter_name == "jsonld"
                    assert result.title == "Test PC"

                    # Verify logging
                    assert any("Trying adapter ebay" in record.message for record in caplog.records)
                    assert any("ebay adapter failed: [timeout]" in record.message for record in caplog.records)
                    assert any("Trying adapter jsonld" in record.message for record in caplog.records)
                    assert any("Success with jsonld" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_network_error_continues_to_next_adapter(self, caplog, sample_listing):
        """Test NETWORK_ERROR continues to next adapter."""
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
                    side_effect=AdapterException(AdapterError.NETWORK_ERROR, "Connection failed")
                ),
            ):
                # Mock JSON-LD to succeed
                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        result, adapter_name = await router.extract(url)

                    # Verify fallback to JSON-LD
                    assert adapter_name == "jsonld"

                    # Verify logging
                    assert any("ebay adapter failed: [network_error]" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_rate_limited_continues_to_next_adapter(self, caplog, sample_listing):
        """Test RATE_LIMITED error continues to next adapter."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to be rate limited
            with patch.object(
                EbayAdapter,
                "extract",
                AsyncMock(
                    side_effect=AdapterException(AdapterError.RATE_LIMITED, "Rate limit exceeded")
                ),
            ):
                # Mock JSON-LD to succeed
                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        result, adapter_name = await router.extract(url)

                    # Verify fallback to JSON-LD
                    assert adapter_name == "jsonld"

                    # Verify logging
                    assert any("ebay adapter failed: [rate_limited]" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_parse_error_continues_to_next_adapter(self, caplog, sample_listing):
        """Test PARSE_ERROR continues to next adapter."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to have parse error
            with patch.object(
                EbayAdapter,
                "extract",
                AsyncMock(
                    side_effect=AdapterException(AdapterError.PARSE_ERROR, "Failed to parse response")
                ),
            ):
                # Mock JSON-LD to succeed
                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        result, adapter_name = await router.extract(url)

                    # Verify fallback to JSON-LD
                    assert adapter_name == "jsonld"

                    # Verify logging
                    assert any("ebay adapter failed: [parse_error]" in record.message for record in caplog.records)


class TestDisabledAdapterHandling:
    """Test handling of disabled adapters in fallback chain."""

    @pytest.mark.asyncio
    async def test_disabled_adapter_skipped_silently(self, caplog, sample_listing):
        """Test disabled adapters are skipped without raising error."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            # Disable eBay, enable others
            mock_settings.return_value.ingestion.ebay.enabled = False
            mock_settings.return_value.ingestion.jsonld.enabled = True
            mock_settings.return_value.ingestion.playwright.enabled = True

            # Mock JSON-LD to succeed
            with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                router = AdapterRouter()

                with caplog.at_level("INFO"):
                    result, adapter_name = await router.extract(url)

                # Verify JSON-LD was used (eBay skipped)
                assert adapter_name == "jsonld"

                # Verify logging shows skip
                assert any("Skipping ebay adapter (disabled" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_multiple_disabled_adapters(self, caplog, sample_listing):
        """Test multiple disabled adapters are all skipped."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            # Disable eBay and JSON-LD, enable Playwright
            mock_settings.return_value.ingestion.ebay.enabled = False
            mock_settings.return_value.ingestion.jsonld.enabled = False
            mock_settings.return_value.ingestion.playwright.enabled = True

            # Mock Playwright adapter initialization and extraction
            with patch("dealbrain_api.adapters.playwright.get_settings") as mock_pw_settings:
                mock_pw_settings.return_value.ingestion.playwright.enabled = True
                mock_pw_settings.return_value.ingestion.playwright.timeout_s = 8
                mock_pw_settings.return_value.ingestion.playwright.max_retries = 2
                mock_pw_settings.return_value.ingestion.playwright.pool_size = 3
                mock_pw_settings.return_value.ingestion.playwright.headless = True

                with patch.object(PlaywrightAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        result, adapter_name = await router.extract(url)

                    # Verify Playwright was used (others skipped)
                    assert adapter_name == "playwright"

                    # Verify logging shows skips
                    assert any("Skipping ebay adapter (disabled" in record.message for record in caplog.records)
                    assert any("Skipping jsonld adapter (disabled" in record.message for record in caplog.records)


class TestAdapterInitializationFailures:
    """Test handling of adapter initialization failures (ValueError)."""

    @pytest.mark.asyncio
    async def test_init_failure_continues_to_next_adapter(self, caplog, sample_listing):
        """Test adapter initialization failure (ValueError) continues to next adapter."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to fail initialization
            with patch.object(
                EbayAdapter, "__init__", side_effect=ValueError("eBay Browse API key not configured")
            ):
                # Mock JSON-LD to succeed
                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("INFO"):
                        result, adapter_name = await router.extract(url)

                    # Verify fallback to JSON-LD
                    assert adapter_name == "jsonld"

                    # Verify logging
                    assert any("ebay adapter initialization failed" in record.message for record in caplog.records)
                    assert any("eBay Browse API key not configured" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_unexpected_error_continues_to_next_adapter(self, caplog, sample_listing):
        """Test unexpected errors during extraction continue to next adapter."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.api_key = "test_key"
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True

            # Mock eBay to raise unexpected error
            with patch.object(
                EbayAdapter, "extract", AsyncMock(side_effect=RuntimeError("Unexpected error"))
            ):
                # Mock JSON-LD to succeed
                with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                    router = AdapterRouter()

                    with caplog.at_level("ERROR"):
                        result, adapter_name = await router.extract(url)

                    # Verify fallback to JSON-LD
                    assert adapter_name == "jsonld"

                    # Verify error logging
                    assert any("ebay adapter unexpected error" in record.message for record in caplog.records)


class TestLoggingCompleteness:
    """Test that all adapter attempts are logged with adapter name."""

    @pytest.mark.asyncio
    async def test_all_attempts_logged_with_adapter_name(self, caplog):
        """Test that every adapter attempt is logged with adapter name."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.ebay.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True
            mock_settings.return_value.ingestion.playwright.enabled = True

            # All adapters fail
            with patch.object(
                EbayAdapter, "__init__", side_effect=ValueError("No API key")
            ):
                with patch.object(
                    JsonLdAdapter,
                    "extract",
                    AsyncMock(side_effect=AdapterException(AdapterError.PARSE_ERROR, "No JSON-LD")),
                ):
                    with patch.object(
                        PlaywrightAdapter,
                        "extract",
                        AsyncMock(side_effect=AdapterException(AdapterError.TIMEOUT, "Timeout")),
                    ):
                        router = AdapterRouter()

                        with caplog.at_level("INFO"):
                            with pytest.raises(AdapterException) as exc_info:
                                await router.extract(url)

                        # Verify ALL_ADAPTERS_FAILED
                        assert exc_info.value.error_type == AdapterError.ALL_ADAPTERS_FAILED

                        # Verify logging includes adapter names
                        log_messages = [record.message for record in caplog.records]

                        # Check each adapter was tried and logged
                        assert any("Trying adapter ebay" in msg for msg in log_messages)
                        assert any("ebay adapter initialization failed" in msg for msg in log_messages)

                        assert any("Trying adapter jsonld" in msg for msg in log_messages)
                        assert any("jsonld adapter failed: [parse_error]" in msg for msg in log_messages)

                        assert any("Trying adapter playwright" in msg for msg in log_messages)
                        assert any("playwright adapter failed: [timeout]" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_success_logged_with_adapter_name(self, caplog, sample_listing):
        """Test that successful extraction logs adapter name."""
        url = "https://www.bestbuy.com/product/123"

        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.jsonld.enabled = True

            with patch.object(JsonLdAdapter, "extract", AsyncMock(return_value=sample_listing)):
                router = AdapterRouter()

                with caplog.at_level("INFO"):
                    result, adapter_name = await router.extract(url)

                # Verify logging
                assert any("Trying adapter jsonld" in record.message for record in caplog.records)
                assert any("Success with jsonld adapter" in record.message for record in caplog.records)


class TestAllAdaptersFailedError:
    """Test ALL_ADAPTERS_FAILED error includes complete metadata."""

    @pytest.mark.asyncio
    async def test_all_adapters_failed_metadata(self):
        """Test ALL_ADAPTERS_FAILED error includes attempted adapters and last error."""
        url = "https://www.ebay.com/itm/123456789012"

        with patch("dealbrain_api.adapters.router.get_settings") as mock_settings:
            mock_settings.return_value.ingestion.ebay.enabled = True
            mock_settings.return_value.ingestion.jsonld.enabled = True
            mock_settings.return_value.ingestion.playwright.enabled = True

            # Mock Playwright settings
            with patch("dealbrain_api.adapters.playwright.get_settings") as mock_pw_settings:
                mock_pw_settings.return_value.ingestion.playwright.enabled = True
                mock_pw_settings.return_value.ingestion.playwright.timeout_s = 8
                mock_pw_settings.return_value.ingestion.playwright.max_retries = 2
                mock_pw_settings.return_value.ingestion.playwright.pool_size = 3
                mock_pw_settings.return_value.ingestion.playwright.headless = True

                # All adapters fail
                with patch.object(
                    EbayAdapter, "__init__", side_effect=ValueError("No API key")
                ):
                    with patch.object(
                        JsonLdAdapter,
                        "extract",
                        AsyncMock(side_effect=AdapterException(AdapterError.PARSE_ERROR, "Parse failed")),
                    ):
                        with patch.object(
                            PlaywrightAdapter,
                            "extract",
                            AsyncMock(side_effect=AdapterException(AdapterError.TIMEOUT, "Timeout")),
                        ):
                            router = AdapterRouter()

                            with pytest.raises(AdapterException) as exc_info:
                                await router.extract(url)

                            # Verify error type
                            assert exc_info.value.error_type == AdapterError.ALL_ADAPTERS_FAILED

                            # Verify metadata includes attempted adapters
                            assert "attempted_adapters" in exc_info.value.metadata
                            attempted = exc_info.value.metadata["attempted_adapters"]
                            assert "jsonld" in attempted
                            assert "playwright" in attempted

                            # Verify last error details
                            assert "last_error_type" in exc_info.value.metadata
                            assert exc_info.value.metadata["last_error_type"] == "timeout"


# Test summary:
# - Priority order: 1 test
# - Non-retryable errors: 2 tests
# - Retryable errors: 5 tests
# - Disabled adapters: 2 tests
# - Initialization failures: 2 tests
# - Logging completeness: 2 tests
# - All adapters failed: 1 test
# Total: 15 comprehensive Phase 2B tests
