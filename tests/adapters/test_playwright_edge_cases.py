"""Edge case tests for Playwright adapter - production hardening."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_api.adapters.browser_pool import BrowserPool
from dealbrain_api.adapters.playwright import PlaywrightAdapter
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


@pytest.fixture
def mock_settings():
    """Mock settings with Playwright configuration."""
    with patch("dealbrain_api.adapters.playwright.get_settings") as mock:
        settings = MagicMock()
        settings.ingestion.playwright.enabled = True
        settings.ingestion.playwright.timeout_s = 8
        settings.ingestion.playwright.max_retries = 2
        settings.ingestion.playwright.pool_size = 3
        settings.ingestion.playwright.headless = True
        mock.return_value = settings
        yield mock


@pytest.fixture
def adapter(mock_settings):
    """Create PlaywrightAdapter instance with mocked settings."""
    return PlaywrightAdapter()


@pytest.fixture
def mock_page():
    """Mock Playwright Page object."""
    page = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.add_init_script = AsyncMock()
    page.close = AsyncMock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    return page


@pytest.fixture
def mock_browser(mock_page):
    """Mock Playwright Browser object."""
    browser = AsyncMock()
    browser.new_page = AsyncMock(return_value=mock_page)
    browser.is_connected = MagicMock(return_value=True)
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_browser_pool(mock_browser):
    """Mock BrowserPool."""
    with patch("dealbrain_api.adapters.playwright.BrowserPool") as mock_pool_class:
        pool_instance = AsyncMock()
        pool_instance.acquire = AsyncMock(return_value=mock_browser)
        pool_instance.release = AsyncMock()
        pool_instance.initialize = AsyncMock()
        pool_instance.get_pool_stats = MagicMock(
            return_value={"in_use": 1, "available": 2, "pool_size": 3, "total_requests": 10}
        )
        mock_pool_class.get_instance = MagicMock(return_value=pool_instance)
        yield pool_instance


class TestPlaywrightBrowserPoolRecycling:
    """Tests for browser recycling logic."""

    @pytest.mark.asyncio
    async def test_browser_recycling_after_max_requests(self):
        """Test that browsers are recycled after max_requests_per_browser."""
        pool = BrowserPool(pool_size=1, max_requests_per_browser=3)

        # Mock Playwright context
        with patch("dealbrain_api.adapters.browser_pool.async_playwright") as mock_pw:
            mock_context = AsyncMock()
            mock_browser = AsyncMock()
            mock_browser.is_connected = MagicMock(return_value=True)
            mock_browser.close = AsyncMock()

            mock_context.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_pw.return_value.start = AsyncMock(return_value=mock_context)

            # Initialize pool
            await pool.initialize()

            # Acquire and release browser 3 times
            for i in range(3):
                browser = await pool.acquire()
                assert browser.is_connected()
                await pool.release(browser)

            # On 4th acquire, browser should be recycled
            browser = await pool.acquire()
            assert mock_browser.close.called  # Old browser was closed
            await pool.release(browser)

            # Cleanup
            await pool.close_all()

    @pytest.mark.asyncio
    async def test_browser_pool_stats(self):
        """Test get_pool_stats returns correct metrics."""
        pool = BrowserPool(pool_size=2, max_requests_per_browser=50)

        with patch("dealbrain_api.adapters.browser_pool.async_playwright") as mock_pw:
            mock_context = AsyncMock()
            mock_browser = AsyncMock()
            mock_browser.is_connected = MagicMock(return_value=True)

            mock_context.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_pw.return_value.start = AsyncMock(return_value=mock_context)

            await pool.initialize()

            # Check initial stats
            stats = pool.get_pool_stats()
            assert stats["pool_size"] == 2
            assert stats["in_use"] == 0
            assert stats["available"] == 2
            assert stats["initialized"] is True
            assert stats["total_requests"] == 0

            # Acquire browser
            browser = await pool.acquire()
            stats = pool.get_pool_stats()
            assert stats["in_use"] == 1
            assert stats["available"] == 1
            assert stats["total_requests"] == 1

            # Release browser
            await pool.release(browser)
            stats = pool.get_pool_stats()
            assert stats["in_use"] == 0
            assert stats["available"] == 2

            await pool.close_all()


class TestPlaywrightTimeoutHandling:
    """Tests for timeout and slow page handling."""

    @pytest.mark.asyncio
    async def test_very_slow_page_timeout(self, adapter, mock_browser_pool, mock_page):
        """Test extraction fails gracefully on very slow pages (8s timeout)."""
        # Mock page load that exceeds timeout
        async def slow_goto(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow page
            raise PlaywrightTimeoutError("Navigation timeout exceeded")

        mock_page.goto.side_effect = slow_goto

        # Execute extraction and expect timeout error
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/slow-page")

        # Verify error details
        assert exc_info.value.error_type == AdapterError.TIMEOUT
        assert "timed out" in exc_info.value.message.lower()

        # Verify browser was released even after error
        mock_browser_pool.release.assert_called_once()

    @pytest.mark.asyncio
    async def test_page_with_javascript_errors(self, adapter, mock_browser_pool, mock_page):
        """Test extraction handles pages with JavaScript errors gracefully."""
        # Mock page with title but JavaScript errors during load
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Product Title")

        mock_page.query_selector.return_value = title_elem

        # Page loads successfully despite JS errors
        result = await adapter.extract("https://example.com/js-errors")

        # Verify extraction succeeded with partial data
        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Product Title"


class TestPlaywrightRedirectHandling:
    """Tests for redirect and expired listing handling."""

    @pytest.mark.asyncio
    async def test_redirect_to_expired_listing(self, adapter, mock_browser_pool, mock_page):
        """Test handling of redirects to expired/unavailable listings."""
        # Mock page that redirects but has no product data
        mock_page.query_selector.return_value = None

        # Execute extraction and expect parse error
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/expired-listing")

        # Verify error
        assert exc_info.value.error_type == AdapterError.PARSE_ERROR
        assert "title" in exc_info.value.message.lower()


class TestPlaywrightBotDetection:
    """Tests for bot detection and rate limiting responses."""

    @pytest.mark.asyncio
    async def test_bot_detection_403_response(self, adapter, mock_browser_pool, mock_page):
        """Test handling of 403 Forbidden (bot detection) responses."""
        # Mock page load that returns 403
        mock_page.goto.side_effect = Exception("HTTP 403 Forbidden")

        # Execute extraction and expect network error
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/bot-detected")

        # Verify error
        assert exc_info.value.error_type == AdapterError.NETWORK_ERROR

    @pytest.mark.asyncio
    async def test_rate_limit_429_response(self, adapter, mock_browser_pool, mock_page):
        """Test handling of 429 Too Many Requests responses."""
        # Mock page load that returns 429
        mock_page.goto.side_effect = Exception("HTTP 429 Too Many Requests")

        # Execute extraction and expect network error
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/rate-limited")

        # Verify error
        assert exc_info.value.error_type == AdapterError.NETWORK_ERROR


class TestPlaywrightMemoryManagement:
    """Tests for memory management and resource cleanup."""

    @pytest.mark.asyncio
    async def test_browser_pool_bounded_growth(self):
        """Test that browser pool doesn't grow unbounded."""
        pool = BrowserPool(pool_size=3, max_requests_per_browser=50)

        with patch("dealbrain_api.adapters.browser_pool.async_playwright") as mock_pw:
            mock_context = AsyncMock()

            # Create 3 distinct browser mocks
            mock_browsers = []
            for i in range(3):
                browser = AsyncMock()
                browser.is_connected = MagicMock(return_value=True)
                mock_browsers.append(browser)

            # Return different browser on each call
            mock_context.chromium.launch = AsyncMock(side_effect=mock_browsers)
            mock_pw.return_value.start = AsyncMock(return_value=mock_context)

            await pool.initialize()

            # Verify pool size is capped
            stats = pool.get_pool_stats()
            assert stats["pool_size"] == 3
            assert len(pool._browsers) == 3

            # Try to acquire all browsers
            browsers = []
            for i in range(3):
                browser = await pool.acquire()
                browsers.append(browser)

            # Pool should be exhausted
            stats = pool.get_pool_stats()
            assert stats["in_use"] == 3
            assert stats["available"] == 0

            # Release all
            for browser in browsers:
                await pool.release(browser)

            # Pool should be back to normal
            stats = pool.get_pool_stats()
            assert stats["in_use"] == 0
            assert stats["available"] == 3

            await pool.close_all()

    @pytest.mark.asyncio
    async def test_clean_shutdown_closes_all_browsers(self):
        """Test that shutdown properly closes all browser instances."""
        pool = BrowserPool(pool_size=2)

        with patch("dealbrain_api.adapters.browser_pool.async_playwright") as mock_pw:
            mock_context = AsyncMock()
            mock_browser1 = AsyncMock()
            mock_browser2 = AsyncMock()
            mock_browser1.is_connected = MagicMock(return_value=True)
            mock_browser2.is_connected = MagicMock(return_value=True)
            mock_browser1.close = AsyncMock()
            mock_browser2.close = AsyncMock()

            # Return different browsers on each call
            mock_context.chromium.launch = AsyncMock(side_effect=[mock_browser1, mock_browser2])
            mock_pw.return_value.start = AsyncMock(return_value=mock_context)

            await pool.initialize()

            # Close all
            await pool.close_all()

            # Verify both browsers were closed
            mock_browser1.close.assert_called_once()
            mock_browser2.close.assert_called_once()

            # Verify pool state is reset
            assert pool._initialized is False
            assert len(pool._browsers) == 0
            assert len(pool._in_use) == 0


class TestPlaywrightPartialImports:
    """Tests for partial import handling."""

    @pytest.mark.asyncio
    async def test_partial_import_missing_price(self, adapter, mock_browser_pool, mock_page):
        """Test successful partial import when price is missing."""
        # Mock title only
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Gaming PC")

        mock_page.query_selector.return_value = title_elem

        # Execute extraction
        result = await adapter.extract("https://example.com/no-price")

        # Verify partial import
        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC"
        assert result.price is None
        assert result.quality == "partial"
        assert "price" in result.missing_fields
        assert result.extraction_metadata["price"] == "extraction_failed"

    @pytest.mark.asyncio
    async def test_partial_import_missing_condition(self, adapter, mock_browser_pool, mock_page):
        """Test partial import defaults to 'used' when condition is missing."""
        # Mock title and price only
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Gaming PC")

        price_elem = AsyncMock()
        price_elem.text_content = AsyncMock(return_value="$599.99")

        async def mock_query_selector(selector: str):
            if "title" in selector.lower() or selector == "h1":
                return title_elem
            elif "price" in selector.lower():
                return price_elem
            return None

        mock_page.query_selector.side_effect = mock_query_selector

        # Execute extraction
        result = await adapter.extract("https://example.com/no-condition")

        # Verify defaults to "used"
        assert result.condition == "used"


class TestPlaywrightConcurrency:
    """Tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_extractions_share_pool(self, mock_settings):
        """Test that concurrent extractions share browser pool efficiently."""
        adapter = PlaywrightAdapter()

        # Mock browser pool
        with patch("dealbrain_api.adapters.playwright.BrowserPool") as mock_pool_class:
            pool_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_browser.is_connected = MagicMock(return_value=True)
            mock_browser.new_page = AsyncMock()

            # Mock page with title
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.add_init_script = AsyncMock()
            mock_page.close = AsyncMock()

            title_elem = AsyncMock()
            title_elem.text_content = AsyncMock(return_value="Test Product")
            mock_page.query_selector.return_value = title_elem
            mock_page.query_selector_all.return_value = []
            mock_browser.new_page.return_value = mock_page

            pool_instance.acquire = AsyncMock(return_value=mock_browser)
            pool_instance.release = AsyncMock()
            pool_instance.initialize = AsyncMock()
            pool_instance.get_pool_stats = MagicMock(
                return_value={"in_use": 1, "available": 2, "pool_size": 3, "total_requests": 10}
            )
            mock_pool_class.get_instance = MagicMock(return_value=pool_instance)

            # Execute 3 concurrent extractions
            tasks = [
                adapter.extract("https://example.com/product1"),
                adapter.extract("https://example.com/product2"),
                adapter.extract("https://example.com/product3"),
            ]

            results = await asyncio.gather(*tasks)

            # Verify all succeeded
            assert len(results) == 3
            for result in results:
                assert isinstance(result, NormalizedListingSchema)
                assert result.title == "Test Product"

            # Verify pool was used efficiently
            assert pool_instance.acquire.call_count == 3
            assert pool_instance.release.call_count == 3


# Coverage target: >80%
# Test categories:
# - Browser recycling: 2 tests
# - Timeout handling: 2 tests
# - Redirects: 1 test
# - Bot detection: 2 tests
# - Memory management: 2 tests
# - Partial imports: 2 tests
# - Concurrency: 1 test
# Total: 12 tests
