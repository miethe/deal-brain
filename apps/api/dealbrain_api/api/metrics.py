"""API endpoints for baseline metrics."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency as get_session
from ..services.baseline_metrics import BaselineMetricsService

router = APIRouter(prefix="/api/v1/baseline", tags=["baseline", "metrics"])


@router.get("/metrics")
async def get_baseline_metrics(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get comprehensive baseline metrics.

    Returns metrics about:
    - Layer influence (% of listings affected by each layer)
    - Top contributing rules by absolute value
    - Override churn rates
    - Current baseline information

    Returns:
        Dictionary with baseline metrics
    """
    service = BaselineMetricsService()
    metrics = await service.get_baseline_summary(session)
    return metrics


@router.get("/metrics/layer-influence")
async def get_layer_influence(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get percentage of listings influenced by each valuation layer.

    Returns:
        Dictionary with layer names and percentages
    """
    service = BaselineMetricsService()
    influence = await service.calculate_layer_influence(session)
    return {"layer_influence": influence}


@router.get("/metrics/top-rules")
async def get_top_rules(
    limit: int = Query(10, ge=1, le=50, description="Number of top rules to return"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get top rules by absolute contribution amount.

    Args:
        limit: Number of top rules to return (1-50)
        days: Number of days to look back for aggregation (1-365)

    Returns:
        List of top contributing rules
    """
    service = BaselineMetricsService()
    rules = await service.get_top_rules_by_contribution(
        session, limit=limit, days_back=days
    )
    return {
        "top_rules": rules,
        "period_days": days,
        "limit": limit
    }


@router.get("/metrics/override-churn")
async def get_override_churn(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get override churn rate over specified period.

    Args:
        days: Number of days to analyze (1-90)

    Returns:
        Dictionary with churn metrics
    """
    service = BaselineMetricsService()
    churn = await service.calculate_override_churn(session, days_back=days)
    return churn