"""Deal Builder API endpoints.

Provides endpoints for:
- Real-time build calculation (pricing and metrics)
- Build saving with snapshots
- Build retrieval with access control
- Build listing with pagination
- Build updates and deletion
- Share link access
- Comparison with pre-built listings
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..schemas.builder import (
    BuildComponentsRequest,
    BuildListResponse,
    CalculateResponse,
    CompareResponse,
    DeleteResponse,
    ListingComparisonResponse,
    MetricsResponse,
    SaveBuildRequest,
    SavedBuildResponse,
    ValuationBreakdownResponse,
    ValuationResponse,
)
from ..services.builder_service import BuilderService
from ..telemetry import get_logger

logger = get_logger("dealbrain.api.builder")

router = APIRouter(prefix="/v1/builder", tags=["builder"])


def normalize_user_id(user_id: Optional[int]) -> int:
    """Normalize user_id: None -> 0 for consistency across operations.

    Args:
        user_id: Optional user ID from auth middleware

    Returns:
        0 if user_id is None, otherwise the original user_id
    """
    return user_id if user_id is not None else 0


@router.post(
    "/calculate",
    response_model=CalculateResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate build valuation and metrics",
    description="""
    Calculate pricing and performance metrics for a custom build without saving.

    **Required:**
    - CPU selection (cpu_id)

    **Optional:**
    - GPU, RAM, storage, PSU, case component IDs

    **Returns:**
    - **Valuation**: Base price, adjusted price, delta, and breakdown
    - **Metrics**: Price-per-performance ratios and composite score

    **Performance:**
    - Target: <300ms response time
    - Uses cached component data when available
    - Real-time calculation with current pricing rules

    **Use Cases:**
    - Interactive build configurator
    - Real-time price updates as components change
    - Performance comparison before saving
    """,
)
async def calculate_build(
    components: BuildComponentsRequest,
    session: AsyncSession = Depends(session_dependency),
) -> CalculateResponse:
    """Calculate build valuation and performance metrics.

    Requires CPU selection. Other components optional.
    Returns pricing breakdown and performance metrics.

    Args:
        components: Component selection (CPU required)
        session: Database session for component lookup

    Returns:
        CalculateResponse with valuation and metrics data

    Raises:
        HTTPException(400): Invalid input (missing CPU, invalid component IDs)
        HTTPException(500): Calculation error
    """
    try:
        logger.info("calculate_build.start", cpu_id=components.cpu_id, gpu_id=components.gpu_id)

        service = BuilderService(session)

        # Calculate valuation
        valuation_data = await service.calculate_build_valuation(components.model_dump())

        # Calculate metrics
        metrics_data = await service.calculate_build_metrics(
            components.cpu_id, valuation_data["adjusted_price"]
        )

        # Build response
        response = CalculateResponse(
            valuation=ValuationResponse(
                base_price=valuation_data["base_price"],
                adjusted_price=valuation_data["adjusted_price"],
                delta_amount=valuation_data["delta_amount"],
                delta_percentage=valuation_data["delta_percentage"],
                breakdown=ValuationBreakdownResponse(
                    components=valuation_data["breakdown"]["components"],
                    adjustments=valuation_data["breakdown"]["adjustments"],
                ),
            ),
            metrics=MetricsResponse(
                dollar_per_cpu_mark_multi=metrics_data["dollar_per_cpu_mark_multi"],
                dollar_per_cpu_mark_single=metrics_data["dollar_per_cpu_mark_single"],
                composite_score=metrics_data["composite_score"],
                cpu_mark_multi=metrics_data["cpu_mark_multi"],
                cpu_mark_single=metrics_data["cpu_mark_single"],
            ),
        )

        logger.info(
            "calculate_build.success",
            cpu_id=components.cpu_id,
            base_price=float(valuation_data["base_price"]),
            adjusted_price=float(valuation_data["adjusted_price"]),
        )

        return response

    except ValueError as e:
        logger.warning("calculate_build.validation_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("calculate_build.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation failed: {str(e)}",
        )


@router.post(
    "/builds",
    response_model=SavedBuildResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a custom build",
    description="""
    Save a custom build with pricing and metrics snapshots.

    **Required:**
    - Build name (1-255 characters)
    - Component selection (CPU required)

    **Optional:**
    - Description (max 2000 characters)
    - Tags (array of strings)
    - Visibility (private/public/unlisted, default: private)

    **Snapshots Created:**
    - Pricing snapshot (current valuation data)
    - Metrics snapshot (current performance metrics)
    - Valuation breakdown (for transparency)

    **Share Token:**
    - Unique token generated for share URLs
    - Used for unlisted and public builds

    **Performance:**
    - Target: <500ms response time
    - Atomic transaction (all or nothing)

    **Use Cases:**
    - Saving custom build configurations
    - Creating shareable build links
    - Building collection of favorite configs
    """,
)
async def save_build(
    request: SaveBuildRequest,
    session: AsyncSession = Depends(session_dependency),
    # TODO: Get user_id from auth middleware when implemented
    user_id: Optional[int] = None,
) -> SavedBuildResponse:
    """Save a build with pricing and metrics snapshots.

    Generates share_token for URL sharing.
    Creates snapshots of current pricing and metrics.

    Args:
        request: Build save request with metadata and components
        session: Database session for persistence
        user_id: Optional user ID (from auth middleware when available)

    Returns:
        SavedBuildResponse with ID, timestamps, and share_token

    Raises:
        HTTPException(400): Validation error (missing name, invalid visibility)
        HTTPException(500): Save failed
    """
    try:
        normalized_user_id = normalize_user_id(user_id)

        logger.info(
            "save_build.start",
            name=request.name,
            visibility=request.visibility,
            user_id=normalized_user_id,
        )

        service = BuilderService(session)

        # Save build (service handles validation and snapshot creation)
        build = await service.save_build(request.model_dump(), normalized_user_id)

        # Commit transaction
        await session.commit()

        # Refresh to get updated timestamps
        await session.refresh(build)

        logger.info(
            "save_build.success",
            build_id=build.id,
            name=build.name,
            share_token=build.share_token,
        )

        return SavedBuildResponse.model_validate(build)

    except ValueError as e:
        await session.rollback()
        logger.warning("save_build.validation_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.error("save_build.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Save failed: {str(e)}"
        )


@router.get(
    "/builds",
    response_model=BuildListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's builds",
    description="""
    List user's saved builds with pagination.

    **Query Parameters:**
    - `limit`: Maximum builds to return (1-100, default: 10)
    - `offset`: Number of builds to skip (default: 0)

    **Ordering:**
    - Builds ordered by created_at DESC (newest first)

    **Access Control:**
    - Returns only builds owned by authenticated user
    - Anonymous users see empty list

    **Pagination:**
    - Use offset/limit for efficient pagination
    - Total count included for UI pagination controls

    **Performance:**
    - Target: <500ms response time
    - Indexed queries for fast retrieval

    **Use Cases:**
    - Build library/collection view
    - User dashboard
    - Build management interface
    """,
)
async def list_builds(
    limit: int = Query(10, ge=1, le=100, description="Maximum builds to return"),
    offset: int = Query(0, ge=0, description="Number of builds to skip"),
    session: AsyncSession = Depends(session_dependency),
    # TODO: Get user_id from auth middleware when implemented
    user_id: Optional[int] = None,
) -> BuildListResponse:
    """List user's saved builds with pagination.

    Ordered by created_at DESC (newest first).

    Args:
        limit: Maximum number of builds to return (1-100)
        offset: Number of builds to skip for pagination
        session: Database session for queries
        user_id: Optional user ID (from auth middleware when available)

    Returns:
        BuildListResponse with builds array and pagination metadata

    Raises:
        HTTPException(400): Invalid limit (>100)
    """
    try:
        logger.info("list_builds.start", limit=limit, offset=offset, user_id=user_id)

        if limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Limit cannot exceed 100"
            )

        service = BuilderService(session)

        # Get builds for user (returns empty list if user_id is None)
        builds = await service.get_user_builds(normalize_user_id(user_id), limit, offset)

        # Convert to response models
        build_responses = [SavedBuildResponse.model_validate(build) for build in builds]

        # TODO: Get actual total count from repository
        # For now, simplified approach
        total = len(build_responses)

        logger.info("list_builds.success", count=len(build_responses), total=total)

        return BuildListResponse(
            builds=build_responses,
            total=total,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_builds.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"List failed: {str(e)}"
        )


@router.get(
    "/builds/{build_id}",
    response_model=SavedBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single build by ID",
    description="""
    Get single build by ID with access control.

    **Access Control:**
    - **Public builds**: Accessible to anyone
    - **Unlisted builds**: Accessible to anyone (use share link)
    - **Private builds**: Only accessible to owner

    **Path Parameters:**
    - `build_id`: Unique build identifier

    **Returns:**
    - Full build data including snapshots
    - Component IDs for reconstruction
    - Timestamps and metadata

    **Use Cases:**
    - Build detail page
    - Build editor/viewer
    - Build sharing (public/unlisted)

    **Error Handling:**
    - 404: Build not found
    - 403: Access denied (private build, not owner)
    """,
)
async def get_build(
    build_id: int,
    session: AsyncSession = Depends(session_dependency),
    # TODO: Get user_id from auth middleware when implemented
    user_id: Optional[int] = None,
) -> SavedBuildResponse:
    """Get single build by ID.

    Access control:
    - Public builds: accessible to anyone
    - Unlisted builds: accessible via share token
    - Private builds: only accessible to owner

    Args:
        build_id: Build ID to retrieve
        session: Database session for queries
        user_id: Optional user ID (from auth middleware when available)

    Returns:
        SavedBuildResponse with full build data

    Raises:
        HTTPException(404): Build not found or access denied
    """
    try:
        logger.info("get_build.start", build_id=build_id, user_id=user_id)

        service = BuilderService(session)
        build = await service.get_build_by_id(build_id, user_id)

        if not build:
            logger.warning("get_build.not_found", build_id=build_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

        logger.info("get_build.success", build_id=build_id, name=build.name)

        return SavedBuildResponse.model_validate(build)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_build.error", build_id=build_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Get failed: {str(e)}"
        )


@router.patch(
    "/builds/{build_id}",
    response_model=SavedBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Update existing build",
    description="""
    Update existing build metadata and/or components.

    **Updatable Fields:**
    - name, description, tags
    - visibility
    - components (triggers recalculation of snapshots)

    **Access Control:**
    - Requires ownership for private builds
    - Public/unlisted builds may have different rules (TBD)

    **Snapshot Update:**
    - Component changes trigger snapshot recalculation
    - Metadata-only changes preserve existing snapshots

    **Use Cases:**
    - Renaming builds
    - Changing visibility
    - Updating component selection
    - Adding/editing description and tags
    """,
)
async def update_build(
    build_id: int,
    request: SaveBuildRequest,
    session: AsyncSession = Depends(session_dependency),
    # TODO: Get user_id from auth middleware when implemented
    user_id: Optional[int] = None,
) -> SavedBuildResponse:
    """Update existing build.

    Requires ownership for private builds.
    Component changes trigger snapshot recalculation.

    Args:
        build_id: Build ID to update
        request: Updated build data
        session: Database session for persistence
        user_id: Optional user ID (from auth middleware when available)

    Returns:
        SavedBuildResponse with updated data

    Raises:
        HTTPException(403): Access denied (not owner)
        HTTPException(404): Build not found
        HTTPException(500): Update failed
    """
    try:
        logger.info("update_build.start", build_id=build_id, user_id=user_id)

        service = BuilderService(session)

        # Update build (repository handles access control)
        try:
            build = await service.repository.update(
                build_id, request.model_dump(exclude_unset=True), normalize_user_id(user_id)
            )
        except ValueError as e:
            # Access denied or not found
            logger.warning("update_build.access_denied", build_id=build_id, error=str(e))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

        # Commit transaction
        await session.commit()
        await session.refresh(build)

        logger.info("update_build.success", build_id=build_id)

        return SavedBuildResponse.model_validate(build)

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error("update_build.error", build_id=build_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Update failed: {str(e)}"
        )


@router.delete(
    "/builds/{build_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete build",
    description="""
    Soft delete a build (sets deleted_at timestamp).

    **Access Control:**
    - Requires ownership
    - Only owner can delete their builds

    **Soft Delete:**
    - Build not actually removed from database
    - Sets deleted_at timestamp
    - Excluded from list/get queries
    - Can be restored by admin if needed

    **Use Cases:**
    - User deleting unwanted builds
    - Cleaning up build library
    - Accidental delete recovery (admin only)
    """,
)
async def delete_build(
    build_id: int,
    session: AsyncSession = Depends(session_dependency),
    # TODO: Get user_id from auth middleware when implemented
    user_id: Optional[int] = None,
) -> DeleteResponse:
    """Soft delete a build (sets deleted_at).

    Requires ownership.

    Args:
        build_id: Build ID to delete
        session: Database session for persistence
        user_id: Optional user ID (from auth middleware when available)

    Returns:
        DeleteResponse with deleted=True

    Raises:
        HTTPException(403): Access denied (not owner)
        HTTPException(404): Build not found
    """
    try:
        logger.info("delete_build.start", build_id=build_id, user_id=user_id)

        service = BuilderService(session)

        # Soft delete (repository handles access control)
        try:
            await service.repository.soft_delete(build_id, normalize_user_id(user_id))
        except ValueError as e:
            logger.warning("delete_build.access_denied", build_id=build_id, error=str(e))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

        # Commit transaction
        await session.commit()

        logger.info("delete_build.success", build_id=build_id)

        return DeleteResponse(deleted=True)

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error("delete_build.error", build_id=build_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Delete failed: {str(e)}"
        )


@router.get(
    "/builds/shared/{share_token}",
    response_model=SavedBuildResponse,
    status_code=status.HTTP_200_OK,
    summary="Get build by share token",
    description="""
    Get build via shareable URL (no authentication required).

    **Access:**
    - No authentication required
    - Works for public and unlisted builds
    - Private builds return 404 (not exposed)

    **Share Token:**
    - Unique token generated at build creation
    - Used in shareable URLs
    - Does not expire (currently)

    **Use Cases:**
    - Sharing build configs via link
    - Public build showcase
    - Forum/social media sharing

    **Security:**
    - Private builds never accessible via share token
    - Token is opaque (not guessable)
    - Rate limiting recommended (not implemented)
    """,
)
async def get_shared_build(
    share_token: str,
    session: AsyncSession = Depends(session_dependency),
) -> SavedBuildResponse:
    """Get build by share token (public/unlisted only).

    No authentication required.
    Private builds return 404.

    Args:
        share_token: Unique share token from URL
        session: Database session for queries

    Returns:
        SavedBuildResponse with full build data

    Raises:
        HTTPException(404): Build not found or private
    """
    try:
        logger.info("get_shared_build.start", share_token=share_token[:8])

        service = BuilderService(session)
        build = await service.repository.get_by_share_token(share_token)

        if not build:
            logger.warning("get_shared_build.not_found", share_token=share_token[:8])
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

        logger.info("get_shared_build.success", build_id=build.id, share_token=share_token[:8])

        return SavedBuildResponse.model_validate(build)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_shared_build.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Get failed: {str(e)}"
        )


@router.get(
    "/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare build to similar listings",
    description="""
    Find similar pre-built listings for comparison.

    **Query Parameters:**
    - `cpu_id`: CPU ID (required)
    - `ram_gb`: RAM amount in GB (optional)
    - `storage_gb`: Storage amount in GB (optional)
    - `limit`: Maximum listings to return (default: 5)

    **Matching Logic:**
    - Same CPU (preferred)
    - Similar RAM (±8GB tolerance)
    - Similar storage (±256GB tolerance)
    - Active listings only

    **Returns:**
    - List of similar listings
    - Price comparison
    - Similarity score (0-1)
    - Deal quality assessment

    **Use Cases:**
    - "Should I build or buy?" analysis
    - Price comparison with market
    - Finding pre-built alternatives

    **Performance:**
    - Cached listing data
    - Limited to top N matches
    - Sorted by similarity score
    """,
)
async def compare_to_listings(
    cpu_id: int = Query(..., gt=0, description="CPU ID (required)"),
    ram_gb: int = Query(0, ge=0, description="RAM amount in GB"),
    storage_gb: int = Query(0, ge=0, description="Storage amount in GB"),
    limit: int = Query(5, ge=1, le=20, description="Maximum listings to return"),
    session: AsyncSession = Depends(session_dependency),
) -> CompareResponse:
    """Find similar pre-built listings for comparison.

    Returns listings with same/similar specs.

    Args:
        cpu_id: CPU ID from build (required)
        ram_gb: Total RAM in GB (optional)
        storage_gb: Total storage in GB (optional)
        limit: Maximum number of listings to return
        session: Database session for queries

    Returns:
        CompareResponse with list of similar listings

    Raises:
        HTTPException(400): Invalid parameters (missing cpu_id)
        HTTPException(500): Comparison failed
    """
    try:
        logger.info(
            "compare_to_listings.start",
            cpu_id=cpu_id,
            ram_gb=ram_gb,
            storage_gb=storage_gb,
            limit=limit,
        )

        service = BuilderService(session)

        # Find similar listings
        comparisons = await service.compare_build_to_listings(cpu_id, ram_gb, storage_gb, limit)

        # Convert to response models
        listing_responses = [
            ListingComparisonResponse(
                listing_id=comp["listing_id"],
                name=comp["name"],
                price=comp["price"],
                adjusted_price=comp["adjusted_price"],
                deal_quality=comp["deal_quality"],
                price_difference=comp["price_difference"],
                similarity_score=comp["similarity_score"],
            )
            for comp in comparisons
        ]

        logger.info("compare_to_listings.success", count=len(listing_responses))

        return CompareResponse(listings=listing_responses)

    except ValueError as e:
        logger.warning("compare_to_listings.validation_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("compare_to_listings.error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Comparison failed: {str(e)}"
        )


__all__ = ["router"]
