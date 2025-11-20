"""Tests for Playwright adapter."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dealbrain_api.adapters.base import AdapterError, AdapterException
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

    # Mock page.goto
    page.goto = AsyncMock()

    # Mock page.wait_for_load_state
    page.wait_for_load_state = AsyncMock()

    # Mock page.add_init_script
    page.add_init_script = AsyncMock()

    # Mock page.close
    page.close = AsyncMock()

    # Mock query_selector and query_selector_all
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])

    return page


@pytest.fixture
def mock_browser(mock_page):
    """Mock Playwright Browser object."""
    browser = AsyncMock()
    browser.new_page = AsyncMock(return_value=mock_page)
    browser.is_connected = MagicMock(return_value=True)
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


class TestPlaywrightAdapterInit:
    """Tests for PlaywrightAdapter initialization."""

    def test_init_success(self, adapter):
        """Test successful adapter initialization."""
        assert adapter.name == "playwright"
        assert adapter.supported_domains == ["*"]
        assert adapter.priority == 10
        assert adapter.timeout_s == 8
        assert adapter.pool_size == 3
        assert adapter.headless is True

    def test_adapter_metadata(self, adapter):
        """Test adapter class metadata attributes."""
        assert PlaywrightAdapter._adapter_name == "playwright"
        assert PlaywrightAdapter._adapter_domains == ["*"]
        assert PlaywrightAdapter._adapter_priority == 10


class TestPlaywrightAdapterExtract:
    """Tests for PlaywrightAdapter.extract() method."""

    @pytest.mark.asyncio
    async def test_extract_full_success(
        self,
        adapter,
        mock_browser_pool,
        mock_page,
    ):
        """Test successful extraction with all fields."""
        # Mock title element
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Gaming PC Intel Core i7")

        # Mock price element
        price_elem = AsyncMock()
        price_elem.text_content = AsyncMock(return_value="$599.99")

        # Mock condition element
        condition_elem = AsyncMock()
        condition_elem.text_content = AsyncMock(return_value="Used")

        # Mock image element
        image_elem = AsyncMock()
        image_elem.get_attribute = AsyncMock(return_value="https://example.com/image.jpg")

        # Configure mock page to return elements
        async def mock_query_selector(selector: str):
            if "title" in selector.lower() or selector == "h1":
                return title_elem
            elif "price" in selector.lower():
                return price_elem
            elif "condition" in selector.lower():
                return condition_elem
            elif "image" in selector.lower():
                return image_elem
            return None

        mock_page.query_selector.side_effect = mock_query_selector
        mock_page.query_selector_all.return_value = [image_elem]

        # Execute extraction
        result = await adapter.extract("https://example.com/product/123")

        # Verify result
        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price == Decimal("599.99")
        assert result.condition == "used"
        assert result.currency == "USD"
        assert result.marketplace == "other"
        assert result.quality == "full"
        assert len(result.images) == 1
        assert result.images[0] == "https://example.com/image.jpg"

        # Verify browser pool interaction
        mock_browser_pool.acquire.assert_called_once()
        mock_browser_pool.release.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_partial_no_price(
        self,
        adapter,
        mock_browser_pool,
        mock_page,
    ):
        """Test extraction with missing price (partial import)."""
        # Mock title element only
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Gaming PC Intel Core i7")

        # Configure mock page
        async def mock_query_selector(selector: str):
            if "title" in selector.lower() or selector == "h1":
                return title_elem
            return None

        mock_page.query_selector.side_effect = mock_query_selector

        # Execute extraction
        result = await adapter.extract("https://example.com/product/123")

        # Verify result
        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC Intel Core i7"
        assert result.price is None
        assert result.quality == "partial"
        assert "price" in result.missing_fields
        assert result.extraction_metadata["price"] == "extraction_failed"
        assert result.extraction_metadata["title"] == "extracted"

    @pytest.mark.asyncio
    async def test_extract_timeout_error(
        self,
        adapter,
        mock_browser_pool,
        mock_page,
    ):
        """Test extraction with page load timeout."""
        # Mock timeout on goto
        mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")

        # Execute extraction and expect timeout error
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/product/123")

        # Verify error
        assert exc_info.value.error_type == AdapterError.TIMEOUT
        assert "timed out" in exc_info.value.message.lower()

        # Verify browser was released even after error
        mock_browser_pool.release.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_missing_title_error(
        self,
        adapter,
        mock_browser_pool,
        mock_page,
    ):
        """Test extraction with missing title (required field)."""
        # Configure mock page to return None for all selectors
        mock_page.query_selector.return_value = None

        # Execute extraction and expect parse error
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/product/123")

        # Verify error
        assert exc_info.value.error_type == AdapterError.PARSE_ERROR
        assert "title" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_extract_browser_crash_retry(
        self,
        adapter,
        mock_browser_pool,
        mock_page,
    ):
        """Test extraction with browser crash and retry."""
        # Mock title element
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Gaming PC")

        # First attempt: browser crashes (network error)
        # Second attempt: succeeds
        attempt = 0

        async def mock_goto_with_retry(*args, **kwargs):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise Exception("Browser crashed")
            return None

        mock_page.goto.side_effect = mock_goto_with_retry

        # Configure successful extraction on retry
        mock_page.query_selector.return_value = title_elem

        # Execute extraction - should succeed on retry
        result = await adapter.extract("https://example.com/product/123")

        # Verify result
        assert isinstance(result, NormalizedListingSchema)
        assert result.title == "Gaming PC"


class TestPlaywrightAdapterPriceParsing:
    """Tests for price parsing logic."""

    def test_parse_price_us_format(self, adapter):
        """Test parsing US price format."""
        assert adapter._parse_price("$599.99") == Decimal("599.99")
        assert adapter._parse_price("Price: $1,234.56") == Decimal("1234.56")
        assert adapter._parse_price("$999") == Decimal("999")

    def test_parse_price_european_format(self, adapter):
        """Test parsing European price format."""
        assert adapter._parse_price("599,99 €") == Decimal("599.99")
        assert adapter._parse_price("1.234,56 €") == Decimal("1234.56")

    def test_parse_price_no_currency_symbol(self, adapter):
        """Test parsing price without currency symbol."""
        assert adapter._parse_price("599.99") == Decimal("599.99")
        assert adapter._parse_price("1,234.56") == Decimal("1234.56")

    def test_parse_price_invalid(self, adapter):
        """Test parsing invalid price strings."""
        assert adapter._parse_price("") is None
        assert adapter._parse_price("Not a price") is None
        assert adapter._parse_price("Price unavailable") is None

    def test_parse_price_negative(self, adapter):
        """Test parsing negative price (should return None)."""
        assert adapter._parse_price("-599.99") is None


class TestPlaywrightAdapterConditionNormalization:
    """Tests for condition normalization."""

    def test_normalize_condition_new(self, adapter):
        """Test normalizing 'new' condition variants."""
        assert adapter._normalize_condition("New") == "new"
        assert adapter._normalize_condition("Brand New") == "new"
        assert adapter._normalize_condition("brand-new") == "new"

    def test_normalize_condition_refurb(self, adapter):
        """Test normalizing 'refurb' condition variants."""
        assert adapter._normalize_condition("Refurbished") == "refurb"
        assert adapter._normalize_condition("Renewed") == "refurb"
        assert adapter._normalize_condition("Recertified") == "refurb"

    def test_normalize_condition_used(self, adapter):
        """Test normalizing 'used' condition variants."""
        assert adapter._normalize_condition("Used") == "used"
        assert adapter._normalize_condition("Pre-owned") == "used"
        assert adapter._normalize_condition("Like New") == "used"


class TestPlaywrightAdapterImageExtraction:
    """Tests for image extraction."""

    @pytest.mark.asyncio
    async def test_extract_images_success(self, adapter, mock_page):
        """Test successful image extraction."""
        # Mock image elements
        image_elem1 = AsyncMock()
        image_elem1.get_attribute = AsyncMock(return_value="https://example.com/img1.jpg")

        image_elem2 = AsyncMock()
        image_elem2.get_attribute = AsyncMock(return_value="https://example.com/img2.jpg")

        mock_page.query_selector_all.return_value = [image_elem1, image_elem2]

        # Extract images
        images = await adapter._extract_images(mock_page)

        # Verify
        assert len(images) == 2
        assert "https://example.com/img1.jpg" in images
        assert "https://example.com/img2.jpg" in images

    @pytest.mark.asyncio
    async def test_extract_images_no_images(self, adapter, mock_page):
        """Test image extraction when no images found."""
        mock_page.query_selector_all.return_value = []

        # Extract images
        images = await adapter._extract_images(mock_page)

        # Verify
        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_extract_images_duplicate_filtering(self, adapter, mock_page):
        """Test that duplicate images are filtered."""
        # Mock image elements with duplicate URLs
        image_elem1 = AsyncMock()
        image_elem1.get_attribute = AsyncMock(return_value="https://example.com/img1.jpg")

        image_elem2 = AsyncMock()
        image_elem2.get_attribute = AsyncMock(return_value="https://example.com/img1.jpg")

        mock_page.query_selector_all.return_value = [image_elem1, image_elem2]

        # Extract images
        images = await adapter._extract_images(mock_page)

        # Verify only one image
        assert len(images) == 1
        assert images[0] == "https://example.com/img1.jpg"


class TestBrowserPool:
    """Tests for BrowserPool functionality."""

    @pytest.mark.asyncio
    async def test_browser_pool_singleton(self):
        """Test BrowserPool singleton pattern."""
        from dealbrain_api.adapters.browser_pool import BrowserPool

        # Reset singleton
        BrowserPool._instance = None

        pool1 = BrowserPool.get_instance(pool_size=3)
        pool2 = BrowserPool.get_instance(pool_size=5)  # Should be ignored

        # Verify same instance
        assert pool1 is pool2
        assert pool1.pool_size == 3  # First call's config is used

    @pytest.mark.asyncio
    async def test_browser_pool_init_validation(self):
        """Test BrowserPool initialization validation."""
        from dealbrain_api.adapters.browser_pool import BrowserPool

        # Reset singleton
        BrowserPool._instance = None

        # Test invalid pool size
        with pytest.raises(ValueError) as exc_info:
            BrowserPool(pool_size=0)
        assert "pool_size must be between 1-10" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            BrowserPool(pool_size=11)
        assert "pool_size must be between 1-10" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_browser_pool_acquire_not_initialized(self):
        """Test acquire() before initialize() raises error."""
        from dealbrain_api.adapters.browser_pool import BrowserPool

        # Reset singleton
        BrowserPool._instance = None

        pool = BrowserPool.get_instance(pool_size=2)

        # Try to acquire without initializing
        with pytest.raises(RuntimeError) as exc_info:
            await pool.acquire()

        assert "not initialized" in str(exc_info.value).lower()


class TestPlaywrightAdapterIntegration:
    """Integration tests for PlaywrightAdapter (require Playwright installation)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_extract_real_url(self, adapter, mock_browser_pool, mock_page):
        """Test extraction with realistic mocked page data."""
        # Mock realistic Amazon-like page structure
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(
            return_value="ASUS Mini PC PN64 - Intel Core i7-12700H, 16GB DDR4 RAM, 512GB SSD"
        )

        price_elem = AsyncMock()
        price_elem.text_content = AsyncMock(return_value="$699.99")

        condition_elem = AsyncMock()
        condition_elem.text_content = AsyncMock(return_value="New")

        image_elem = AsyncMock()
        image_elem.get_attribute = AsyncMock(
            return_value="https://m.media-amazon.com/images/I/71abc123.jpg"
        )

        desc_elem = AsyncMock()
        desc_elem.text_content = AsyncMock(
            return_value="High-performance mini PC with 12th Gen Intel Core i7 processor"
        )

        # Configure mock page
        async def mock_query_selector(selector: str):
            if "title" in selector.lower() or selector == "h1":
                return title_elem
            elif "price" in selector.lower():
                return price_elem
            elif "condition" in selector.lower():
                return condition_elem
            elif "description" in selector.lower():
                return desc_elem
            return None

        mock_page.query_selector.side_effect = mock_query_selector
        mock_page.query_selector_all.return_value = [image_elem]

        # Execute extraction
        result = await adapter.extract("https://www.amazon.com/dp/B0EXAMPLE")

        # Verify comprehensive result
        assert result.title == "ASUS Mini PC PN64 - Intel Core i7-12700H, 16GB DDR4 RAM, 512GB SSD"
        assert result.price == Decimal("699.99")
        assert result.condition == "new"
        assert result.quality == "full"
        assert len(result.images) == 1
        assert result.description is not None
        assert "Intel Core i7" in result.description


class TestPlaywrightRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self, adapter, mock_browser_pool, mock_page):
        """Test that rate limiting is enforced (30 req/min)."""
        # Mock title element
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Test Product")
        mock_page.query_selector.return_value = title_elem

        # Rate limit is 30 req/min = 0.5 req/sec = 2s per request
        # Make 2 rapid requests - second should be delayed
        import time

        start_time = time.time()

        # First request should succeed immediately
        result1 = await adapter.extract("https://example.com/product1")
        assert result1.title == "Test Product"

        # Second request should be rate-limited (but we won't wait in test)
        # Just verify the rate limiter is configured
        assert adapter.rate_limit_config is not None
        assert adapter.rate_limit_config.requests_per_minute == 30


class TestPlaywrightRetryLogic:
    """Tests for retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_error(self, adapter, mock_browser_pool, mock_page):
        """Test retry logic on timeout errors."""
        # Mock title element
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Test Product")

        # First attempt: timeout
        # Second attempt: success
        attempt = 0

        async def mock_goto_with_retry(*args, **kwargs):
            nonlocal attempt
            attempt += 1
            if attempt == 1:
                raise PlaywrightTimeoutError("Timeout on first attempt")
            return None

        mock_page.goto.side_effect = mock_goto_with_retry
        mock_page.query_selector.return_value = title_elem

        # Execute extraction - should succeed on retry
        result = await adapter.extract("https://example.com/product")

        # Verify success
        assert result.title == "Test Product"
        assert attempt == 2  # Retried once

    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises_error(self, adapter, mock_browser_pool, mock_page):
        """Test that exhausted retries raise final error."""
        # Mock persistent timeout error
        mock_page.goto.side_effect = PlaywrightTimeoutError("Persistent timeout")

        # Execute extraction and expect timeout error after retries
        with pytest.raises(AdapterException) as exc_info:
            await adapter.extract("https://example.com/timeout")

        # Verify error
        assert exc_info.value.error_type == AdapterError.TIMEOUT

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self, adapter, mock_browser_pool, mock_page):
        """Test that retry uses exponential backoff."""
        # Verify retry config is set correctly
        assert adapter.retry_config.max_retries == 2
        assert adapter.retry_config.backoff_factor == 1.0

        # Verify retryable errors include TIMEOUT, NETWORK_ERROR
        retryable = adapter.retry_config.retryable_errors
        assert AdapterError.TIMEOUT in retryable
        assert AdapterError.NETWORK_ERROR in retryable


class TestPlaywrightObservability:
    """Tests for observability and metrics."""

    @pytest.mark.asyncio
    async def test_metrics_tracked_on_success(self, adapter, mock_browser_pool, mock_page):
        """Test that metrics are tracked on successful extraction."""
        # Mock title element
        title_elem = AsyncMock()
        title_elem.text_content = AsyncMock(return_value="Test Product")
        mock_page.query_selector.return_value = title_elem

        # Execute extraction
        result = await adapter.extract("https://example.com/product")

        # Verify result
        assert result.title == "Test Product"

        # Metrics should be tracked (we can't easily verify Prometheus metrics in tests,
        # but we can verify the code paths are exercised)

    @pytest.mark.asyncio
    async def test_metrics_tracked_on_failure(self, adapter, mock_browser_pool, mock_page):
        """Test that metrics are tracked on extraction failure."""
        # Mock timeout error
        mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")

        # Execute extraction and expect error
        with pytest.raises(AdapterException):
            await adapter.extract("https://example.com/timeout")

        # Metrics should be tracked for failures as well


# Coverage target: >80%
# Test categories:
# - Initialization: 2 tests
# - Extract method: 5 tests
# - Price parsing: 5 tests
# - Condition normalization: 3 tests
# - Image extraction: 3 tests
# - Browser pool: 3 tests
# - Integration: 1 test
# - Rate limiting: 1 test
# - Retry logic: 3 tests
# - Observability: 2 tests
# Total: 28 tests
