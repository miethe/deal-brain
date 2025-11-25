"""Browser pool for managing reusable Playwright browser instances."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from playwright.async_api import Browser, async_playwright

logger = logging.getLogger(__name__)


class BrowserPool:
    """
    Singleton browser pool for application-wide browser reuse.

    Maintains a pool of 2-3 reusable Chromium browser instances to amortize
    the high startup cost (~1-2s per browser launch). This is critical for
    achieving <10s latency per Playwright request.

    Architecture:
    ------------
    - Singleton pattern: One pool per application lifecycle
    - Async context manager: Proper cleanup on shutdown
    - Auto-restart: Crashed browsers are automatically restarted
    - Thread-safe: Uses asyncio.Lock for concurrent access

    Usage:
    -----
    ```python
    pool = BrowserPool.get_instance(pool_size=3)
    await pool.initialize()

    # Acquire browser for use
    browser = await pool.acquire()
    try:
        page = await browser.new_page()
        await page.goto("https://example.com")
        # ... use page ...
    finally:
        await pool.release(browser)

    # Cleanup on shutdown
    await pool.close_all()
    ```

    Performance:
    -----------
    - Browser launch: ~1-2s (amortized across pool)
    - Page creation: ~50-100ms (per request)
    - Pool reuse: ~10-20ms overhead (lock acquisition)
    - Target latency: <10s per full extraction

    Configuration:
    -------------
    - pool_size: Number of browser instances (default: 3)
    - headless: Run in headless mode (default: True)
    - timeout_ms: Browser operation timeout (default: 30000)

    Thread Safety:
    -------------
    - acquire() uses asyncio.Lock to prevent race conditions
    - release() is thread-safe
    - close_all() can be called from any async context
    """

    _instance: BrowserPool | None = None
    _lock = asyncio.Lock()

    def __init__(
        self,
        pool_size: int = 3,
        headless: bool = True,
        timeout_ms: int = 30000,
        max_requests_per_browser: int = 50,
    ):
        """
        Initialize browser pool.

        Args:
            pool_size: Number of browser instances to maintain (1-10)
            headless: Run browsers in headless mode (required for Docker)
            timeout_ms: Browser operation timeout in milliseconds
            max_requests_per_browser: Maximum requests before recycling browser (default: 50)
        """
        if not 1 <= pool_size <= 10:
            raise ValueError(f"pool_size must be between 1-10, got {pool_size}")

        self.pool_size = pool_size
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.max_requests_per_browser = max_requests_per_browser

        # Pool state
        self._playwright_context: Any = None
        self._browsers: list[Browser] = []
        self._available: asyncio.Queue[Browser] = asyncio.Queue()
        self._in_use: set[Browser] = set()
        self._initialized = False
        self._access_lock = asyncio.Lock()

        # Tracking for browser recycling
        self._browser_request_counts: dict[Browser, int] = {}

        logger.info(
            f"BrowserPool created with pool_size={pool_size}, "
            f"headless={headless}, timeout_ms={timeout_ms}, "
            f"max_requests_per_browser={max_requests_per_browser}"
        )

    @classmethod
    def get_instance(
        cls,
        pool_size: int = 3,
        headless: bool = True,
        timeout_ms: int = 30000,
        max_requests_per_browser: int = 50,
    ) -> BrowserPool:
        """
        Get or create singleton BrowserPool instance.

        This method implements the singleton pattern to ensure only one
        browser pool exists per application lifecycle.

        Args:
            pool_size: Number of browser instances (only used on first call)
            headless: Run in headless mode (only used on first call)
            timeout_ms: Browser timeout (only used on first call)
            max_requests_per_browser: Max requests before recycling (only used on first call)

        Returns:
            Singleton BrowserPool instance
        """
        if cls._instance is None:
            cls._instance = cls(
                pool_size=pool_size,
                headless=headless,
                timeout_ms=timeout_ms,
                max_requests_per_browser=max_requests_per_browser,
            )
            logger.info("Created singleton BrowserPool instance")
        return cls._instance

    async def initialize(self) -> None:
        """
        Initialize the browser pool by launching all browser instances.

        This method should be called during application startup to warm up
        the pool. It launches all browsers concurrently to minimize startup time.

        Raises:
            RuntimeError: If pool is already initialized
            Exception: If browser launch fails
        """
        async with self._access_lock:
            if self._initialized:
                logger.warning("BrowserPool already initialized, skipping")
                return

            logger.info(f"Initializing BrowserPool with {self.pool_size} browsers...")

            try:
                # Launch Playwright context
                self._playwright_context = await async_playwright().start()

                # Launch all browsers concurrently
                launch_tasks = [self._launch_browser() for _ in range(self.pool_size)]
                browsers = await asyncio.gather(*launch_tasks)

                # Add browsers to pool and initialize request counts
                self._browsers = browsers
                for browser in browsers:
                    await self._available.put(browser)
                    self._browser_request_counts[browser] = 0

                self._initialized = True
                logger.info(
                    f"BrowserPool initialized successfully with {len(self._browsers)} browsers"
                )

            except Exception as e:
                logger.error(f"Failed to initialize BrowserPool: {e}", exc_info=True)
                # Cleanup any partially launched browsers
                await self._cleanup_browsers()
                raise

    async def _launch_browser(self) -> Browser:
        """
        Launch a single browser instance with anti-detection settings.

        Configures browser with:
        - Realistic User-Agent
        - Standard viewport (1920x1080)
        - Disabled automation signals
        - WebDriver override via init script

        Returns:
            Launched Browser instance

        Raises:
            Exception: If browser launch fails
        """
        try:
            browser = await self._playwright_context.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            logger.debug("Launched browser successfully")
            return browser

        except Exception as e:
            logger.error(f"Failed to launch browser: {e}", exc_info=True)
            raise

    async def acquire(self) -> Browser:
        """
        Acquire a browser from the pool.

        This method blocks if no browsers are available until one is released.
        If a browser has crashed, it automatically restarts it before returning.
        Recycles browsers that have exceeded max_requests_per_browser.

        Returns:
            Browser instance ready for use

        Raises:
            RuntimeError: If pool is not initialized
            Exception: If browser restart fails
        """
        if not self._initialized:
            raise RuntimeError("BrowserPool not initialized. Call initialize() first.")

        logger.debug("Acquiring browser from pool...")

        # Wait for available browser (blocks if pool is empty)
        browser = await self._available.get()

        # Check if browser needs recycling
        request_count = self._browser_request_counts.get(browser, 0)
        if request_count >= self.max_requests_per_browser:
            logger.info(
                f"Browser reached max requests ({request_count}/{self.max_requests_per_browser}), recycling...",
                browser_id=id(browser),
                request_count=request_count,
            )
            try:
                # Close old browser
                if browser.is_connected():
                    await browser.close()
                # Launch new browser
                browser = await self._launch_browser()
                # Reset request count
                self._browser_request_counts[browser] = 0
                logger.info("Browser recycled successfully", browser_id=id(browser))
            except Exception as e:
                logger.error(f"Failed to recycle browser: {e}", exc_info=True)
                # Try to put browser back for next acquire attempt
                await self._available.put(browser)
                raise

        # Check if browser is still connected (not crashed)
        elif not browser.is_connected():
            logger.warning("Browser crashed, restarting...", browser_id=id(browser))
            try:
                browser = await self._launch_browser()
                # Reset request count for new browser
                self._browser_request_counts[browser] = 0
                logger.info("Crashed browser restarted successfully", browser_id=id(browser))
            except Exception as e:
                logger.error(f"Failed to restart crashed browser: {e}", exc_info=True)
                # Try to put browser back for next acquire attempt
                await self._available.put(browser)
                raise

        # Increment request count
        self._browser_request_counts[browser] = self._browser_request_counts.get(browser, 0) + 1

        # Mark as in-use
        async with self._access_lock:
            self._in_use.add(browser)

        logger.debug(
            "Acquired browser",
            browser_id=id(browser),
            request_count=self._browser_request_counts[browser],
            in_use=len(self._in_use),
            available=self._available.qsize(),
        )
        return browser

    async def release(self, browser: Browser) -> None:
        """
        Release a browser back to the pool.

        The browser is returned to the available queue for reuse by other requests.

        Args:
            browser: Browser instance to release
        """
        async with self._access_lock:
            if browser in self._in_use:
                self._in_use.remove(browser)

        # Return to available queue
        await self._available.put(browser)

        logger.debug(
            "Released browser",
            browser_id=id(browser),
            request_count=self._browser_request_counts.get(browser, 0),
            in_use=len(self._in_use),
            available=self._available.qsize(),
        )

    async def close_all(self) -> None:
        """
        Close all browsers and cleanup Playwright context.

        This method should be called during application shutdown to ensure
        proper cleanup of browser resources.
        """
        async with self._access_lock:
            if not self._initialized:
                logger.warning("BrowserPool not initialized, nothing to close")
                return

            logger.info("Closing all browsers in pool...")

            # Close all browsers
            await self._cleanup_browsers()

            # Stop Playwright context
            if self._playwright_context:
                await self._playwright_context.stop()
                self._playwright_context = None

            # Reset state
            self._initialized = False
            self._browsers.clear()
            self._in_use.clear()
            self._browser_request_counts.clear()

            # Clear queue
            while not self._available.empty():
                try:
                    self._available.get_nowait()
                except asyncio.QueueEmpty:
                    break

            logger.info("BrowserPool closed successfully")

    async def _cleanup_browsers(self) -> None:
        """
        Close all browser instances.

        Helper method for cleanup during shutdown or initialization failure.
        """
        close_tasks = []
        for browser in self._browsers:
            if browser.is_connected():
                close_tasks.append(browser.close())

        if close_tasks:
            try:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error closing browsers: {e}", exc_info=True)

    def get_pool_stats(self) -> dict[str, Any]:
        """
        Get current pool statistics for monitoring.

        Returns:
            Dictionary with pool statistics:
                - pool_size: Total browser instances
                - in_use: Currently in-use browsers
                - available: Available browsers in queue
                - initialized: Whether pool is initialized
                - total_requests: Sum of all request counts
                - browser_request_counts: Request counts per browser
        """
        return {
            "pool_size": self.pool_size,
            "in_use": len(self._in_use),
            "available": self._available.qsize(),
            "initialized": self._initialized,
            "total_requests": sum(self._browser_request_counts.values()),
            "browser_request_counts": {
                f"browser_{id(browser)}": count
                for browser, count in self._browser_request_counts.items()
            },
        }

    async def __aenter__(self) -> BrowserPool:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close_all()


__all__ = ["BrowserPool"]
