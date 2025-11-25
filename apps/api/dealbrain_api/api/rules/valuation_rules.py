"""API endpoints for individual valuation rule management (CRUD operations)"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import session_dependency as get_session
from ...schemas.rules import (
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleResponse,
    ConditionSchema,
    ActionSchema,
)
from ...services.rules import RulesService
from ...validation.rules_validation import (
    validate_basic_managed_group,
    validate_modifiers_json,
)


router = APIRouter()


@router.post("/valuation-rules", response_model=RuleResponse)
async def create_rule(
    request: RuleCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new valuation rule"""
    service = RulesService()

    # Check if the parent group is basic-managed
    group = await service.get_rule_group(session, request.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Rule group not found")

    # Validate modifiers for each action
    if request.actions:
        for action in request.actions:
            validate_modifiers_json(action.modifiers, action.action_type)

    conditions = [c.dict() for c in request.conditions] if request.conditions else []
    actions = [a.dict() for a in request.actions] if request.actions else []

    try:
        rule = await service.create_rule(
            session=session,
            group_id=request.group_id,
            name=request.name,
            description=request.description,
            priority=request.priority,
            evaluation_order=request.evaluation_order,
            conditions=conditions,
            actions=actions,
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RuleResponse(
        id=rule.id,
        group_id=rule.group_id,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
        is_active=rule.is_active,
        evaluation_order=rule.evaluation_order,
        version=rule.version,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        conditions=request.conditions,
        actions=request.actions,
        metadata=rule.metadata_json,
    )


@router.get("/valuation-rules", response_model=list[RuleResponse])
async def list_rules(
    group_id: int | None = Query(None),
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """List valuation rules"""
    service = RulesService()
    rules = await service.list_rules(
        session=session,
        group_id=group_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )

    return [
        RuleResponse(
            id=rule.id,
            group_id=rule.group_id,
            name=rule.name,
            description=rule.description,
            priority=rule.priority,
            is_active=rule.is_active,
            evaluation_order=rule.evaluation_order,
            version=rule.version,
            created_by=rule.created_by,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            conditions=[
                ConditionSchema(
                    field_name=c.field_name,
                    field_type=c.field_type,
                    operator=c.operator,
                    value=c.value_json,
                    logical_operator=c.logical_operator,
                    group_order=c.group_order,
                )
                for c in rule.conditions
            ],
            actions=[
                ActionSchema(
                    action_type=a.action_type,
                    metric=a.metric,
                    value_usd=float(a.value_usd) if a.value_usd else None,
                    unit_type=a.unit_type,
                    formula=a.formula,
                    modifiers=a.modifiers_json,
                )
                for a in rule.actions
            ],
            metadata=rule.metadata_json,
        )
        for rule in rules
    ]


@router.get("/valuation-rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a valuation rule by ID"""
    service = RulesService()
    rule = await service.get_rule(session, rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return RuleResponse(
        id=rule.id,
        group_id=rule.group_id,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
        is_active=rule.is_active,
        evaluation_order=rule.evaluation_order,
        version=rule.version,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        conditions=[
            ConditionSchema(
                field_name=c.field_name,
                field_type=c.field_type,
                operator=c.operator,
                value=c.value_json,
                logical_operator=c.logical_operator,
                group_order=c.group_order,
            )
            for c in rule.conditions
        ],
        actions=[
            ActionSchema(
                action_type=a.action_type,
                metric=a.metric,
                value_usd=float(a.value_usd) if a.value_usd else None,
                unit_type=a.unit_type,
                formula=a.formula,
                modifiers=a.modifiers_json,
            )
            for a in rule.actions
        ],
        metadata=rule.metadata_json,
    )


@router.put("/valuation-rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    request: RuleUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update a valuation rule"""
    service = RulesService()

    # Get the existing rule to check its parent group
    existing_rule = await service.get_rule(session, rule_id)
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Check if the parent group is basic-managed
    group = await service.get_rule_group(session, existing_rule.group_id)
    if group:
        validate_basic_managed_group(group.metadata_json, "update rule in")

    # Validate modifiers for each action
    if request.actions:
        for action in request.actions:
            validate_modifiers_json(action.modifiers, action.action_type)

    updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}

    # No conversion needed - request.dict() already converts Pydantic objects to dicts
    try:
        rule = await service.update_rule(session, rule_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return RuleResponse(
        id=rule.id,
        group_id=rule.group_id,
        name=rule.name,
        description=rule.description,
        priority=rule.priority,
        is_active=rule.is_active,
        evaluation_order=rule.evaluation_order,
        version=rule.version,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        conditions=[
            ConditionSchema(
                field_name=c.field_name,
                field_type=c.field_type,
                operator=c.operator,
                value=c.value_json,
                logical_operator=c.logical_operator,
                group_order=c.group_order,
            )
            for c in rule.conditions
        ],
        actions=[
            ActionSchema(
                action_type=a.action_type,
                metric=a.metric,
                value_usd=float(a.value_usd) if a.value_usd else None,
                unit_type=a.unit_type,
                formula=a.formula,
                modifiers=a.modifiers_json,
            )
            for a in rule.actions
        ],
        metadata=rule.metadata_json,
    )


@router.delete("/valuation-rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a valuation rule"""
    service = RulesService()

    # Get the existing rule to check its parent group
    existing_rule = await service.get_rule(session, rule_id)
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Check if the parent group is basic-managed
    group = await service.get_rule_group(session, existing_rule.group_id)
    if group:
        validate_basic_managed_group(group.metadata_json, "delete rule from")

    success = await service.delete_rule(session, rule_id)

    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"message": "Rule deleted successfully"}
