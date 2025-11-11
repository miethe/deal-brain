"""API endpoints for ruleset management (CRUD operations)"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import session_dependency as get_session
from ...schemas.rules import (
    RulesetCreateRequest,
    RulesetUpdateRequest,
    RulesetResponse,
    RuleGroupResponse,
    RuleResponse,
    ConditionSchema,
    ActionSchema,
)
from ...services.rules import RulesService
from ...validation.rules_validation import extract_metadata_fields


router = APIRouter()


@router.post("/rulesets", response_model=RulesetResponse)
async def create_ruleset(
    request: RulesetCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new valuation ruleset"""
    service = RulesService()
    ruleset = await service.create_ruleset(
        session=session,
        name=request.name,
        description=request.description,
        version=request.version,
        metadata=request.metadata,
        priority=request.priority,
        conditions=request.conditions,
        is_active=request.is_active,
    )

    return RulesetResponse(
        id=ruleset.id,
        name=ruleset.name,
        description=ruleset.description,
        version=ruleset.version,
        is_active=ruleset.is_active,
        created_by=ruleset.created_by,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
        metadata=ruleset.metadata_json,
        priority=ruleset.priority,
        conditions=ruleset.conditions_json,
        rule_groups=[],
    )


@router.get("/rulesets", response_model=list[RulesetResponse])
async def list_rulesets(
    active_only: bool = Query(False, description="Filter to active rulesets only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """List all valuation rulesets"""
    service = RulesService()
    rulesets = await service.list_rulesets(
        session=session,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )

    return [
        RulesetResponse(
            id=rs.id,
            name=rs.name,
            description=rs.description,
            version=rs.version,
            is_active=rs.is_active,
            created_by=rs.created_by,
            created_at=rs.created_at,
            updated_at=rs.updated_at,
            metadata=rs.metadata_json,
            priority=rs.priority,
            conditions=rs.conditions_json,
            rule_groups=[],
        )
        for rs in rulesets
    ]


@router.get("/rulesets/{ruleset_id}", response_model=RulesetResponse)
async def get_ruleset(
    ruleset_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a ruleset by ID with all groups and rules"""
    service = RulesService()
    ruleset = await service.get_ruleset(session, ruleset_id)

    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    # Build response with nested groups and rules
    rule_groups = []
    for group in ruleset.rule_groups:
        rules = [
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
            for rule in group.rules
        ]

        # Extract basic_managed and entity_key from metadata
        basic_managed, entity_key = extract_metadata_fields(group.metadata_json)

        rule_groups.append(
            RuleGroupResponse(
                id=group.id,
                ruleset_id=group.ruleset_id,
                name=group.name,
                category=group.category,
                description=group.description,
                display_order=group.display_order,
                weight=group.weight,
                is_active=group.is_active,
                created_at=group.created_at,
                updated_at=group.updated_at,
                metadata=group.metadata_json,
                basic_managed=basic_managed,
                entity_key=entity_key,
                rules=rules,
            )
        )

    return RulesetResponse(
        id=ruleset.id,
        name=ruleset.name,
        description=ruleset.description,
        version=ruleset.version,
        is_active=ruleset.is_active,
        created_by=ruleset.created_by,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
        metadata=ruleset.metadata_json,
        priority=ruleset.priority,
        conditions=ruleset.conditions_json,
        rule_groups=rule_groups,
    )


@router.put("/rulesets/{ruleset_id}", response_model=RulesetResponse)
async def update_ruleset(
    ruleset_id: int,
    request: RulesetUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update a ruleset"""
    service = RulesService()

    updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}

    ruleset = await service.update_ruleset(session, ruleset_id, updates)

    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    return RulesetResponse(
        id=ruleset.id,
        name=ruleset.name,
        description=ruleset.description,
        version=ruleset.version,
        is_active=ruleset.is_active,
        created_by=ruleset.created_by,
        created_at=ruleset.created_at,
        updated_at=ruleset.updated_at,
        metadata=ruleset.metadata_json,
        priority=ruleset.priority,
        conditions=ruleset.conditions_json,
        rule_groups=[],
    )


@router.delete("/rulesets/{ruleset_id}")
async def delete_ruleset(
    ruleset_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a ruleset (cascades to groups and rules)"""
    service = RulesService()
    success = await service.delete_ruleset(session, ruleset_id)

    if not success:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    return {"message": "Ruleset deleted successfully"}
