"""Tests for image generation service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models import Listing
from dealbrain_api.services.image_generation import (
    CARD_DIMENSIONS,
    BrowserPool,
    ImageGenerationService,
)


@pytest.fixture
def mock_settings():
    """Mock settings with Playwright and S3 enabled."""
    settings = Mock()
    settings.playwright.enabled = True
    settings.playwright.max_concurrent_browsers = 2
    settings.playwright.browser_timeout_ms = 30000
    settings.playwright.headless = True
    settings.s3.enabled = False  # Disabled by default for tests
    settings.s3.bucket_name = "test-bucket"
    settings.s3.region = "us-east-1"
    settings.s3.access_key_id = None
    settings.s3.secret_access_key = None
    settings.s3.cache_ttl_seconds = 2592000
    settings.s3.endpoint_url = None
    settings.aws_access_key_id = None
    settings.aws_secret_access_key = None
    settings.aws_region = None
    return settings


@pytest.fixture
def sample_listing():
    """Create a sample listing for testing."""
    listing = Mock(spec=Listing)
    listing.id = 123
    listing.title = "Intel NUC 11 Pro - Powerful Compact PC"
    listing.price_usd = 599.99
    listing.adjusted_price_usd = 549.99
    listing.cpu = Mock(model="Intel Core i7-1165G7")
    listing.ram_gb = 16
    listing.primary_storage_gb = 512
    listing.primary_storage_type = "NVMe SSD"
    listing.score_composite = 8.5
    listing.manufacturer = "Intel"
    listing.series = "NUC 11 Pro"
    return listing


class TestBrowserPool:
    """Tests for BrowserPool class."""

    @pytest.mark.asyncio
    async def test_acquire_browser_initializes_on_first_call(self):
        """Test that acquiring a browser initializes Playwright on first call."""
        pool = BrowserPool(max_size=2, timeout_ms=30000)

        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch(
            "dealbrain_api.services.image_generation.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            browser = await pool.acquire()

            assert browser is mock_browser
            mock_playwright.chromium.launch.assert_called_once()

        pool.release()
        await pool.close()

    @pytest.mark.asyncio
    async def test_browser_pool_semaphore_limits_concurrent_browsers(self):
        """Test that semaphore limits concurrent browser instances."""
        pool = BrowserPool(max_size=1, timeout_ms=30000)

        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch(
            "dealbrain_api.services.image_generation.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            # Acquire first browser
            browser1 = await pool.acquire()
            assert browser1 is mock_browser

            # Semaphore should be at capacity (can't test easily without async)
            # Just verify we got a browser
            assert pool._semaphore.locked()

        pool.release()
        await pool.close()

    @pytest.mark.asyncio
    async def test_close_shuts_down_browser_and_playwright(self):
        """Test that close() properly shuts down resources."""
        pool = BrowserPool(max_size=2, timeout_ms=30000)

        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch(
            "dealbrain_api.services.image_generation.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            await pool.acquire()
            await pool.close()

            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()
            assert pool._browser is None


class TestImageGenerationService:
    """Tests for ImageGenerationService class."""

    @pytest.mark.asyncio
    async def test_render_card_returns_image_bytes(
        self, mock_settings, sample_listing
    ):
        """Test that render_card returns image bytes."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            # Mock dependencies
            service._load_listing = AsyncMock(return_value=sample_listing)
            service._render_html = AsyncMock(return_value="<html>test</html>")
            service._html_to_image = AsyncMock(return_value=b"fake_image_data")
            service.get_cached_image = AsyncMock(return_value=None)
            service.cache_image = AsyncMock()

            result = await service.render_card(
                listing_id=123,
                style="light",
                format="png",
                size="social",
            )

            assert result == b"fake_image_data"
            service._load_listing.assert_called_once_with(123)
            service._render_html.assert_called_once()
            service._html_to_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_card_uses_cache_if_available(
        self, mock_settings, sample_listing
    ):
        """Test that render_card uses cached image if available."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            cached_image = b"cached_image_data"
            service.get_cached_image = AsyncMock(return_value=cached_image)
            service._load_listing = AsyncMock(return_value=sample_listing)
            service._render_html = AsyncMock()
            service._html_to_image = AsyncMock()

            result = await service.render_card(
                listing_id=123,
                style="light",
                format="png",
                size="social",
            )

            assert result == cached_image
            service.get_cached_image.assert_called_once()
            # Should not call render functions if cache hit
            service._render_html.assert_not_called()
            service._html_to_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_render_card_raises_error_if_listing_not_found(
        self, mock_settings
    ):
        """Test that render_card raises ValueError if listing not found."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)
            service._load_listing = AsyncMock(return_value=None)
            service.get_cached_image = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="Listing 999 not found"):
                await service.render_card(
                    listing_id=999,
                    style="light",
                    format="png",
                    size="social",
                )

    @pytest.mark.asyncio
    async def test_render_card_returns_placeholder_on_error(
        self, mock_settings, sample_listing
    ):
        """Test that render_card returns placeholder if rendering fails."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            service._load_listing = AsyncMock(return_value=sample_listing)
            service._render_html = AsyncMock(return_value="<html>test</html>")
            service._html_to_image = AsyncMock(
                side_effect=Exception("Playwright error")
            )
            service._generate_placeholder = AsyncMock(
                return_value=b"placeholder_image"
            )
            service.get_cached_image = AsyncMock(return_value=None)

            result = await service.render_card(
                listing_id=123,
                style="light",
                format="png",
                size="social",
            )

            assert result == b"placeholder_image"
            service._generate_placeholder.assert_called_once()

    @pytest.mark.asyncio
    async def test_render_html_renders_template_correctly(
        self, mock_settings, sample_listing
    ):
        """Test that _render_html renders the template with correct context."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            # Mock Jinja2 template
            mock_template = AsyncMock()
            mock_template.render_async = AsyncMock(
                return_value="<html>rendered</html>"
            )
            service.jinja_env.get_template = Mock(return_value=mock_template)

            html = await service._render_html(
                listing=sample_listing,
                style="dark",
                size="social",
            )

            assert html == "<html>rendered</html>"
            service.jinja_env.get_template.assert_called_once_with(
                "card_template.html"
            )

            # Verify template context includes expected fields
            call_kwargs = mock_template.render_async.call_args[1]
            assert call_kwargs["title"] == sample_listing.title[:60]
            assert call_kwargs["price"] == "600"
            assert call_kwargs["adjusted_price"] == "550"
            assert call_kwargs["cpu"] == "Intel Core i7-1165G7"
            assert call_kwargs["ram"] == "16GB"
            assert call_kwargs["storage"] == "512GB NVMe SSD"
            assert call_kwargs["theme"] == "dark"
            assert call_kwargs["width"] == CARD_DIMENSIONS["social"]["width"]
            assert call_kwargs["height"] == CARD_DIMENSIONS["social"]["height"]

    @pytest.mark.asyncio
    async def test_get_cached_image_returns_none_if_s3_disabled(
        self, mock_settings
    ):
        """Test that get_cached_image returns None if S3 is disabled."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            result = await service.get_cached_image(
                listing_id=123,
                style="light",
                format="png",
                size="social",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_cache_image_returns_none_if_s3_disabled(self, mock_settings):
        """Test that cache_image returns None if S3 is disabled."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            result = await service.cache_image(
                listing_id=123,
                style="light",
                format="png",
                size="social",
                image_bytes=b"test_image",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_cache_image_uploads_to_s3_when_enabled(self, mock_settings):
        """Test that cache_image uploads to S3 when enabled."""
        mock_settings.s3.enabled = True
        mock_session = AsyncMock(spec=AsyncSession)

        mock_s3_client = MagicMock()

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "dealbrain_api.services.image_generation.boto3.client",
                return_value=mock_s3_client,
            ):
                service = ImageGenerationService(mock_session)

                result = await service.cache_image(
                    listing_id=123,
                    style="light",
                    format="png",
                    size="social",
                    image_bytes=b"test_image",
                )

                # Verify S3 upload was called
                mock_s3_client.put_object.assert_called_once()
                call_kwargs = mock_s3_client.put_object.call_args[1]
                assert call_kwargs["Bucket"] == "test-bucket"
                assert call_kwargs["Body"] == b"test_image"
                assert call_kwargs["ContentType"] == "image/png"

                # Should return S3 URL
                assert "s3" in result
                assert "cards/123" in result

    @pytest.mark.asyncio
    async def test_invalidate_cache_deletes_all_variants(self, mock_settings):
        """Test that invalidate_cache deletes all cached variants."""
        mock_settings.s3.enabled = True
        mock_session = AsyncMock(spec=AsyncSession)

        mock_s3_client = MagicMock()

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "dealbrain_api.services.image_generation.boto3.client",
                return_value=mock_s3_client,
            ):
                service = ImageGenerationService(mock_session)

                deleted_count = await service.invalidate_cache(listing_id=123)

                # Should attempt to delete 2 styles × 3 sizes × 2 formats = 12 variants
                assert mock_s3_client.delete_object.call_count == 12
                assert deleted_count == 12

    @pytest.mark.asyncio
    async def test_get_s3_key_generates_correct_format(self, mock_settings):
        """Test that _get_s3_key generates correct key format."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            key = service._get_s3_key(
                listing_id=123,
                style="dark",
                size="social",
                format="png",
            )

            assert key == "cards/123/dark/1200x630.png"

    @pytest.mark.asyncio
    async def test_get_valuation_tier_calculates_correctly(
        self, mock_settings, sample_listing
    ):
        """Test that _get_valuation_tier calculates tier correctly."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "dealbrain_api.services.image_generation.get_settings",
            return_value=mock_settings,
        ):
            service = ImageGenerationService(mock_session)

            # Test "great" tier (15%+ below market)
            sample_listing.price_usd = 100
            sample_listing.adjusted_price_usd = 115
            assert service._get_valuation_tier(sample_listing) == "great"

            # Test "good" tier (5-15% below market)
            sample_listing.adjusted_price_usd = 110
            assert service._get_valuation_tier(sample_listing) == "good"

            # Test "fair" tier (within 5%)
            sample_listing.adjusted_price_usd = 103
            assert service._get_valuation_tier(sample_listing) == "fair"

            # Test "premium" tier (above market)
            sample_listing.adjusted_price_usd = 95
            assert service._get_valuation_tier(sample_listing) == "premium"

            # Test None if no prices
            sample_listing.price_usd = None
            assert service._get_valuation_tier(sample_listing) is None


class TestCacheInvalidationIntegration:
    """Tests for cache invalidation integration with listing updates."""

    @pytest.mark.asyncio
    async def test_listing_update_triggers_cache_invalidation(self):
        """Test that updating price triggers cache invalidation."""
        from dealbrain_api.services.listings.crud import (
            CACHE_INVALIDATION_FIELDS,
            _invalidate_card_cache_if_needed,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_listing = Mock(spec=Listing)
        mock_listing.id = 123

        # Mock the ImageGenerationService
        with patch(
            "dealbrain_api.services.listings.crud.ImageGenerationService"
        ) as MockImageService:
            mock_service = AsyncMock()
            mock_service.invalidate_cache = AsyncMock(return_value=5)
            MockImageService.return_value = mock_service

            # Update with price change (should trigger invalidation)
            await _invalidate_card_cache_if_needed(
                mock_session,
                mock_listing,
                {"price_usd": 599.99},
            )

            mock_service.invalidate_cache.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_listing_update_skips_invalidation_for_irrelevant_fields(self):
        """Test that updating irrelevant fields doesn't trigger invalidation."""
        from dealbrain_api.services.listings.crud import (
            _invalidate_card_cache_if_needed,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_listing = Mock(spec=Listing)
        mock_listing.id = 123

        with patch(
            "dealbrain_api.services.listings.crud.ImageGenerationService"
        ) as MockImageService:
            mock_service = AsyncMock()
            mock_service.invalidate_cache = AsyncMock()
            MockImageService.return_value = mock_service

            # Update with irrelevant field (should not trigger invalidation)
            await _invalidate_card_cache_if_needed(
                mock_session,
                mock_listing,
                {"notes": "Updated notes"},
            )

            mock_service.invalidate_cache.assert_not_called()
