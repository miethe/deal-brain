"""Listings API endpoints.

This module provides REST API endpoints for managing listings and their export/import:
- GET /listings/{id}/export - Export listing as portable JSON
- POST /listings/import - Import listing from JSON (create preview)
- POST /listings/import/confirm - Confirm and execute listing import
- GET /listings/{id}/card-image - Generate shareable card image for social media
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from opentelemetry import trace
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.export_import import ExportImportService
from ..services.image_generation import ImageGenerationService

router = APIRouter(prefix="/v1/listings", tags=["listings"])
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


# ==================== Auth Dependency (Placeholder) ====================


class CurrentUser(BaseModel):
    """Represents the currently authenticated user.

    TODO: This is a placeholder. Replace with actual auth implementation in Phase 4.
    """

    user_id: int
    username: str


async def get_current_user() -> CurrentUser:
    """Get currently authenticated user.

    TODO: This is a PLACEHOLDER implementation.
    In production, this should:
    1. Extract JWT from Authorization header
    2. Validate JWT signature and expiry
    3. Extract user_id from JWT claims
    4. Return CurrentUser with validated user_id

    For development/testing, this returns a hardcoded user.
    """
    # PLACEHOLDER: Return test user for development
    # In production, this would extract from JWT token
    logger.warning("Using placeholder auth - returning hardcoded user_id=1")
    return CurrentUser(user_id=1, username="testuser")


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


# ==================== Request/Response Schemas ====================


class ImportPreviewResponse(BaseModel):
    """Response for import preview with duplicate detection."""

    preview_id: str
    type: str
    parsed_data: dict
    duplicates: list[dict]
    expires_at: str


class ConfirmImportRequest(BaseModel):
    """Request to confirm and execute an import."""

    preview_id: str
    merge_strategy: str = "create_new"  # create_new | update_existing | skip
    target_listing_id: int | None = None


class ListingExportResponse(BaseModel):
    """Response after successful listing export."""

    listing_id: int
    title: str
    export_format: str
    schema_version: str


# ==================== Task 2c-api-1: GET /listings/{id}/export ====================


@router.get(
    "/{listing_id}/export",
    summary="Export listing as portable JSON",
    description=(
        "Export a single listing as portable JSON file (v1.0.0 schema). "
        "User must own or listing must be public."
    ),
    responses={
        200: {"description": "Listing exported successfully as JSON file"},
        401: {"description": "Authentication required"},
        403: {"description": "User does not have access to this listing"},
        404: {"description": "Listing not found"},
        500: {"description": "Internal server error"},
    },
)
async def export_listing(
    listing_id: int,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    format: str = Query(
        "json",
        regex="^json$",
        description="Export format (only json supported currently)",
    ),
) -> Response:
    """Export listing as portable JSON.

    Downloads listing data as a portable JSON file using the v1.0.0 export schema.
    The file includes all listing details, components, performance data, and valuation.

    Args:
        listing_id: Listing ID to export
        current_user: Currently authenticated user (injected)
        session: Database session (injected)
        format: Export format (default: json, only json currently supported)

    Returns:
        File download (JSON) with Content-Disposition header

    Raises:
        HTTPException: 403 if no access, 404 if not found, 500 on export error

    Example:
        GET /api/v1/listings/123/export?format=json

        Response (200):
        Content-Type: application/json
        Content-Disposition: attachment; filename="deal-brain-listing-123-2025-11-19.json"

        {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": "2025-11-19T12:00:00Z",
                "type": "deal"
            },
            "data": { ... }
        }
    """
    logger.info(f"Exporting listing {listing_id} as {format} for user {current_user.user_id}")

    # Initialize export service
    export_service = ExportImportService(session)

    try:
        # Export listing to portable schema
        # TODO: Add access control check (ownership or public visibility)
        portable_export = await export_service.export_listing_as_json(
            listing_id=listing_id,
            user_id=current_user.user_id
        )

        # Generate filename with current date
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        filename = f"deal-brain-listing-{listing_id}-{current_date}.json"

        # Serialize to JSON
        json_content = portable_export.model_dump_json(indent=2, exclude_none=True)

        logger.info(
            f"Listing {listing_id} exported successfully: "
            f"size={len(json_content)} bytes, "
            f"format={format}, "
            f"user={current_user.user_id}"
        )

        # Return file download
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ValueError as e:
        # Listing not found
        logger.warning(f"Listing {listing_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except Exception as e:
        # Unexpected error
        logger.exception(f"Failed to export listing {listing_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


# ==================== Task 2c-api-2: POST /listings/import ====================


@router.post(
    "/import",
    response_model=ImportPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Import listing from JSON (preview)",
    description=(
        "Import a listing from JSON file or data. "
        "Returns preview with duplicate detection. "
        "User must confirm via /import/confirm."
    ),
    responses={
        200: {"description": "Import preview created successfully"},
        400: {"description": "Invalid JSON format or schema validation failed"},
        401: {"description": "Authentication required"},
        422: {"description": "Unprocessable entity (invalid schema)"},
        500: {"description": "Internal server error"},
    },
)
async def import_listing(
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
    file: UploadFile | None = File(None, description="JSON file upload (multipart/form-data)"),
    data: str | None = None,
) -> ImportPreviewResponse:
    """Import listing from JSON with preview and duplicate detection.

    Accepts either a JSON file upload or raw JSON data. Validates against v1.0.0 schema,
    detects potential duplicates, and returns a preview for user confirmation.

    Args:
        current_user: Currently authenticated user (injected)
        session: Database session (injected)
        file: Optional JSON file upload (multipart/form-data)
        data: Optional raw JSON string (alternative to file upload)

    Returns:
        ImportPreviewResponse with preview_id, parsed data, and duplicates

    Raises:
        HTTPException: 400 if invalid format, 422 if schema validation fails

    Example:
        POST /api/v1/listings/import
        Content-Type: multipart/form-data
        file: listing.json

        Response (200):
        {
            "preview_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "deal",
            "parsed_data": {
                "listing": { "title": "Gaming PC", ... }
            },
            "duplicates": [
                {
                    "entity_id": 42,
                    "entity_type": "listing",
                    "match_score": 1.0,
                    "match_reason": "Exact title and seller match",
                    "entity_data": { "id": 42, "title": "Gaming PC", ... }
                }
            ],
            "expires_at": "2025-11-19T12:30:00Z"
        }
    """
    logger.info(f"Importing listing for user {current_user.user_id}")

    # Parse JSON input (either from file or raw data)
    try:
        if file:
            # Read from uploaded file
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty file uploaded"
                )

            # Decode and parse JSON
            try:
                json_text = content.decode("utf-8")
                json_data = json.loads(json_text)
            except UnicodeDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid encoding, expected UTF-8: {e}"
                )
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON format: {e}"
                )

            logger.info(f"Parsed JSON from file: {file.filename}")

        elif data:
            # Parse from raw JSON string
            try:
                json_data = json.loads(data)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON format: {e}"
                )

            logger.info("Parsed JSON from request body")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'file' or 'data' parameter required"
            )

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise

    except Exception as e:
        logger.exception("Error parsing JSON input")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse input: {str(e)}"
        )

    # Initialize export service
    export_service = ExportImportService(session)

    try:
        # Validate schema and create preview with duplicate detection
        preview_id = await export_service.import_listing_from_json(
            json_data=json_data,
            user_id=current_user.user_id
        )

        # Retrieve preview to build response
        from ..services.export_import import _preview_cache
        preview = _preview_cache.get(preview_id)

        if not preview:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create preview"
            )

        logger.info(
            f"Import preview created: preview_id={preview_id}, "
            f"duplicates={len(preview.duplicates)}, "
            f"user={current_user.user_id}"
        )

        # Build response
        return ImportPreviewResponse(
            preview_id=preview_id,
            type=preview.type,
            parsed_data={
                "listing": preview.data.data.listing.model_dump(exclude_none=True)
            },
            duplicates=[
                {
                    "entity_id": dup.entity_id,
                    "entity_type": dup.entity_type,
                    "match_score": dup.match_score,
                    "match_reason": dup.match_reason,
                    "entity_data": dup.entity_data
                }
                for dup in preview.duplicates
            ],
            expires_at=preview.expires_at.isoformat()
        )

    except ValueError as e:
        # Schema validation error
        logger.warning(f"Schema validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except Exception as e:
        logger.exception("Failed to import listing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# ==================== Task 2c-api-2b: POST /listings/import/confirm ====================


@router.post(
    "/import/confirm",
    status_code=status.HTTP_201_CREATED,
    summary="Confirm listing import",
    description=(
        "Confirm and execute a listing import from preview. "
        "Creates or updates listing based on merge strategy."
    ),
    responses={
        201: {"description": "Listing imported successfully"},
        400: {"description": "Invalid preview_id or merge strategy"},
        401: {"description": "Authentication required"},
        404: {"description": "Preview not found or expired"},
        500: {"description": "Internal server error"},
    },
)
async def confirm_import_listing(
    request: ConfirmImportRequest,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    """Confirm and execute listing import.

    Executes the import operation from a preview, applying the specified merge strategy.
    Preview must not be expired (30 minute TTL).

    Args:
        request: Confirmation request with preview_id and merge strategy
        current_user: Currently authenticated user (injected)
        session: Database session (injected)

    Returns:
        Created or updated listing details

    Raises:
        HTTPException: 400 if invalid, 404 if preview not found

    Merge Strategies:
        - create_new: Always create new listing (default)
        - update_existing: Update existing listing (requires target_listing_id)
        - skip: Don't import (returns error)

    Example:
        POST /api/v1/listings/import/confirm
        {
            "preview_id": "550e8400-e29b-41d4-a716-446655440000",
            "merge_strategy": "create_new"
        }

        Response (201):
        {
            "id": 123,
            "title": "Gaming PC",
            "price_usd": 599.99,
            "status": "active",
            "created_at": "2025-11-19T12:00:00Z"
        }
    """
    logger.info(
        f"Confirming import: preview_id={request.preview_id}, "
        f"strategy={request.merge_strategy}, "
        f"user={current_user.user_id}"
    )

    # Initialize export service
    export_service = ExportImportService(session)

    try:
        # Confirm and execute import
        listing = await export_service.confirm_import_listing(
            preview_id=request.preview_id,
            merge_strategy=request.merge_strategy,
            target_listing_id=request.target_listing_id
        )

        logger.info(
            f"Listing imported successfully: id={listing.id}, "
            f"title='{listing.title}', "
            f"strategy={request.merge_strategy}, "
            f"user={current_user.user_id}"
        )

        # Build response
        return {
            "id": listing.id,
            "title": listing.title,
            "price_usd": listing.price_usd,
            "status": listing.status,
            "created_at": listing.created_at.isoformat() if listing.created_at else None,
            "updated_at": listing.updated_at.isoformat() if listing.updated_at else None
        }

    except ValueError as e:
        # Preview not found or invalid merge strategy
        logger.warning(f"Import confirmation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.exception("Failed to confirm import")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import confirmation failed: {str(e)}"
        )


# ==================== Task 2b-api: GET /listings/{id}/card-image ====================


@router.get(
    "/{listing_id}/card-image",
    summary="Generate listing card image",
    description=(
        "Generate a shareable card image for a listing with customizable "
        "style, format, and size. Supports caching with ETags."
    ),
    responses={
        200: {
            "description": "Card image generated successfully",
            "content": {
                "image/png": {"schema": {"type": "string", "format": "binary"}},
                "image/jpeg": {"schema": {"type": "string", "format": "binary"}},
            },
        },
        304: {"description": "Not modified (cached)"},
        400: {"description": "Invalid parameters"},
        404: {"description": "Listing not found"},
        500: {"description": "Image generation failed"},
    },
)
async def get_listing_card_image(
    listing_id: int,
    request: Request,
    session: AsyncSession = Depends(session_dependency),
    format: str = Query(
        "png",
        regex="^(png|jpeg)$",
        description="Image format: 'png' or 'jpeg'",
    ),
    style: str = Query(
        "light",
        regex="^(light|dark)$",
        description="Card theme: 'light' or 'dark'",
    ),
    size: str = Query(
        "social",
        regex="^(social|instagram|story)$",
        description=(
            "Card size: 'social' (1200x630), 'instagram' (1080x1080), "
            "'story' (1080x1920)"
        ),
    ),
) -> Response:
    """Generate listing card image for social sharing.

    Generates a visually appealing card image for a listing with customizable
    style, format, and size. Implements HTTP caching with ETags and Cache-Control
    headers for optimal performance.

    Args:
        listing_id: Listing ID to generate card for
        request: FastAPI request object (for If-None-Match header)
        session: Database session (injected)
        format: Image format ("png" or "jpeg", default: "png")
        style: Card theme ("light" or "dark", default: "light")
        size: Card size preset (default: "social")
            - "social": 1200x630 (Twitter/Facebook)
            - "instagram": 1080x1080 (Instagram square)
            - "story": 1080x1920 (Instagram story)

    Returns:
        Binary image response with appropriate MIME type and caching headers

    Raises:
        HTTPException: 400 if invalid parameters, 404 if not found, 500 on error

    Caching:
        - ETag based on listing_id + parameters
        - Cache-Control: public, max-age=86400 (24 hours)
        - Supports If-None-Match for 304 responses

    Example:
        GET /api/v1/listings/123/card-image?format=png&style=dark&size=social

        Response (200):
        Content-Type: image/png
        Cache-Control: public, max-age=86400
        ETag: "a1b2c3d4e5f6..."

        <binary image data>

        Subsequent request with If-None-Match header:
        Response (304 Not Modified)
    """
    with tracer.start_as_current_span("listings.get_card_image") as span:
        span.set_attribute("listing_id", listing_id)
        span.set_attribute("format", format)
        span.set_attribute("style", style)
        span.set_attribute("size", size)

        logger.info(
            f"Generating card image for listing {listing_id}: "
            f"format={format}, style={style}, size={size}"
        )

        # Validate parameters (redundant with Query validation, but explicit)
        valid_formats = {"png", "jpeg"}
        valid_styles = {"light", "dark"}
        valid_sizes = {"social", "instagram", "story"}

        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}",
            )

        if style not in valid_styles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid style '{style}'. Must be one of: {', '.join(valid_styles)}",
            )

        if size not in valid_sizes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}",
            )

        # Generate ETag based on listing ID and parameters
        etag_source = f"{listing_id}:{style}:{format}:{size}"
        etag = hashlib.md5(etag_source.encode()).hexdigest()

        # Check If-None-Match header for 304 response
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match.strip('"') == etag:
            logger.info(f"ETag match for listing {listing_id}, returning 304")
            span.set_attribute("cache_hit", True)
            return Response(status_code=status.HTTP_304_NOT_MODIFIED)

        span.set_attribute("cache_hit", False)

        # Initialize image generation service
        image_service = ImageGenerationService(session)

        try:
            # Generate card image
            image_bytes = await image_service.render_card(
                listing_id=listing_id,
                style=style,  # type: ignore
                format=format,  # type: ignore
                size=size,  # type: ignore
            )

            logger.info(
                f"Card image generated for listing {listing_id}: "
                f"{len(image_bytes)} bytes ({format.upper()})"
            )

            span.set_attribute("image_size_bytes", len(image_bytes))
            span.set_attribute("success", True)

            # Determine MIME type
            mime_type = f"image/{format}"

            # Return image with caching headers
            return Response(
                content=image_bytes,
                media_type=mime_type,
                headers={
                    "Cache-Control": "public, max-age=86400",  # 24 hours
                    "ETag": f'"{etag}"',
                },
            )

        except ValueError as e:
            # Listing not found
            logger.warning(f"Listing {listing_id} not found: {e}")
            span.set_attribute("error", "listing_not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing {listing_id} not found",
            )

        except Exception as e:
            # Image generation failed - service handles fallback to placeholder
            logger.exception(f"Failed to generate card image for listing {listing_id}")
            span.set_attribute("error", "generation_failed")
            span.set_attribute("error_message", str(e))

            # Try to return a placeholder instead of failing completely
            try:
                # Service's render_card already handles fallback internally
                # If we're here, it means something else failed
                # Return minimal 1x1 transparent PNG as last resort
                fallback_png = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                    b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
                )

                logger.warning(
                    f"Returning fallback placeholder for listing {listing_id}"
                )
                span.set_attribute("fallback_used", True)

                return Response(
                    content=fallback_png,
                    media_type="image/png",
                    headers={
                        # Cache placeholder for 5 minutes only
                        "Cache-Control": "public, max-age=300",
                        "ETag": f'"{etag}-fallback"',
                    },
                )

            except Exception as fallback_error:
                logger.error(f"Even fallback failed: {fallback_error}")
                span.set_attribute("fallback_failed", True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Image generation failed: {str(e)}",
                )


__all__ = ["router"]
