"""API endpoints for rule evaluation, preview, validation, and audit"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import session_dependency as get_session
from ...schemas.rules import (
    RulePreviewRequest,
    RulePreviewResponse,
    RuleEvaluationResponse,
    ApplyRulesetRequest,
    AuditLogResponse,
    FormulaValidationRequest,
    FormulaValidationResponse,
    FormulaValidationError,
)
from ...services.rules import RulesService
from ...services.rule_evaluation import RuleEvaluationService
from ...services.rule_preview import RulePreviewService
from ...services.formula_validation import FormulaValidationService


logger = logging.getLogger(__name__)
router = APIRouter()


# --- Preview Endpoints ---


@router.post("/valuation-rules/preview", response_model=RulePreviewResponse)
async def preview_rule(
    request: RulePreviewRequest,
    session: AsyncSession = Depends(get_session),
):
    """Preview impact of a rule before saving"""
    service = RulePreviewService()

    conditions = [c.dict() for c in request.conditions]
    actions = [a.dict() for a in request.actions]

    result = await service.preview_rule(
        session=session,
        conditions=conditions,
        actions=actions,
        sample_size=request.sample_size,
        category_filter=request.category_filter,
    )

    return RulePreviewResponse(**result)


@router.post("/valuation-rules/validate-formula", response_model=FormulaValidationResponse)
async def validate_formula(
    request: FormulaValidationRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Validate a formula and provide preview calculation.

    This endpoint:
    - Validates formula syntax
    - Checks field availability against entity metadata
    - Calculates preview with sample data (either provided or from database)
    - Returns list of used fields from formula
    - Provides helpful error messages with suggestions

    Example formulas:
    - "ram_gb * 2.5" - Simple per-GB pricing
    - "cpu_mark_multi / 1000 * 5.0" - Benchmark-based calculation
    - "max(ram_gb * 2.5, 50)" - Minimum value enforcement
    - "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0" - Conditional pricing
    """
    service = FormulaValidationService()

    try:
        result = await service.validate_formula(
            session=session,
            formula=request.formula,
            entity_type=request.entity_type,
            sample_context=request.sample_context,
        )

        # Convert error dictionaries to Pydantic models
        errors = [
            FormulaValidationError(
                message=error["message"],
                severity=error["severity"],
                position=error.get("position"),
                suggestion=error.get("suggestion"),
            )
            for error in result["errors"]
        ]

        return FormulaValidationResponse(
            valid=result["valid"],
            errors=errors,
            preview=result["preview"],
            used_fields=result["used_fields"],
            available_fields=result["available_fields"],
        )

    except Exception as e:
        logger.error(f"Formula validation failed with unexpected error: {e}", exc_info=True)
        # Return error response instead of raising exception
        return FormulaValidationResponse(
            valid=False,
            errors=[
                FormulaValidationError(
                    message=f"Validation failed: {str(e)}",
                    severity="error",
                    position=None,
                    suggestion="Please check the formula syntax and try again",
                )
            ],
            preview=None,
            used_fields=[],
            available_fields=[],
        )


# --- Evaluation Endpoints ---


@router.post("/valuation-rules/evaluate/{listing_id}", response_model=RuleEvaluationResponse)
async def evaluate_listing(
    listing_id: int,
    ruleset_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Evaluate a single listing with a ruleset"""
    service = RuleEvaluationService()

    try:
        result = await service.evaluate_listing(session, listing_id, ruleset_id)
        return RuleEvaluationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/valuation-rules/apply")
async def apply_ruleset(
    request: ApplyRulesetRequest,
    session: AsyncSession = Depends(get_session),
):
    """Apply a ruleset to listings"""
    service = RuleEvaluationService()

    if request.listing_ids:
        # Apply to specific listings
        results = []
        for listing_id in request.listing_ids:
            try:
                result = await service.apply_ruleset_to_listing(
                    session, listing_id, request.ruleset_id
                )
                results.append(result)
            except Exception as e:
                results.append({"listing_id": listing_id, "error": str(e)})

        return {"results": results}
    else:
        # Apply to all active listings
        result = await service.apply_ruleset_to_all_listings(session, request.ruleset_id)
        return result


# --- Audit Endpoints ---


@router.get("/valuation-rules/audit-log", response_model=list[AuditLogResponse])
async def get_audit_log(
    rule_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Get audit log for rules"""
    service = RulesService()
    logs = await service.get_audit_log(session, rule_id=rule_id, limit=limit)

    return [
        AuditLogResponse(
            id=log.id,
            rule_id=log.rule_id,
            action=log.action,
            actor=log.actor,
            changes=log.changes_json,
            impact_summary=log.impact_summary,
            created_at=log.created_at,
        )
        for log in logs
    ]
