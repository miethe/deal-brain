"""Background tasks for card image generation and caching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dealbrain_api.telemetry import get_logger
from dealbrain_api.worker import celery_app

if TYPE_CHECKING:
    from dealbrain_api.models.core import Listing

logger = get_logger("dealbrain.tasks.card_images")


@celery_app.task(name="card_images.warm_cache_top_listings", bind=True)
def warm_cache_top_listings(
    self,
    limit: int = 100,
    metric: str = "cpu_mark_per_dollar",
) -> dict[str, int | str]:
    """
    Pre-generate card images for top N listings to reduce p95 latency.

    This task runs during off-peak hours to warm the S3 cache with the most
    popular listings. By pre-generating these images, we avoid cold starts
    for the most frequently accessed cards.

    Args:
        limit: Number of top listings to pre-generate (default 100)
        metric: Metric to sort by (default "cpu_mark_per_dollar")

    Returns:
        Dict with success count, error count, and status message

    Example:
        >>> warm_cache_top_listings.delay(limit=50)
    """
    from dealbrain_api.db import session_scope
    from dealbrain_api.models.core import Listing
    from dealbrain_api.settings import get_settings
    from sqlalchemy import select

    settings = get_settings()

    # Check if features are enabled
    if not settings.playwright.enabled:
        logger.warning("Playwright disabled, skipping cache warm-up")
        return {
            "success_count": 0,
            "error_count": 0,
            "status": "skipped",
            "reason": "playwright_disabled",
        }

    if not settings.s3.enabled:
        logger.warning("S3 disabled, skipping cache warm-up")
        return {
            "success_count": 0,
            "error_count": 0,
            "status": "skipped",
            "reason": "s3_disabled",
        }

    logger.info(f"Starting cache warm-up for top {limit} listings by {metric}")

    success_count = 0
    error_count = 0

    try:
        with session_scope() as session:
            # Get top listings by specified metric
            # Note: This will be updated once the card image service is implemented
            stmt = select(Listing).order_by(Listing.id.desc()).limit(limit)
            result = session.execute(stmt)
            listings = result.scalars().all()

            logger.info(f"Found {len(listings)} listings to warm cache")

            for listing in listings:
                try:
                    # TODO: Import and call card image generation service
                    # from dealbrain_api.services.card_images import generate_card_image
                    # generate_card_image(listing_id=listing.id, force_regenerate=False)

                    # Placeholder for now - will be implemented in Phase 2b
                    logger.debug(f"Would generate card image for listing {listing.id}")
                    success_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to generate card image for listing {listing.id}: {e}",
                        exc_info=True,
                    )
                    error_count += 1
                    # Continue with next listing even if one fails

            logger.info(
                f"Cache warm-up completed: {success_count} success, {error_count} errors"
            )

            return {
                "success_count": success_count,
                "error_count": error_count,
                "status": "completed",
            }

    except Exception as e:
        logger.error(f"Cache warm-up failed: {e}", exc_info=True)
        raise


@celery_app.task(name="card_images.cleanup_expired_cache", bind=True)
def cleanup_expired_cache(self) -> dict[str, int | str]:
    """
    Clean up expired card images from S3 based on TTL settings.

    This task runs daily to remove card images that have exceeded their
    configured TTL. The S3 lifecycle policy should handle most cleanup,
    but this task provides additional logic for manual cleanup if needed.

    Returns:
        Dict with deletion count and status message

    Example:
        >>> cleanup_expired_cache.delay()
    """
    from dealbrain_api.settings import get_settings

    settings = get_settings()

    if not settings.s3.enabled:
        logger.warning("S3 disabled, skipping cache cleanup")
        return {
            "deleted_count": 0,
            "status": "skipped",
            "reason": "s3_disabled",
        }

    logger.info("Starting S3 card image cache cleanup")

    try:
        # TODO: Implement S3 cleanup logic once card image service is ready
        # This will:
        # 1. List objects in S3 bucket with card-images/ prefix
        # 2. Check object metadata for creation timestamp
        # 3. Delete objects older than cache_ttl_seconds
        # 4. Return count of deleted objects

        deleted_count = 0

        logger.info(f"S3 cache cleanup completed: {deleted_count} objects deleted")

        return {
            "deleted_count": deleted_count,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"S3 cache cleanup failed: {e}", exc_info=True)
        raise


@celery_app.task(name="card_images.test_playwright", bind=True)
def test_playwright(self) -> dict[str, str | bool]:
    """
    Test task to verify Playwright browser startup.

    This task is useful for healthchecks and ensuring Playwright is
    properly installed with all required system dependencies.

    Returns:
        Dict with browser info and status

    Example:
        >>> test_playwright.delay()
    """
    from dealbrain_api.settings import get_settings

    settings = get_settings()

    if not settings.playwright.enabled:
        return {
            "status": "disabled",
            "success": False,
            "message": "Playwright is disabled in settings",
        }

    try:
        from playwright.sync_api import sync_playwright

        logger.info("Testing Playwright browser startup")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=settings.playwright.headless,
                timeout=settings.playwright.browser_timeout_ms,
            )
            version = browser.version
            browser.close()

            logger.info(f"Playwright test successful: Chromium {version}")

            return {
                "status": "success",
                "success": True,
                "browser": "chromium",
                "version": version,
                "headless": settings.playwright.headless,
            }

    except Exception as e:
        logger.error(f"Playwright test failed: {e}", exc_info=True)
        return {
            "status": "error",
            "success": False,
            "error": str(e),
        }


__all__ = [
    "warm_cache_top_listings",
    "cleanup_expired_cache",
    "test_playwright",
]
