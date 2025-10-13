"""API endpoints for baseline valuation management"""

from pathlib import Path

from dealbrain_core.schemas.baseline import (
    BaselineAdoptRequest,
    BaselineAdoptResponse,
    BaselineDiffRequest,
    BaselineDiffResponse,
    BaselineInstantiateRequest,
    BaselineInstantiateResponse,
    BaselineMetadataResponse,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency as get_session
from ..services.baseline_loader import BaselineLoaderService

router = APIRouter(prefix="/api/v1/baseline", tags=["baseline"])


# --- Baseline Metadata Endpoint ---

@router.get("/meta", response_model=BaselineMetadataResponse | None)
async def get_baseline_metadata(
    session: AsyncSession = Depends(get_session),
):
    """Get metadata for the currently active baseline ruleset.

    Returns baseline field definitions, version info, and source hash.
    Public endpoint for UI metadata population.

    Returns:
        BaselineMetadataResponse if active baseline exists, None otherwise
    """
    service = BaselineLoaderService()
    metadata = await service.get_baseline_metadata(session)

    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active baseline ruleset found"
        )

    return metadata


# --- Baseline Instantiation Endpoint ---

@router.post("/instantiate", response_model=BaselineInstantiateResponse)
async def instantiate_baseline(
    request: BaselineInstantiateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Instantiate a baseline ruleset from a JSON file (idempotent).

    If a ruleset with the same source hash already exists, returns existing
    ruleset info with created=false. Otherwise creates new baseline ruleset.

    Requires: baseline:admin permission (RBAC integration point)

    Args:
        request: Contains baseline_path, create_adjustments_group flag, and actor

    Returns:
        BaselineInstantiateResponse with ruleset info and creation status
    """
    service = BaselineLoaderService()
    baseline_path = Path(request.baseline_path)

    # Validate path exists
    if not baseline_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Baseline file not found: {request.baseline_path}"
        )

    # Load baseline (idempotent)
    try:
        result = await service.load_from_path(
            session=session,
            source_path=baseline_path,
            actor=request.actor or "api_user",
            ensure_basic_for_ruleset=None if not request.create_adjustments_group else 0,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to instantiate baseline: {str(e)}",
        ) from e

    # Map result to response schema
    return BaselineInstantiateResponse(
        ruleset_id=result.ruleset_id,
        version=result.version,
        created=result.status == "created",
        hash_match=(
            result.status == "skipped" and result.skipped_reason == "ruleset_with_hash_exists"
        ),
        source_hash=result.source_hash,
        ruleset_name=result.ruleset_name,
        created_groups=result.created_groups,
        created_rules=result.created_rules,
        skipped_reason=result.skipped_reason,
    )


# --- Baseline Diff Endpoint ---

@router.post("/diff", response_model=BaselineDiffResponse)
async def diff_baseline(
    request: BaselineDiffRequest,
    session: AsyncSession = Depends(get_session),
):
    """Compare candidate baseline JSON against current active baseline.

    Returns field-level granular diff showing added, changed, and removed fields.

    Requires: baseline:admin permission (RBAC integration point)

    Args:
        request: Contains candidate_json and optional actor

    Returns:
        BaselineDiffResponse with added, changed, removed fields and summary
    """
    service = BaselineLoaderService()

    try:
        diff_result = await service.diff_baseline(
            session=session,
            candidate_json=request.candidate_json,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to diff baseline: {str(e)}",
        ) from e

    return diff_result


# --- Baseline Adopt Endpoint ---

@router.post("/adopt", response_model=BaselineAdoptResponse)
async def adopt_baseline(
    request: BaselineAdoptRequest,
    session: AsyncSession = Depends(get_session),
):
    """Adopt selected changes from candidate baseline, creating new version.

    Creates a NEW baseline ruleset version with selected changes. Never mutates existing
    rulesets. Previous baseline is deactivated automatically.

    Requires: baseline:admin permission (RBAC integration point)

    Args:
        request: Contains candidate_json, optional selected_changes,
                 trigger_recalculation, and actor

    Returns:
        BaselineAdoptResponse with new ruleset info and audit details
    """
    service = BaselineLoaderService()

    try:
        adopt_result = await service.adopt_baseline(
            session=session,
            candidate_json=request.candidate_json,
            selected_changes=request.selected_changes,
            actor=request.actor or "api_user",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adopt baseline: {str(e)}",
        ) from e

    # Handle recalculation trigger if requested
    recalculation_job_id = None
    if request.trigger_recalculation and adopt_result.get("new_ruleset_id"):
        # Import here to avoid circular dependency
        from ..tasks import enqueue_listing_recalculation

        try:
            job = enqueue_listing_recalculation(
                ruleset_id=adopt_result["new_ruleset_id"], reason="baseline_adopted"
            )
            recalculation_job_id = str(job.id) if job else None
        except Exception:  # noqa: S110
            # Non-fatal: recalculation can be triggered manually
            pass

    return BaselineAdoptResponse(
        new_ruleset_id=adopt_result["new_ruleset_id"],
        new_version=adopt_result["new_version"],
        changes_applied=adopt_result["changes_applied"],
        recalculation_job_id=recalculation_job_id,
        adopted_fields=adopt_result["adopted_fields"],
        skipped_fields=adopt_result["skipped_fields"],
        previous_ruleset_id=adopt_result.get("previous_ruleset_id"),
        audit_log_id=adopt_result.get("audit_log_id"),
    )
