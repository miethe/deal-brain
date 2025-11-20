"""Playwright adapter for browser-based listing extraction."""

from __future__ import annotations

import asyncio
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from dealbrain_api.adapters.base import AdapterError, AdapterException, BaseAdapter
from dealbrain_api.adapters.browser_pool import BrowserPool
from dealbrain_api.settings import get_settings
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from playwright.async_api import Browser, Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class PlaywrightAdapter(BaseAdapter):
    """
    Playwright adapter for extracting listing data from JavaScript-rendered pages.

    This adapter uses headless Chromium via Playwright to extract data from
    marketplace listings that require browser rendering (especially Amazon).
    It serves as the lowest-priority fallback when API-based and JSON-LD
    adapters fail.

    Use Cases:
    ---------
    - Amazon product pages (heavy JavaScript, no JSON-LD)
    - Dynamic marketplace listings
    - Pages with client-side rendering
    - Fallback when structured data is unavailable

    Architecture:
    ------------
    - Priority: 10 (lowest, fallback adapter)
    - Supported domains: ["*"] (wildcard - all domains)
    - Browser pool: Reuses 2-3 Chromium instances for performance
    - Timeout: 8s default (configurable)
    - Extraction strategy: CSS selectors + JavaScript evaluation

    Anti-Detection Features:
    ------------------------
    - Realistic User-Agent headers
    - Standard viewport (1920x1080)
    - Headless mode (configurable)
    - Disabled automation signals (--disable-blink-features=AutomationControlled)
    - navigator.webdriver override via init script

    Extraction Strategy:
    -------------------
    1. Wait for network idle (ensures page fully loaded)
    2. Try CSS selectors for common fields:
       - Title: h1, h2, .title, .product-title, #title
       - Price: .price, .current-price, [data-price], .a-price
       - Condition: .condition, .item-condition
    3. Fallback to JavaScript evaluation if selectors fail
    4. Handle missing fields gracefully (partial imports)
    5. Track extraction metadata for manual population

    Performance:
    -----------
    - Browser pool amortizes launch cost (~1-2s per browser)
    - Page load + extraction: ~3-8s per URL
    - Network idle wait: ~1-3s typical
    - Target latency: <10s per request

    Error Handling:
    --------------
    - TIMEOUT: Page load exceeds configured timeout (retryable)
    - PARSE_ERROR: Failed to extract any meaningful data (not retryable)
    - NETWORK_ERROR: Browser crash or connection failure (retryable)
    - Partial imports: Missing price creates "partial" quality listing

    Example Usage:
    -------------
    ```python
    adapter = PlaywrightAdapter()
    listing = await adapter.extract("https://www.amazon.com/dp/B08N5WRWNW")
    # Returns NormalizedListingSchema with extracted data
    ```

    Settings Configuration:
    ----------------------
    ```python
    # In settings.py (IngestionSettings)
    playwright: PlaywrightAdapterConfig = Field(
        default_factory=lambda: PlaywrightAdapterConfig(
            enabled=True,
            timeout_s=8,
            max_retries=2,
            pool_size=3,
            headless=True,
        )
    )
    ```
    """

    # Class attributes for router metadata access
    _adapter_name = "playwright"
    _adapter_domains = ["*"]  # Wildcard - supports all domains
    _adapter_priority = 10  # Lowest priority (fallback)

    def __init__(self) -> None:
        """
        Initialize Playwright adapter.

        Loads configuration from settings and initializes browser pool.
        The browser pool is lazily initialized on first use to avoid
        startup cost if adapter is never used.
        """
        settings = get_settings()

        # Initialize base adapter with Playwright-specific configuration
        super().__init__(
            name="playwright",
            supported_domains=["*"],  # Wildcard - all domains
            priority=10,  # Lowest priority (fallback)
            timeout_s=settings.ingestion.playwright.timeout_s,
            max_retries=settings.ingestion.playwright.max_retries,
            requests_per_minute=30,  # Conservative rate limit for browser automation
        )

        # Playwright-specific configuration
        self.pool_size = settings.ingestion.playwright.pool_size
        self.headless = settings.ingestion.playwright.headless
        self._browser_pool: BrowserPool | None = None

        logger.info(
            f"Initialized PlaywrightAdapter with timeout={self.timeout_s}s, "
            f"retries={self.retry_config.max_retries}, "
            f"pool_size={self.pool_size}, "
            f"headless={self.headless}"
        )

    async def _ensure_browser_pool(self) -> BrowserPool:
        """
        Ensure browser pool is initialized.

        Lazy initialization of browser pool to avoid startup cost if adapter
        is never used. Uses singleton pattern to share pool across all requests.

        Returns:
            Initialized BrowserPool instance
        """
        if self._browser_pool is None:
            logger.info("Initializing browser pool for PlaywrightAdapter...")
            self._browser_pool = BrowserPool.get_instance(
                pool_size=self.pool_size,
                headless=self.headless,
                timeout_ms=self.timeout_s * 1000,
            )
            await self._browser_pool.initialize()
            logger.info("Browser pool initialized successfully")

        return self._browser_pool

    async def extract(self, url: str) -> NormalizedListingSchema:
        """
        Extract listing data from URL using Playwright.

        This is the main entry point that orchestrates the extraction workflow:
        1. Validate URL format
        2. Acquire browser from pool
        3. Create new page with anti-detection settings
        4. Load page and wait for network idle
        5. Extract data using CSS selectors and JavaScript
        6. Map to NormalizedListingSchema
        7. Release browser back to pool

        Args:
            url: URL to extract listing data from

        Returns:
            NormalizedListingSchema with normalized listing data

        Raises:
            AdapterException: If extraction fails at any step
        """
        logger.info(f"Extracting listing data from URL using Playwright: {url}")

        # Ensure browser pool is initialized
        pool = await self._ensure_browser_pool()

        # Acquire browser from pool
        browser = await pool.acquire()

        try:
            # Check rate limit before making request
            await self._check_rate_limit()

            # Execute extraction with retry logic
            normalized = await self.retry_config.execute_with_retry(
                self._extract_with_browser,
                browser,
                url,
            )

            logger.info(f"Successfully extracted listing: {normalized.title}")
            return normalized

        finally:
            # Always release browser back to pool
            await pool.release(browser)

    async def _extract_with_browser(
        self,
        browser: Browser,
        url: str,
    ) -> NormalizedListingSchema:
        """
        Extract data using provided browser instance.

        This method creates a new page, configures anti-detection settings,
        loads the URL, and extracts data using CSS selectors and JavaScript.

        Args:
            browser: Browser instance from pool
            url: URL to extract data from

        Returns:
            NormalizedListingSchema with extracted data

        Raises:
            AdapterException: On timeout, parse error, or network error
        """
        page: Page | None = None

        try:
            # Create new page with anti-detection settings
            page = await browser.new_page(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            # Override navigator.webdriver to avoid detection
            await page.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            )

            logger.debug(f"Loading page: {url}")

            # Load page and wait for network idle
            try:
                await page.goto(url, timeout=self.timeout_s * 1000, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=self.timeout_s * 1000)
                logger.debug("Page loaded successfully")

            except PlaywrightTimeoutError as e:
                raise AdapterException(
                    AdapterError.TIMEOUT,
                    f"Page load timed out after {self.timeout_s}s",
                    metadata={"url": url, "timeout_s": self.timeout_s},
                ) from e

            # Extract data from page
            extracted_data = await self._extract_data_from_page(page, url)

            # Validate extracted data
            self._validate_response(extracted_data)

            # Map to normalized schema
            normalized = self._map_to_schema(extracted_data)

            return normalized

        except Exception as e:
            if isinstance(e, AdapterException):
                raise
            raise AdapterException(
                AdapterError.NETWORK_ERROR,
                f"Unexpected error during Playwright extraction: {e}",
                metadata={"url": url},
            ) from e

        finally:
            # Always close page to free resources
            if page:
                await page.close()

    async def _extract_data_from_page(self, page: Page, url: str) -> dict[str, Any]:
        """
        Extract listing data from page using CSS selectors and JavaScript.

        Tries multiple CSS selectors for each field to handle different site layouts.
        Falls back to JavaScript evaluation if selectors fail.

        Args:
            page: Playwright Page instance
            url: Original URL (for logging)

        Returns:
            Dictionary with extracted data

        Raises:
            AdapterException: If title extraction fails (required field)
        """
        logger.debug("Extracting data from page...")

        extracted: dict[str, Any] = {}

        # Extract title (required)
        title = await self._extract_title(page)
        if not title:
            raise AdapterException(
                AdapterError.PARSE_ERROR,
                "Failed to extract title from page",
                metadata={"url": url},
            )
        extracted["title"] = title

        # Extract price (optional - may be None for partial imports)
        price = await self._extract_price(page)
        if price:
            extracted["price"] = price
        else:
            logger.warning(f"No price found on page - will create partial import: {url}")

        # Extract condition (optional)
        condition = await self._extract_condition(page)
        if condition:
            extracted["condition"] = condition
        else:
            # Default to "used" if not found
            extracted["condition"] = str(Condition.USED.value)

        # Extract images (optional)
        images = await self._extract_images(page)
        extracted["images"] = images

        # Extract description (optional)
        description = await self._extract_description(page)
        if description:
            extracted["description"] = description

        # Set marketplace to "other" (generic)
        extracted["marketplace"] = "other"
        extracted["currency"] = "USD"

        logger.debug(
            f"Extracted data: title={bool(title)}, price={bool(price)}, "
            f"condition={bool(condition)}, images={len(images)}"
        )

        return extracted

    async def _extract_title(self, page: Page) -> str | None:
        """
        Extract product title from page.

        Tries multiple CSS selectors in priority order:
        1. #title (Amazon)
        2. h1 (common pattern)
        3. .product-title, .title
        4. h2 (fallback)

        Args:
            page: Playwright Page instance

        Returns:
            Product title or None if not found
        """
        selectors = [
            "#title",
            "h1#title",
            "h1.product-title",
            "h1",
            ".product-title",
            ".title",
            "h2.product-title",
            "h2",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and text.strip():
                        title = text.strip()
                        logger.debug(f"Extracted title from selector '{selector}': {title[:50]}...")
                        return title
            except Exception as e:
                logger.debug(f"Failed to extract title with selector '{selector}': {e}")
                continue

        logger.warning("Failed to extract title from any selector")
        return None

    async def _extract_price(self, page: Page) -> Decimal | None:
        """
        Extract product price from page.

        Tries multiple CSS selectors and patterns:
        1. .a-price .a-offscreen (Amazon)
        2. .price, .current-price
        3. [data-price], [data-testid*="price"]
        4. JavaScript evaluation of common price patterns

        Parses values like:
        - "$599.99" -> 599.99
        - "599,99 €" -> 599.99
        - "Price: $1,234.56" -> 1234.56

        Args:
            page: Playwright Page instance

        Returns:
            Decimal price or None if not found
        """
        selectors = [
            ".a-price .a-offscreen",
            ".a-price-whole",
            ".price",
            ".current-price",
            "[data-price]",
            "[data-testid*='price']",
            "span.price",
            "div.price",
        ]

        for selector in selectors:
            try:
                # Try text content first
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        price = self._parse_price(text)
                        if price:
                            logger.debug(f"Extracted price from selector '{selector}': {price}")
                            return price

                # Try data-price attribute
                if "[data-price]" in selector:
                    attr_value = await element.get_attribute("data-price")
                    if attr_value:
                        price = self._parse_price(attr_value)
                        if price:
                            logger.debug(f"Extracted price from data-price attribute: {price}")
                            return price

            except Exception as e:
                logger.debug(f"Failed to extract price with selector '{selector}': {e}")
                continue

        logger.warning("Failed to extract price from any selector")
        return None

    def _parse_price(self, text: str) -> Decimal | None:
        """
        Parse price from text string.

        Handles various formats:
        - "$599.99" -> 599.99
        - "599,99 €" -> 599.99
        - "Price: $1,234.56" -> 1234.56
        - "1.234,56" -> 1234.56 (European format)

        Args:
            text: Text containing price

        Returns:
            Decimal price or None if parsing fails
        """
        if not text:
            return None

        # Remove common currency symbols and words
        text = text.strip()

        # Check for negative price (reject it)
        if text.startswith("-") or text.startswith("−"):
            return None

        text = re.sub(r"(?i)(price|usd|\$|€|£|¥|₹|from|save|off|sale)", "", text)

        # Extract first number pattern (handles both US and European formats)
        # Match patterns like: 1,234.56 or 1.234,56 or 1234.56
        pattern = r"(\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})?)"
        match = re.search(pattern, text)

        if not match:
            return None

        price_str = match.group(1)

        # Normalize to US format (dots for decimals)
        # If there are both commas and dots, last one is decimal separator
        if "," in price_str and "." in price_str:
            if price_str.rindex(",") > price_str.rindex("."):
                # European format: 1.234,56 -> 1234.56
                price_str = price_str.replace(".", "").replace(",", ".")
            else:
                # US format: 1,234.56 -> 1234.56
                price_str = price_str.replace(",", "")
        elif "," in price_str:
            # Check if comma is thousand separator or decimal separator
            if price_str.count(",") == 1 and len(price_str.split(",")[1]) == 2:
                # Likely decimal: 599,99 -> 599.99
                price_str = price_str.replace(",", ".")
            else:
                # Thousand separator: 1,234 -> 1234
                price_str = price_str.replace(",", "")

        try:
            price = Decimal(price_str)
            if price > 0:
                return price
        except (InvalidOperation, ValueError) as e:
            logger.debug(f"Failed to parse price '{price_str}': {e}")

        return None

    async def _extract_condition(self, page: Page) -> str | None:
        """
        Extract product condition from page.

        Tries multiple CSS selectors:
        1. .condition
        2. .item-condition
        3. [data-testid*="condition"]

        Normalizes to Condition enum values:
        - "new", "brand new" -> "new"
        - "refurbished", "renewed" -> "refurb"
        - "used", "pre-owned" -> "used"

        Args:
            page: Playwright Page instance

        Returns:
            Normalized condition string or None if not found
        """
        selectors = [
            ".condition",
            ".item-condition",
            "[data-testid*='condition']",
            "span.condition",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        condition = self._normalize_condition(text.strip())
                        logger.debug(f"Extracted condition from selector '{selector}': {condition}")
                        return condition
            except Exception as e:
                logger.debug(f"Failed to extract condition with selector '{selector}': {e}")
                continue

        return None

    def _normalize_condition(self, condition_raw: str) -> str:
        """
        Normalize condition string to Condition enum value.

        Args:
            condition_raw: Raw condition string from page

        Returns:
            Normalized condition string (new|refurb|used)
        """
        condition_lower = condition_raw.lower()

        # Check refurb first (before new) to avoid "renewed" matching "new"
        if any(
            keyword in condition_lower for keyword in ["refurb", "renewed", "refurbished", "recertified"]
        ):
            return str(Condition.REFURB.value)
        elif "brand new" in condition_lower or "brand-new" in condition_lower:
            # Check for "brand new" before plain "new"
            return str(Condition.NEW.value)
        elif condition_lower == "new":
            # Only match exact "new" (not "like new", "renewed", etc.)
            return str(Condition.NEW.value)
        else:
            # Default to "used" for any other condition including "like new"
            return str(Condition.USED.value)

    async def _extract_images(self, page: Page) -> list[str]:
        """
        Extract product images from page.

        Tries multiple patterns:
        1. #landingImage (Amazon main image)
        2. .product-image img
        3. [data-testid*="image"] img
        4. img elements with product/item in class or id

        Args:
            page: Playwright Page instance

        Returns:
            List of image URLs (may be empty)
        """
        images: list[str] = []

        selectors = [
            "#landingImage",
            ".product-image img",
            "[data-testid*='image'] img",
            "img.product-image",
            "img[itemprop='image']",
        ]

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    src = await element.get_attribute("src")
                    if src and src.startswith("http"):
                        if src not in images:
                            images.append(src)

            except Exception as e:
                logger.debug(f"Failed to extract images with selector '{selector}': {e}")
                continue

        logger.debug(f"Extracted {len(images)} images")
        return images

    async def _extract_description(self, page: Page) -> str | None:
        """
        Extract product description from page.

        Tries multiple patterns:
        1. #productDescription
        2. .product-description
        3. [data-testid*="description"]

        Args:
            page: Playwright Page instance

        Returns:
            Product description or None if not found
        """
        selectors = [
            "#productDescription",
            ".product-description",
            "[data-testid*='description']",
            "div.description",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and len(text.strip()) > 10:
                        description = text.strip()
                        logger.debug(f"Extracted description from selector '{selector}': {len(description)} chars")
                        return description
            except Exception as e:
                logger.debug(f"Failed to extract description with selector '{selector}': {e}")
                continue

        return None

    def _map_to_schema(self, extracted_data: dict[str, Any]) -> NormalizedListingSchema:
        """
        Map extracted data to NormalizedListingSchema.

        Builds normalized schema from extracted fields. Supports partial imports
        when price is unavailable.

        Args:
            extracted_data: Dictionary with extracted data

        Returns:
            NormalizedListingSchema with mapped data

        Raises:
            AdapterException: If required fields are missing (title required, price optional)
        """
        try:
            title = extracted_data.get("title", "")
            if not title:
                raise AdapterException(
                    AdapterError.INVALID_SCHEMA,
                    "Missing required field: title",
                    metadata={"extracted_data": extracted_data},
                )

            # Extract price (optional - may be None for partial imports)
            price = extracted_data.get("price")

            # Determine data quality and build extraction metadata
            quality = "partial" if price is None else "full"
            missing_fields = ["price"] if price is None else []

            # Track what was successfully extracted
            extraction_metadata: dict[str, str] = {}
            extracted_fields = {
                "title": title,
                "condition": extracted_data.get("condition"),
                "marketplace": extracted_data.get("marketplace"),
                "currency": extracted_data.get("currency"),
            }

            if price is not None:
                extracted_fields["price"] = str(price)
            if extracted_data.get("images"):
                extracted_fields["images"] = ",".join(extracted_data["images"])
            if extracted_data.get("description"):
                extracted_fields["description"] = extracted_data["description"]

            # Mark all extracted fields
            for field_name, field_value in extracted_fields.items():
                if field_value:
                    extraction_metadata[field_name] = "extracted"

            # Mark price as extraction_failed if missing
            if price is None:
                extraction_metadata["price"] = "extraction_failed"

            # Build normalized schema
            return NormalizedListingSchema(
                title=title,
                price=price,
                currency=extracted_data.get("currency", "USD"),
                condition=extracted_data.get("condition", str(Condition.USED.value)),
                images=extracted_data.get("images", []),
                seller=extracted_data.get("seller"),
                marketplace=extracted_data.get("marketplace", "other"),
                vendor_item_id=extracted_data.get("vendor_item_id"),
                description=extracted_data.get("description"),
                cpu_model=extracted_data.get("cpu_model"),
                ram_gb=extracted_data.get("ram_gb"),
                storage_gb=extracted_data.get("storage_gb"),
                quality=quality,
                extraction_metadata=extraction_metadata,
                missing_fields=missing_fields,
            )

        except Exception as e:
            if isinstance(e, AdapterException):
                raise
            raise AdapterException(
                AdapterError.INVALID_SCHEMA,
                f"Failed to map extracted data to schema: {e}",
                metadata={"extracted_data": extracted_data},
            ) from e


__all__ = ["PlaywrightAdapter"]
