"""API endpoints for baseline valuation management"""

from datetime import datetime
from pathlib import Path
from typing import Any

from dealbrain_core.schemas.baseline import (
    BaselineAdoptRequest,
    BaselineAdoptResponse,
    BaselineDiffRequest,
    BaselineDiffResponse,
    BaselineInstantiateRequest,
    BaselineInstantiateResponse,
    BaselineMetadataResponse,
    HydrateBaselineRequest,
    HydrateBaselineResponse,
    HydrationSummaryItem,
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


@router.get("/metadata", response_model=BaselineMetadataResponse | None)
async def get_baseline_metadata_alias(
    session: AsyncSession = Depends(get_session),
):
    """Alias for /meta endpoint for backwards compatibility.

    Returns:
        BaselineMetadataResponse if active baseline exists, None otherwise
    """
    return await get_baseline_metadata(session)


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


# --- Baseline Hydration Endpoint ---

@router.post("/rulesets/{ruleset_id}/hydrate", response_model=HydrateBaselineResponse)
async def hydrate_baseline_rules(
    ruleset_id: int,
    request: HydrateBaselineRequest,
    session: AsyncSession = Depends(get_session),
):
    """Hydrate placeholder baseline rules for Advanced mode editing.

    Converts compact baseline placeholder rules into expanded, editable rules
    with explicit conditions and actions. This enables the transition from
    Basic mode (compact baseline) to Advanced mode (full rule editing).

    Requires: baseline:admin permission (RBAC integration point)

    Args:
        ruleset_id: ID of the ruleset containing placeholder rules to hydrate
        request: Contains optional actor field

    Returns:
        HydrateBaselineResponse with status, counts, and hydration summary

    Raises:
        HTTPException: 404 if ruleset not found, 500 if hydration fails
    """
    from ..services.baseline_hydration import BaselineHydrationService
    from ..models.core import ValuationRuleset
    from sqlalchemy import select

    # Verify ruleset exists
    stmt = select(ValuationRuleset).where(ValuationRuleset.id == ruleset_id)
    result = await session.execute(stmt)
    ruleset = result.scalar_one_or_none()

    if not ruleset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruleset {ruleset_id} not found"
        )

    # Hydrate rules
    service = BaselineHydrationService()
    try:
        hydration_result = await service.hydrate_baseline_rules(
            session=session,
            ruleset_id=ruleset_id,
            actor=request.actor or "system"
        )

        return HydrateBaselineResponse(
            status=hydration_result.status,
            ruleset_id=hydration_result.ruleset_id,
            hydrated_rule_count=hydration_result.hydrated_rule_count,
            created_rule_count=hydration_result.created_rule_count,
            hydration_summary=[
                HydrationSummaryItem(
                    original_rule_id=item["original_rule_id"],
                    field_name=item["field_name"],
                    field_type=item["field_type"],
                    expanded_rule_ids=item["expanded_rule_ids"],
                )
                for item in hydration_result.hydration_summary
            ],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to hydrate baseline rules: {str(e)}",
        ) from e


# --- Field Override Endpoints (Stub implementations) ---

@router.get("/overrides/{entity_key}")
async def get_entity_overrides(
    entity_key: str,
    session: AsyncSession = Depends(get_session),
):
    """Get all field overrides for an entity.

    TODO: Implement full override management via Basic Adjustments group.
    For now, returns empty list to allow UI to load.

    Args:
        entity_key: Entity identifier (e.g., 'listing', 'cpu', 'gpu')

    Returns:
        List of field overrides (currently empty stub)
    """
    # Stub: Return empty list for now
    # TODO: Query ValuationRuleGroup where group_name='Basic · Adjustments'
    # and metadata_json->entity_key = entity_key, extract modifiers_json
    return []


@router.post("/overrides")
async def upsert_field_override(
    override: dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """Create or update a field override.

    TODO: Implement by updating modifiers_json in Basic Adjustments group.
    For now, returns the input unchanged.

    Args:
        override: Field override data (field_name, entity_key, override_value, etc.)

    Returns:
        The created/updated override (currently echo stub)
    """
    # Stub: Echo back the input
    # TODO: Update ValuationRuleGroup modifiers_json for the specified entity/field
    return override


@router.delete("/overrides/{entity_key}/{field_name}")
async def delete_field_override(
    entity_key: str,
    field_name: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a specific field override (reset to baseline).

    TODO: Implement by removing field from modifiers_json.

    Args:
        entity_key: Entity identifier
        field_name: Field name to reset

    Returns:
        Success status
    """
    # Stub: Return success
    # TODO: Remove field from modifiers_json in Basic Adjustments group
    return {"status": "deleted", "entity_key": entity_key, "field_name": field_name}


@router.delete("/overrides/{entity_key}")
async def delete_entity_overrides(
    entity_key: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete all overrides for an entity.

    TODO: Implement by clearing modifiers_json for entity.

    Args:
        entity_key: Entity identifier

    Returns:
        Success status
    """
    # Stub: Return success
    # TODO: Clear all modifiers_json for entity in Basic Adjustments group
    return {"status": "deleted", "entity_key": entity_key, "count": 0}


# --- Preview Impact Endpoint (Stub) ---

@router.get("/preview")
async def preview_impact(
    entity_key: str | None = None,
    sample_size: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Preview the impact of current overrides on listings.

    TODO: Implement by running evaluation with/without overrides.
    For now, returns stub data.

    Args:
        entity_key: Optional entity filter
        sample_size: Number of listings to sample

    Returns:
        Preview statistics and sample listings
    """
    # Stub: Return minimal structure
    return {
        "statistics": {
            "total_listings": 0,
            "matched_count": 0,
            "match_percentage": 0.0,
            "avg_delta": 0.0,
            "min_delta": 0.0,
            "max_delta": 0.0,
            "median_delta": 0.0,
        },
        "samples": [],
        "generated_at": datetime.utcnow().isoformat(),
    }


# --- Export Endpoint (Stub) ---

@router.get("/export")
async def export_baseline(
    session: AsyncSession = Depends(get_session),
):
    """Export current baseline configuration including overrides.

    TODO: Implement by serializing active baseline + overrides.

    Returns:
        Baseline metadata with current overrides applied
    """
    # Stub: Delegate to metadata endpoint for now
    service = BaselineLoaderService()
    metadata = await service.get_baseline_metadata(session)

    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active baseline to export"
        )

    return metadata


# --- Validate Endpoint (Stub) ---

@router.post("/validate")
async def validate_baseline(
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
):
    """Validate a baseline JSON structure.

    TODO: Implement schema validation and constraint checking.

    Args:
        payload: Contains baseline_json or baseline object

    Returns:
        Validation result with errors/warnings
    """
    # Stub: Always return valid for now
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
    }
