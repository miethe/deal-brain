"""Business logic for generating card images from listings using Playwright.

This module provides the service layer for card image generation including:
- HTML template rendering with Jinja2
- Playwright-based headless browser rendering
- Browser pool management for performance
- S3 caching with automatic invalidation
- Graceful fallback on errors
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import Browser, Error as PlaywrightError, async_playwright
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.listings import Listing
from ..settings import get_settings

logger = logging.getLogger(__name__)

# Template dimensions for different card sizes
CARD_DIMENSIONS = {
    "social": {"width": 1200, "height": 630},  # Twitter/Facebook
    "instagram": {"width": 1080, "height": 1080},  # Instagram square
    "story": {"width": 1080, "height": 1920},  # Instagram story
}

# Valuation tier thresholds (should match frontend settings)
VALUATION_TIERS = {
    "great": 0.15,  # 15% or more below market
    "good": 0.05,   # 5-15% below market
    "fair": -0.05,  # Within 5% of market
    "premium": -0.05,  # More than 5% above market
}


class BrowserPool:
    """Pool manager for Playwright browser instances.

    Manages a pool of headless browser instances to improve performance
    and prevent resource exhaustion. Implements semaphore-based limiting
    to prevent OOM issues.

    Args:
        max_size: Maximum number of concurrent browser instances (default: 2)
        timeout_ms: Browser operation timeout in milliseconds (default: 30000)
    """

    def __init__(self, max_size: int = 2, timeout_ms: int = 30000):
        """Initialize browser pool.

        Args:
            max_size: Maximum concurrent browsers
            timeout_ms: Browser operation timeout
        """
        self._semaphore = asyncio.Semaphore(max_size)
        self._timeout_ms = timeout_ms
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> Browser:
        """Acquire a browser instance from the pool.

        Returns:
            Playwright Browser instance

        Raises:
            PlaywrightError: If browser initialization fails
        """
        await self._semaphore.acquire()

        async with self._lock:
            if self._browser is None:
                try:
                    self._playwright = await async_playwright().start()
                    self._browser = await self._playwright.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-dev-shm-usage",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-gpu",
                        ]
                    )
                    logger.info("Initialized Playwright browser instance")
                except PlaywrightError as e:
                    logger.error(f"Failed to initialize browser: {e}")
                    self._semaphore.release()
                    raise

        return self._browser

    def release(self):
        """Release browser instance back to pool."""
        self._semaphore.release()

    async def close(self):
        """Close all browser instances and cleanup."""
        async with self._lock:
            if self._browser:
                try:
                    await self._browser.close()
                    logger.info("Closed browser instance")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
                finally:
                    self._browser = None

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playwright: {e}")
                finally:
                    self._playwright = None


class ImageGenerationService:
    """Business logic for generating listing card images.

    Provides high-level operations for:
    - Rendering listing data as HTML cards
    - Converting HTML to PNG/JPEG images using Playwright
    - Caching images in S3 with TTL
    - Cache invalidation on listing updates
    - Graceful error handling and fallbacks

    Args:
        session: Async SQLAlchemy session for database operations
    """

    # Shared browser pool across all service instances
    _browser_pool: Optional[BrowserPool] = None
    _pool_lock = asyncio.Lock()

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.settings = get_settings()

        # Initialize Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=True,
        )

        # Initialize S3 client if enabled
        self.s3_client = None
        if self.settings.s3.enabled:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.settings.aws_access_key_id or self.settings.s3.access_key_id,
                    aws_secret_access_key=self.settings.aws_secret_access_key or self.settings.s3.secret_access_key,
                    region_name=self.settings.aws_region or self.settings.s3.region,
                    endpoint_url=self.settings.s3.endpoint_url,
                )
                logger.info(
                    f"Initialized S3 client for bucket: {self.settings.s3.bucket_name}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.s3_client = None

    @classmethod
    async def get_browser_pool(cls) -> BrowserPool:
        """Get or create the shared browser pool.

        Returns:
            Shared BrowserPool instance
        """
        async with cls._pool_lock:
            if cls._browser_pool is None:
                settings = get_settings()
                cls._browser_pool = BrowserPool(
                    max_size=settings.playwright.max_concurrent_browsers,
                    timeout_ms=settings.playwright.browser_timeout_ms,
                )
            return cls._browser_pool

    @classmethod
    async def close_browser_pool(cls):
        """Close the shared browser pool."""
        async with cls._pool_lock:
            if cls._browser_pool is not None:
                await cls._browser_pool.close()
                cls._browser_pool = None

    async def render_card(
        self,
        listing_id: int,
        style: Literal["light", "dark"] = "light",
        format: Literal["png", "jpeg"] = "png",
        size: Literal["social", "instagram", "story"] = "social",
    ) -> bytes:
        """Render listing as card image.

        Loads listing data, renders HTML template, and converts to image
        using Playwright. Implements caching with S3 if enabled.

        Args:
            listing_id: Listing ID to render
            style: Card theme ("light" or "dark")
            format: Image format ("png" or "jpeg")
            size: Card size preset ("social", "instagram", "story")

        Returns:
            Image bytes (PNG or JPEG)

        Raises:
            ValueError: If listing not found
            PlaywrightError: If rendering fails

        Example:
            # Generate social card
            image_bytes = await service.render_card(
                listing_id=123,
                style="dark",
                format="png",
                size="social"
            )
        """
        # Check cache first
        cached_image = await self.get_cached_image(listing_id, style, format, size)
        if cached_image:
            logger.info(f"Cache hit for listing {listing_id} ({style}/{size}.{format})")
            return cached_image

        # Load listing data
        listing = await self._load_listing(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # Render HTML
        html = await self._render_html(listing, style, size)

        # Convert to image
        try:
            image_bytes = await self._html_to_image(html, format, size)
            logger.info(
                f"Generated {format.upper()} card for listing {listing_id} "
                f"({style}/{size}): {len(image_bytes)} bytes"
            )
        except Exception as e:
            logger.error(f"Failed to render card for listing {listing_id}: {e}")
            # Return placeholder image on error
            return await self._generate_placeholder(size, format)

        # Cache the image
        if image_bytes:
            await self.cache_image(listing_id, style, format, size, image_bytes)

        return image_bytes

    async def _load_listing(self, listing_id: int) -> Optional[Listing]:
        """Load listing with related data.

        Args:
            listing_id: Listing ID

        Returns:
            Listing instance or None if not found
        """
        stmt = select(Listing).where(Listing.id == listing_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _render_html(
        self,
        listing: Listing,
        style: str,
        size: str,
    ) -> str:
        """Render listing data as HTML card.

        Args:
            listing: Listing instance
            style: Card theme
            size: Card size preset

        Returns:
            Rendered HTML string
        """
        dimensions = CARD_DIMENSIONS[size]

        # Determine valuation tier
        valuation_tier = self._get_valuation_tier(listing)

        # Prepare template context
        context = {
            "title": listing.title[:60],  # Truncate for readability
            "price": f"{listing.price_usd:.0f}" if listing.price_usd else "N/A",
            "adjusted_price": (
                f"{listing.adjusted_price_usd:.0f}"
                if listing.adjusted_price_usd and listing.adjusted_price_usd != listing.price_usd
                else None
            ),
            "cpu": listing.cpu.model if listing.cpu else None,
            "ram": f"{listing.ram_gb}GB" if listing.ram_gb else None,
            "storage": (
                f"{listing.primary_storage_gb}GB {listing.primary_storage_type or 'SSD'}"
                if listing.primary_storage_gb
                else None
            ),
            "score": (
                f"{listing.score_composite:.1f}"
                if listing.score_composite
                else None
            ),
            "manufacturer": listing.manufacturer,
            "series": listing.series,
            "valuation_tier": valuation_tier,
            "theme": style,
            "width": dimensions["width"],
            "height": dimensions["height"],
            "qr_code_url": None,  # TODO: Generate QR code in future phase
        }

        template = self.jinja_env.get_template("card_template.html")
        return await template.render_async(**context)

    def _get_valuation_tier(self, listing: Listing) -> Optional[str]:
        """Determine valuation tier based on price difference.

        Args:
            listing: Listing instance

        Returns:
            Valuation tier ("great", "good", "fair", "premium") or None
        """
        if not listing.price_usd or not listing.adjusted_price_usd:
            return None

        # Calculate percentage difference
        diff_pct = (listing.adjusted_price_usd - listing.price_usd) / listing.price_usd

        if diff_pct >= VALUATION_TIERS["great"]:
            return "great"
        elif diff_pct >= VALUATION_TIERS["good"]:
            return "good"
        elif diff_pct >= VALUATION_TIERS["fair"]:
            return "fair"
        else:
            return "premium"

    async def _html_to_image(
        self,
        html: str,
        format: str,
        size: str,
    ) -> bytes:
        """Convert HTML to image using Playwright.

        Args:
            html: HTML content
            format: Image format ("png" or "jpeg")
            size: Card size preset

        Returns:
            Image bytes

        Raises:
            PlaywrightError: If rendering fails
        """
        if not self.settings.playwright.enabled:
            raise RuntimeError("Playwright is disabled in settings")

        dimensions = CARD_DIMENSIONS[size]
        browser_pool = await self.get_browser_pool()
        browser = None

        try:
            browser = await browser_pool.acquire()
            page = await browser.new_page(
                viewport={
                    "width": dimensions["width"],
                    "height": dimensions["height"],
                }
            )

            # Set content and wait for fonts/images to load
            await page.set_content(html, wait_until="networkidle")

            # Small delay to ensure rendering completes
            await asyncio.sleep(0.5)

            # Capture screenshot
            screenshot_bytes = await page.screenshot(
                type=format,
                full_page=False,
            )

            await page.close()
            return screenshot_bytes

        except PlaywrightError as e:
            logger.error(f"Playwright rendering error: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error("Playwright rendering timeout")
            raise PlaywrightError("Rendering timeout")
        finally:
            if browser:
                browser_pool.release()

    async def _generate_placeholder(
        self,
        size: str,
        format: str,
    ) -> bytes:
        """Generate placeholder image on error.

        Args:
            size: Card size preset
            format: Image format

        Returns:
            Placeholder image bytes
        """
        # Simple placeholder HTML
        dimensions = CARD_DIMENSIONS[size]
        placeholder_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    width: {dimensions["width"]}px;
                    height: {dimensions["height"]}px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: Arial, sans-serif;
                    color: white;
                    font-size: 48px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            Deal Brain
        </body>
        </html>
        """

        try:
            return await self._html_to_image(placeholder_html, format, size)
        except Exception as e:
            logger.error(f"Failed to generate placeholder: {e}")
            # Return minimal 1x1 transparent PNG as last resort
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    async def get_cached_image(
        self,
        listing_id: int,
        style: str,
        format: str,
        size: str,
    ) -> Optional[bytes]:
        """Retrieve cached image from S3.

        Args:
            listing_id: Listing ID
            style: Card theme
            format: Image format
            size: Card size preset

        Returns:
            Image bytes if cached and not expired, None otherwise
        """
        if not self.s3_client or not self.settings.s3.enabled:
            return None

        s3_key = self._get_s3_key(listing_id, style, size, format)

        try:
            response = self.s3_client.get_object(
                Bucket=self.settings.s3.bucket_name,
                Key=s3_key,
            )

            # Check if cache is expired
            metadata = response.get("Metadata", {})
            if "expires_at" in metadata:
                expires_at = datetime.fromisoformat(metadata["expires_at"])
                if datetime.utcnow() > expires_at:
                    logger.info(f"Cache expired for {s3_key}")
                    return None

            image_bytes = response["Body"].read()
            logger.debug(f"Retrieved cached image from S3: {s3_key}")
            return image_bytes

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.debug(f"Cache miss for {s3_key}")
            else:
                logger.warning(f"S3 get error for {s3_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving from S3: {e}")
            return None

    async def cache_image(
        self,
        listing_id: int,
        style: str,
        format: str,
        size: str,
        image_bytes: bytes,
    ) -> Optional[str]:
        """Cache image in S3.

        Args:
            listing_id: Listing ID
            style: Card theme
            format: Image format
            size: Card size preset
            image_bytes: Image data

        Returns:
            S3 URL if successful, None otherwise
        """
        if not self.s3_client or not self.settings.s3.enabled:
            return None

        s3_key = self._get_s3_key(listing_id, style, size, format)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(
            seconds=self.settings.s3.cache_ttl_seconds
        )

        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.settings.s3.bucket_name,
                Key=s3_key,
                Body=image_bytes,
                ContentType=f"image/{format}",
                Metadata={
                    "listing_id": str(listing_id),
                    "style": style,
                    "size": size,
                    "format": format,
                    "expires_at": expires_at.isoformat(),
                },
                CacheControl=f"max-age={self.settings.s3.cache_ttl_seconds}",
            )

            # Generate URL
            s3_url = f"https://{self.settings.s3.bucket_name}.s3.{self.settings.s3.region}.amazonaws.com/{s3_key}"

            logger.info(f"Cached image to S3: {s3_key}")
            return s3_url

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to cache image to S3: {e}")
            return None

    async def invalidate_cache(self, listing_id: int) -> int:
        """Invalidate all cached images for a listing.

        Deletes all cached variants (styles, sizes, formats) for the
        given listing. Called when listing is updated.

        Args:
            listing_id: Listing ID

        Returns:
            Number of cached images deleted
        """
        if not self.s3_client or not self.settings.s3.enabled:
            return 0

        deleted_count = 0

        # Generate all possible cache keys
        for style in ["light", "dark"]:
            for size in ["social", "instagram", "story"]:
                for format in ["png", "jpeg"]:
                    s3_key = self._get_s3_key(listing_id, style, size, format)
                    try:
                        self.s3_client.delete_object(
                            Bucket=self.settings.s3.bucket_name,
                            Key=s3_key,
                        )
                        deleted_count += 1
                    except Exception as e:
                        logger.debug(
                            f"Failed to delete {s3_key} (may not exist): {e}"
                        )

        if deleted_count > 0:
            logger.info(
                f"Invalidated {deleted_count} cached images for listing {listing_id}"
            )

        return deleted_count

    def _get_s3_key(
        self,
        listing_id: int,
        style: str,
        size: str,
        format: str,
    ) -> str:
        """Generate S3 key for cached image.

        Format: cards/{listing_id}/{style}/{size}.{format}
        Example: cards/123/light/1200x630.png

        Args:
            listing_id: Listing ID
            style: Card theme
            size: Card size preset
            format: Image format

        Returns:
            S3 object key
        """
        dimensions = CARD_DIMENSIONS[size]
        size_str = f"{dimensions['width']}x{dimensions['height']}"
        return f"cards/{listing_id}/{style}/{size_str}.{format}"


__all__ = [
    "ImageGenerationService",
    "BrowserPool",
    "CARD_DIMENSIONS",
    "VALUATION_TIERS",
]
