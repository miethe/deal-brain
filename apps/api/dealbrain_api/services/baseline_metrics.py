"""Service for aggregating baseline valuation metrics."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from ..models.core import (
    Listing,
    ValuationRuleset,
    ValuationRuleV2,
    ValuationRuleGroup,
)

logger = logging.getLogger(__name__)


class BaselineMetricsService:
    """Service for calculating and aggregating baseline metrics."""

    async def calculate_layer_influence(
        self, session: AsyncSession
    ) -> dict[str, float]:
        """Calculate percentage of listings influenced by each layer.

        Returns:
            Dictionary with layer names and percentages
        """
        # Get total active listings count
        total_stmt = select(func.count(Listing.id)).where(
            Listing.status == "active"
        )
        total_result = await session.execute(total_stmt)
        total_listings = total_result.scalar() or 0

        if total_listings == 0:
            return {
                "baseline": 0.0,
                "basic": 0.0,
                "advanced": 0.0
            }

        # Query listings with valuation_breakdown containing each layer
        layer_counts = {}

        for layer in ["baseline", "basic", "advanced"]:
            # Count listings where this layer has matched rules
            stmt = select(func.count(Listing.id)).where(
                and_(
                    Listing.status == "active",
                    Listing.valuation_breakdown.op("->>")("layers").contains(f'"{layer}"')
                )
            )
            result = await session.execute(stmt)
            count = result.scalar() or 0
            layer_counts[layer] = (count / total_listings) * 100

        return layer_counts

    async def get_top_rules_by_contribution(
        self,
        session: AsyncSession,
        limit: int = 10,
        days_back: int = 30
    ) -> list[dict[str, Any]]:
        """Get top rules by absolute contribution amount.

        Args:
            session: Database session
            limit: Number of top rules to return
            days_back: Number of days to look back for aggregation

        Returns:
            List of rule dictionaries with contribution data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Aggregate rule contributions from valuation_breakdown JSON
        stmt = text("""
            WITH rule_contributions AS (
                SELECT
                    rule_data->>'rule_id' as rule_id,
                    rule_data->>'rule_name' as rule_name,
                    (rule_data->>'adjustment')::numeric as adjustment,
                    l.id as listing_id
                FROM listing l,
                     jsonb_array_elements(
                        jsonb_array_elements(l.valuation_breakdown->'layers')->'matched_rules'
                     ) as rule_data
                WHERE l.status = 'active'
                  AND l.updated_at >= :cutoff_date
                  AND l.valuation_breakdown IS NOT NULL
            )
            SELECT
                rule_id::integer,
                rule_name,
                COUNT(DISTINCT listing_id) as affected_listings,
                AVG(ABS(adjustment)) as avg_adjustment,
                SUM(ABS(adjustment)) as total_adjustment,
                MAX(ABS(adjustment)) as max_adjustment
            FROM rule_contributions
            WHERE adjustment != 0
            GROUP BY rule_id, rule_name
            ORDER BY total_adjustment DESC
            LIMIT :limit
        """)

        result = await session.execute(
            stmt,
            {"cutoff_date": cutoff_date, "limit": limit}
        )

        rules = []
        for row in result:
            rules.append({
                "rule_id": row[0],
                "rule_name": row[1],
                "affected_listings": row[2],
                "avg_adjustment_usd": float(row[3]) if row[3] else 0,
                "total_adjustment_usd": float(row[4]) if row[4] else 0,
                "max_adjustment_usd": float(row[5]) if row[5] else 0
            })

        return rules

    async def calculate_override_churn(
        self,
        session: AsyncSession,
        days_back: int = 7
    ) -> dict[str, Any]:
        """Calculate override churn rate over specified period.

        Args:
            session: Database session
            days_back: Number of days to analyze

        Returns:
            Dictionary with churn metrics

        Note:
            This method currently returns placeholder data until the EntityFieldValue
            model is implemented. This is part of the baseline valuation enhancement
            feature and will be fully functional once the field value storage model
            is created.
        """
        # TODO: Implement once EntityFieldValue model is created
        # This model will track baseline field overrides for churn rate calculation
        logger.warning(
            "calculate_override_churn called but EntityFieldValue model not yet implemented"
        )

        return {
            "period_days": days_back,
            "total_overrides": 0,
            "new_overrides": 0,
            "changed_overrides": 0,
            "churn_rate_percent": 0.0,
            "calculated_at": datetime.utcnow().isoformat(),
            "note": "EntityFieldValue model not yet implemented - placeholder data"
        }

    async def get_baseline_summary(
        self, session: AsyncSession
    ) -> dict[str, Any]:
        """Get comprehensive baseline metrics summary.

        Returns:
            Dictionary with all baseline metrics
        """
        # Get layer influence
        layer_influence = await self.calculate_layer_influence(session)

        # Get top rules
        top_rules = await self.get_top_rules_by_contribution(session)

        # Get override churn for different periods
        churn_7d = await self.calculate_override_churn(session, days_back=7)
        churn_30d = await self.calculate_override_churn(session, days_back=30)

        # Get active baseline info
        baseline_stmt = select(ValuationRuleset).where(
            and_(
                ValuationRuleset.is_active == True,
                ValuationRuleset.metadata_json.op("->>")(
                    "system_baseline"
                ) == "true"
            )
        ).order_by(ValuationRuleset.priority.asc())

        baseline_result = await session.execute(baseline_stmt)
        baseline_ruleset = baseline_result.scalar_one_or_none()

        baseline_info = None
        if baseline_ruleset:
            baseline_info = {
                "id": baseline_ruleset.id,
                "name": baseline_ruleset.name,
                "version": baseline_ruleset.metadata_json.get("version", "unknown"),
                "source_hash": baseline_ruleset.metadata_json.get("source_hash", "unknown"),
                "created_at": baseline_ruleset.created_at.isoformat(),
                "age_days": (datetime.utcnow() - baseline_ruleset.created_at).days
            }

        return {
            "baseline": baseline_info,
            "layer_influence": layer_influence,
            "top_rules": top_rules[:10],
            "override_churn": {
                "7_day": churn_7d,
                "30_day": churn_30d
            },
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def store_metrics_snapshot(
        self,
        session: AsyncSession,
        metrics: dict[str, Any]
    ) -> None:
        """Store metrics snapshot for historical tracking.

        Args:
            session: Database session
            metrics: Metrics to store
        """
        # Store in Redis cache or dedicated metrics table
        # For now, just log the metrics
        logger.info("Baseline metrics snapshot", extra=metrics)