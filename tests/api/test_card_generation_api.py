"""Tests for card image generation API endpoints (Phase 2b).

This test suite verifies:
- GET /listings/{id}/card-image with parameters
- Caching headers (Cache-Control, ETag)
- Error responses (404, 400)
- Content-Type headers
- Parameter validation (style, size, format)

Target: >85% code coverage
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from apps.api.dealbrain_api.main import app
from apps.api.dealbrain_api.models.core import Listing


@pytest.fixture
def sample_listing_data():
    """Sample listing data for mocking."""
    from unittest.mock import Mock

    listing = Mock(spec=Listing)
    listing.id = 123
    listing.title = "Intel NUC 11 Pro"
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


@pytest.mark.asyncio
class TestCardImageEndpoint:
    """Test /listings/{id}/card-image endpoint."""

    async def test_card_image_default_parameters(
        self, sample_listing_data
    ):
        """Test generating card image with default parameters."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/listings/123/card-image")

            # Verify response
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["Content-Type"] == "image/png"
            assert response.content == b"fake_image_data"

            # Verify service called with defaults
            mock_service.render_card.assert_called_once_with(
                listing_id=123,
                style="light",
                format="png",
                size="social",
            )

    async def test_card_image_custom_parameters(
        self, sample_listing_data
    ):
        """Test generating card image with custom parameters."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request with custom params
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={
                        "style": "dark",
                        "format": "webp",
                        "size": "card",
                    },
                )

            # Verify response
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["Content-Type"] == "image/webp"

            # Verify service called with custom params
            mock_service.render_card.assert_called_once_with(
                listing_id=123,
                style="dark",
                format="webp",
                size="card",
            )

    async def test_card_image_listing_not_found(self):
        """Test generating card for non-existent listing."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service to raise ValueError
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(
                side_effect=ValueError("Listing 99999 not found")
            )
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/listings/99999/card-image")

            # Verify 404 response
            assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_card_image_invalid_style(self):
        """Test generating card with invalid style parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/listings/123/card-image",
                params={"style": "invalid"},
            )

        # Verify 400 or 422 response (validation error)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    async def test_card_image_invalid_format(self):
        """Test generating card with invalid format parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/listings/123/card-image",
                params={"format": "gif"},  # Not supported
            )

        # Verify validation error
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    async def test_card_image_invalid_size(self):
        """Test generating card with invalid size parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/listings/123/card-image",
                params={"size": "huge"},  # Not supported
            )

        # Verify validation error
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    async def test_card_image_cache_headers(
        self, sample_listing_data
    ):
        """Test that card image responses include caching headers."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/listings/123/card-image")

            # Verify caching headers
            assert "Cache-Control" in response.headers
            # Should cache for at least 1 hour
            assert "max-age" in response.headers["Cache-Control"]

    async def test_card_image_png_format(
        self, sample_listing_data
    ):
        """Test generating card in PNG format."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_png_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={"format": "png"},
                )

            # Verify Content-Type
            assert response.headers["Content-Type"] == "image/png"

    async def test_card_image_webp_format(
        self, sample_listing_data
    ):
        """Test generating card in WebP format."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_webp_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={"format": "webp"},
                )

            # Verify Content-Type
            assert response.headers["Content-Type"] == "image/webp"

    async def test_card_image_light_style(
        self, sample_listing_data
    ):
        """Test generating card in light style."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={"style": "light"},
                )

            # Verify service called with light style
            mock_service.render_card.assert_called_once()
            call_kwargs = mock_service.render_card.call_args[1]
            assert call_kwargs["style"] == "light"

    async def test_card_image_dark_style(
        self, sample_listing_data
    ):
        """Test generating card in dark style."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={"style": "dark"},
                )

            # Verify service called with dark style
            mock_service.render_card.assert_called_once()
            call_kwargs = mock_service.render_card.call_args[1]
            assert call_kwargs["style"] == "dark"

    async def test_card_image_social_size(
        self, sample_listing_data
    ):
        """Test generating card in social size (1200x630)."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={"size": "social"},
                )

            # Verify service called with social size
            mock_service.render_card.assert_called_once()
            call_kwargs = mock_service.render_card.call_args[1]
            assert call_kwargs["size"] == "social"

    async def test_card_image_card_size(
        self, sample_listing_data
    ):
        """Test generating card in card size (800x600)."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(return_value=b"fake_image_data")
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/listings/123/card-image",
                    params={"size": "card"},
                )

            # Verify service called with card size
            mock_service.render_card.assert_called_once()
            call_kwargs = mock_service.render_card.call_args[1]
            assert call_kwargs["size"] == "card"

    async def test_card_image_service_error(
        self,
    ):
        """Test handling service errors gracefully."""
        with patch("apps.api.dealbrain_api.api.listings.ImageGenerationService") as MockService:
            # Mock service to raise exception
            mock_service = AsyncMock()
            mock_service.render_card = AsyncMock(
                side_effect=Exception("Rendering failed")
            )
            MockService.return_value = mock_service

            # Make request
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/listings/123/card-image")

            # Verify error response
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
class TestCardCacheIntegration:
    """Test card cache invalidation integration."""

    async def test_cache_invalidated_on_price_update(
        self,
    ):
        """Test that updating listing price invalidates card cache."""
        # This would be an integration test with real database
        # For now, we verify the cache invalidation logic is called

        with patch("apps.api.dealbrain_api.services.listings.crud.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.invalidate_cache = AsyncMock(return_value=5)
            MockService.return_value = mock_service

            # Simulate listing update
            from apps.api.dealbrain_api.services.listings.crud import (
                _invalidate_card_cache_if_needed,
            )
            from unittest.mock import Mock

            mock_session = Mock()
            mock_listing = Mock()
            mock_listing.id = 123

            # Update with price change
            await _invalidate_card_cache_if_needed(
                mock_session,
                mock_listing,
                {"price_usd": 599.99},
            )

            # Verify cache invalidation was called
            mock_service.invalidate_cache.assert_called_once_with(123)

    async def test_cache_not_invalidated_on_irrelevant_update(
        self,
    ):
        """Test that updating irrelevant fields doesn't invalidate cache."""
        with patch("apps.api.dealbrain_api.services.listings.crud.ImageGenerationService") as MockService:
            # Mock service
            mock_service = AsyncMock()
            mock_service.invalidate_cache = AsyncMock()
            MockService.return_value = mock_service

            # Simulate listing update with irrelevant field
            from apps.api.dealbrain_api.services.listings.crud import (
                _invalidate_card_cache_if_needed,
            )
            from unittest.mock import Mock

            mock_session = Mock()
            mock_listing = Mock()
            mock_listing.id = 123

            # Update with notes change (should not invalidate)
            await _invalidate_card_cache_if_needed(
                mock_session,
                mock_listing,
                {"notes": "Updated notes"},
            )

            # Verify cache invalidation was NOT called
            mock_service.invalidate_cache.assert_not_called()
