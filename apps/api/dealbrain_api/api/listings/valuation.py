"""
Valuation endpoints for listings.

Handles valuation breakdowns, overrides, and ruleset management.
Extracted from monolithic listings.py for better modularity and maintainability.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db import session_dependency
from ...telemetry import get_logger
from ...models import Listing, ValuationRuleset, ValuationRuleV2, ValuationRuleGroup
from ...services.listings import (
    apply_listing_metrics,
    update_listing_overrides,
    VALUATION_DISABLED_RULESETS_KEY,
)
from ..schemas.listings import (
    LegacyValuationLine,
    ListingValuationOverrideRequest,
    ListingValuationOverrideResponse,
    ValuationAdjustmentAction,
    ValuationAdjustmentDetail,
    ValuationBreakdownResponse,
)

router = APIRouter()
logger = get_logger("dealbrain.api.listings.valuation")


def _serialize_listing_override(listing: Listing) -> ListingValuationOverrideResponse:
    """Helper function to serialize listing valuation overrides."""
    attrs = listing.attributes_json or {}
    disabled = [
        int(ruleset_id)
        for ruleset_id in attrs.get(VALUATION_DISABLED_RULESETS_KEY, [])
        if isinstance(ruleset_id, (int, str)) and str(ruleset_id).isdigit()
    ]
    mode = "static" if listing.ruleset_id else "auto"
    return ListingValuationOverrideResponse(
        mode=mode,
        ruleset_id=listing.ruleset_id,
        disabled_rulesets=disabled,
    )


@router.patch("/{listing_id}/valuation-overrides", response_model=ListingValuationOverrideResponse)
async def update_listing_valuation_overrides(
    listing_id: int,
    request: ListingValuationOverrideRequest,
    session: AsyncSession = Depends(session_dependency),
) -> ListingValuationOverrideResponse:
    """Update valuation overrides for a listing.

    Allows configuring:
    - Static ruleset assignment (mode='static')
    - Auto ruleset selection (mode='auto')
    - Disabled rulesets for the listing

    After updating overrides, recalculates listing metrics.
    """
    try:
        listing = await session.get(Listing, listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        if request.mode == "static":
            ruleset = await session.get(ValuationRuleset, request.ruleset_id)
            if not ruleset:
                raise HTTPException(status_code=404, detail="Ruleset not found")
            if not ruleset.is_active:
                raise HTTPException(
                    status_code=400, detail="Ruleset is inactive and cannot be assigned"
                )

        try:
            await update_listing_overrides(
                session,
                listing,
                mode=request.mode,
                ruleset_id=request.ruleset_id,
                disabled_rulesets=request.disabled_rulesets,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        await apply_listing_metrics(session, listing)
        await session.refresh(listing)
        return _serialize_listing_override(listing)
    except HTTPException:
        # Re-raise HTTPException without catching it
        raise
    except OperationalError as e:
        logger.error(
            f"Database connection error in update_listing_valuation_overrides (id={listing_id}): {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later.",
        )
    except ProgrammingError as e:
        logger.error(
            f"Database schema error in update_listing_valuation_overrides (id={listing_id}): {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support.",
        )
    except DatabaseError as e:
        logger.error(f"Database error in update_listing_valuation_overrides (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later.",
        )


@router.get("/{listing_id}/valuation-breakdown", response_model=ValuationBreakdownResponse)
async def get_valuation_breakdown(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> ValuationBreakdownResponse:
    """Get detailed valuation breakdown for a listing.

    This endpoint returns the detailed breakdown of how a listing's adjusted price
    was calculated, including all applied rules and their individual contributions,
    as well as inactive rules from the same ruleset.

    Args:
        listing_id: ID of the listing to get breakdown for
        session: Database session

    Returns:
        Detailed valuation breakdown with enriched rule metadata

    Raises:
        404: Listing not found
    """
    try:
        # Get listing
        result = await session.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Listing {listing_id} not found"
            )

        breakdown = listing.valuation_breakdown or {}
        ruleset_info = breakdown.get("ruleset") or {}

        # Parse active adjustments from breakdown JSON
        adjustments_payload = breakdown.get("adjustments") or []
        active_rule_ids = {
            payload.get("rule_id")
            for payload in adjustments_payload
            if payload.get("rule_id") is not None
        }

        # Query ValuationRuleV2 with eager loading for active rules
        rules_by_id: dict[int, ValuationRuleV2] = {}
        if active_rule_ids:
            stmt = (
                select(ValuationRuleV2)
                .options(selectinload(ValuationRuleV2.group))
                .where(ValuationRuleV2.id.in_(active_rule_ids))
            )
            rules_result = await session.execute(stmt)
            rules_by_id = {rule.id: rule for rule in rules_result.scalars().all()}

        # Enrich active adjustments with database metadata
        adjustments: list[ValuationAdjustmentDetail] = []
        for payload in adjustments_payload:
            actions_payload = payload.get("actions") or []
            actions = [
                ValuationAdjustmentAction(
                    action_type=action.get("action_type"),
                    metric=action.get("metric"),
                    value=float(action.get("value") or 0.0),
                    details=action.get("details"),
                    error=action.get("error"),
                )
                for action in actions_payload
            ]

            rule_id = payload.get("rule_id")
            rule = rules_by_id.get(rule_id) if rule_id else None

            adjustments.append(
                ValuationAdjustmentDetail(
                    rule_id=rule_id,
                    rule_name=payload.get("rule_name") or "Unnamed Rule",
                    rule_description=rule.description if rule else None,
                    rule_group_id=rule.group_id if rule else None,
                    rule_group_name=rule.group.name if rule and rule.group else None,
                    adjustment_amount=float(payload.get("adjustment_usd") or 0.0),
                    actions=actions,
                )
            )

        # Get ruleset ID from first rule to query inactive rules
        ruleset_id = None
        if rules_by_id:
            first_rule = next(iter(rules_by_id.values()))
            ruleset_id = first_rule.group.ruleset_id if first_rule.group else None

        # Query and include inactive rules from the same ruleset
        if ruleset_id and active_rule_ids:
            inactive_stmt = (
                select(ValuationRuleV2)
                .join(ValuationRuleV2.group)
                .options(selectinload(ValuationRuleV2.group))
                .where(
                    ValuationRuleGroup.ruleset_id == ruleset_id,
                    ValuationRuleV2.id.notin_(active_rule_ids),
                )
            )
            inactive_result = await session.execute(inactive_stmt)
            inactive_rules = inactive_result.scalars().all()

            # Add zero-adjustment entries for inactive rules
            for rule in inactive_rules:
                adjustments.append(
                    ValuationAdjustmentDetail(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        rule_description=rule.description,
                        rule_group_id=rule.group_id,
                        rule_group_name=rule.group.name if rule.group else None,
                        adjustment_amount=0.0,
                        actions=[],
                    )
                )

        # Parse legacy lines
        legacy_payload = breakdown.get("legacy_lines") or breakdown.get("lines") or []
        legacy_lines: list[LegacyValuationLine] = []
        for line in legacy_payload:
            adjustment_usd = line.get("adjustment_usd")
            legacy_lines.append(
                LegacyValuationLine(
                    label=line.get("label", "Unknown"),
                    component_type=line.get("component_type", "component"),
                    quantity=float(line.get("quantity") or 0.0),
                    unit_value=float(line.get("unit_value") or 0.0),
                    condition_multiplier=float(line.get("condition_multiplier") or 1.0),
                    deduction_usd=float(line.get("deduction_usd") or 0.0),
                    adjustment_usd=float(adjustment_usd) if adjustment_usd is not None else None,
                )
            )

        # Calculate totals (only from active adjustments, not inactive)
        total_adjustment = float(
            breakdown.get("total_adjustment")
            or sum(adj.adjustment_amount for adj in adjustments if adj.adjustment_amount != 0.0)
        )
        total_deductions = breakdown.get("total_deductions")
        if total_deductions is not None:
            total_deductions = float(total_deductions)

        # Count only active rules (non-zero adjustments)
        matched_rules_count = int(
            breakdown.get("matched_rules_count")
            or sum(1 for adj in adjustments if adj.adjustment_amount != 0.0)
        )

        return ValuationBreakdownResponse(
            listing_id=listing.id,
            listing_title=listing.title,
            base_price_usd=float(listing.price_usd or 0.0),
            adjusted_price_usd=float(listing.adjusted_price_usd or listing.price_usd or 0.0),
            total_adjustment=total_adjustment,
            total_deductions=total_deductions,
            matched_rules_count=matched_rules_count,
            ruleset_id=ruleset_info.get("id"),
            ruleset_name=ruleset_info.get("name") or breakdown.get("ruleset_name"),
            adjustments=adjustments,
            legacy_lines=legacy_lines,
        )
    except HTTPException:
        # Re-raise HTTPException without catching it
        raise
    except OperationalError as e:
        logger.error(f"Database connection error in get_valuation_breakdown (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later.",
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in get_valuation_breakdown (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support.",
        )
    except DatabaseError as e:
        logger.error(f"Database error in get_valuation_breakdown (id={listing_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later.",
        )
