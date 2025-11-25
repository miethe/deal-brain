"""Health check endpoints for baseline system."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency as get_session
from ..models.core import ValuationRuleset, ValuationRuleGroup

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/baseline")
async def check_baseline_health(
    expected_hash: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Check health of baseline valuation system.

    Checks:
    - At least one active baseline ruleset exists
    - Baseline source_hash matches expected (if provided)
    - No stale baselines (warn if > 90 days old)
    - Basic Adjustments group exists in target ruleset

    Args:
        expected_hash: Expected source hash for baseline (optional)

    Returns:
        Health status with detailed check results
    """
    warnings = []
    errors = []
    checks = {
        "baseline_exists": False,
        "baseline_version": None,
        "baseline_age_days": None,
        "adjustments_group_exists": False,
        "hash_match": None if expected_hash is None else False,
    }

    # Check for active baseline ruleset
    baseline_stmt = (
        select(ValuationRuleset)
        .where(
            and_(
                ValuationRuleset.is_active == True,
                ValuationRuleset.metadata_json.op("->>")("system_baseline") == "true",
            )
        )
        .order_by(ValuationRuleset.priority.asc())
    )

    baseline_result = await session.execute(baseline_stmt)
    baseline_ruleset = baseline_result.scalar_one_or_none()

    if baseline_ruleset:
        checks["baseline_exists"] = True
        metadata = baseline_ruleset.metadata_json or {}
        checks["baseline_version"] = metadata.get("version", "unknown")

        # Calculate age
        age_days = (datetime.utcnow() - baseline_ruleset.created_at).days
        checks["baseline_age_days"] = age_days

        # Check if baseline is stale
        if age_days > 90:
            warnings.append(f"Baseline is {age_days} days old, consider updating")

        # Check hash match if expected
        if expected_hash is not None:
            actual_hash = metadata.get("source_hash", "")
            checks["hash_match"] = actual_hash == expected_hash
            if not checks["hash_match"]:
                errors.append(
                    f"Baseline hash mismatch: expected={expected_hash[:8]}..., "
                    f"actual={actual_hash[:8] if actual_hash else 'none'}..."
                )

        # Check for Basic Adjustments group in any active ruleset
        group_stmt = select(func.count(ValuationRuleGroup.id)).where(
            and_(
                ValuationRuleGroup.name == "Basic · Adjustments",
                ValuationRuleGroup.is_active == True,
            )
        )
        group_result = await session.execute(group_stmt)
        group_count = group_result.scalar() or 0
        checks["adjustments_group_exists"] = group_count > 0

        if not checks["adjustments_group_exists"]:
            warnings.append("No Basic Adjustments group found in any active ruleset")

    else:
        errors.append("No active baseline ruleset found")

    # Determine overall status
    if errors:
        status = "error"
    elif warnings:
        status = "warning"
    else:
        status = "healthy"

    return {
        "status": status,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/")
async def check_overall_health(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Check overall system health including baseline subsystem.

    Returns:
        Overall health status
    """
    # Check baseline health
    baseline_health = await check_baseline_health(session=session)

    # Add other health checks here as needed
    subsystems = {
        "baseline": baseline_health["status"],
        "database": "healthy",  # Assume healthy if we got this far
        "api": "healthy",
    }

    # Determine overall status
    if any(status == "error" for status in subsystems.values()):
        overall_status = "error"
    elif any(status == "warning" for status in subsystems.values()):
        overall_status = "warning"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "subsystems": subsystems,
        "timestamp": datetime.utcnow().isoformat(),
    }
