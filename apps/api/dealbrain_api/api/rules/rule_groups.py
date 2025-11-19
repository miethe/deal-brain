"""API endpoints for rule group management (CRUD operations)"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import session_dependency as get_session
from ...models.core import ValuationRuleGroup
from ...schemas.rules import (
    RuleGroupCreateRequest,
    RuleGroupUpdateRequest,
    RuleGroupResponse,
    RuleResponse,
    ConditionSchema,
    ActionSchema,
)
from ...services.rules import RulesService
from ...validation.rules_validation import (
    validate_basic_managed_group,
    validate_entity_key,
    extract_metadata_fields,
    merge_metadata_fields,
)


router = APIRouter()


@router.post("/rule-groups", response_model=RuleGroupResponse)
async def create_rule_group(
    request: RuleGroupCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new rule group"""
    # Validate entity key if provided
    validate_entity_key(request.entity_key)

    # Merge basic_managed and entity_key into metadata
    metadata = merge_metadata_fields(
        existing_metadata=request.metadata,
        basic_managed=request.basic_managed,
        entity_key=request.entity_key,
    )

    service = RulesService()
    group = await service.create_rule_group(
        session=session,
        ruleset_id=request.ruleset_id,
        name=request.name,
        category=request.category,
        description=request.description,
        display_order=request.display_order,
        weight=request.weight,
        is_active=request.is_active,
        metadata=metadata,
    )

    # Extract basic_managed and entity_key from metadata for response
    basic_managed, entity_key = extract_metadata_fields(group.metadata_json)

    return RuleGroupResponse(
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
        rules=[],
    )


@router.get("/rule-groups", response_model=list[RuleGroupResponse])
async def list_rule_groups(
    ruleset_id: int | None = Query(None),
    category: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[RuleGroupResponse]:
    """List rule groups"""
    service = RulesService()
    groups: list[ValuationRuleGroup] = await service.list_rule_groups(
        session=session,
        ruleset_id=ruleset_id,
        category=category,
    )

    result: list[RuleGroupResponse] = []
    for g in groups:
        if not g:  # Skip None entries if they somehow exist
            continue

        # Extract basic_managed and entity_key from metadata
        basic_managed, entity_key = extract_metadata_fields(g.metadata_json)

        result.append(
            RuleGroupResponse(
                id=g.id,
                ruleset_id=g.ruleset_id,
                name=g.name,
                category=g.category,
                description=g.description,
                display_order=g.display_order,
                weight=g.weight,
                is_active=g.is_active,
                created_at=g.created_at,
                updated_at=g.updated_at,
                metadata=g.metadata_json,
                basic_managed=basic_managed,
                entity_key=entity_key,
                rules=[],
            )
        )

    return result


@router.get("/rule-groups/{group_id}", response_model=RuleGroupResponse)
async def get_rule_group(
    group_id: int,
    session: AsyncSession = Depends(get_session),
) -> RuleGroupResponse:
    """Get a rule group by ID"""
    service = RulesService()
    group: ValuationRuleGroup | None = await service.get_rule_group(session, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Rule group not found")

    rules: list[RuleResponse] = [
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

    return RuleGroupResponse(
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


@router.put("/rule-groups/{group_id}", response_model=RuleGroupResponse)
async def update_rule_group(
    group_id: int,
    request: RuleGroupUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> RuleGroupResponse:
    """Update a rule group"""
    service = RulesService()

    # First get the group to check if it's basic-managed
    existing_group = await service.get_rule_group(session, group_id)
    if not existing_group:
        raise HTTPException(status_code=404, detail="Rule group not found")

    # Check if group is basic-managed (prevent manual edits)
    validate_basic_managed_group(existing_group.metadata_json, "update")

    # Validate entity key if provided
    validate_entity_key(request.entity_key)

    # Prepare update data
    updates = request.model_dump(exclude_unset=True)

    # Handle basic_managed and entity_key separately
    basic_managed = updates.pop("basic_managed", None)
    entity_key = updates.pop("entity_key", None)

    # Merge metadata fields
    if basic_managed is not None or entity_key is not None or "metadata" in updates:
        updates["metadata"] = merge_metadata_fields(
            existing_metadata=existing_group.metadata_json,
            basic_managed=basic_managed,
            entity_key=entity_key,
            additional_metadata=updates.get("metadata"),
        )

    group: ValuationRuleGroup | None = await service.update_rule_group(session, group_id, updates)

    if not group:
        raise HTTPException(status_code=404, detail="Rule group not found")

    # Extract basic_managed and entity_key from metadata for response
    basic_managed, entity_key = extract_metadata_fields(group.metadata_json)

    return RuleGroupResponse(
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
        rules=[],
    )
