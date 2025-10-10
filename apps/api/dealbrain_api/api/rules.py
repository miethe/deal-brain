"""API endpoints for valuation rules management"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import tempfile
from pathlib import Path

from ..db import session_dependency as get_session
from ..schemas.rules import (
    RulesetCreateRequest,
    RulesetUpdateRequest,
    RulesetResponse,
    RuleGroupCreateRequest,
    RuleGroupUpdateRequest,
    RuleGroupResponse,
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleResponse,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleEvaluationResponse,
    BulkEvaluationRequest,
    ApplyRulesetRequest,
    AuditLogResponse,
    ConditionSchema,
    ActionSchema,
    PackageMetadataRequest,
    PackageExportResponse,
    PackageInstallResponse,
)
from ..services.rules import RulesService
from ..services.rule_evaluation import RuleEvaluationService
from ..services.rule_preview import RulePreviewService
from ..services.ruleset_packaging import RulesetPackagingService
from dealbrain_core.rules.packaging import (
    RulesetPackage,
    create_package_metadata
)


router = APIRouter(prefix="/api/v1", tags=["rules"])


# --- Ruleset Endpoints ---

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


# --- Rule Group Endpoints ---

@router.post("/rule-groups", response_model=RuleGroupResponse)
async def create_rule_group(
    request: RuleGroupCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new rule group"""
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
    )

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
        rules=[],
    )


@router.get("/rule-groups", response_model=list[RuleGroupResponse])
async def list_rule_groups(
    ruleset_id: int | None = Query(None),
    category: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List rule groups"""
    service = RulesService()
    groups = await service.list_rule_groups(
        session=session,
        ruleset_id=ruleset_id,
        category=category,
    )

    return [
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
            rules=[],
        )
        for g in groups
    ]


@router.get("/rule-groups/{group_id}", response_model=RuleGroupResponse)
async def get_rule_group(
    group_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a rule group by ID"""
    service = RulesService()
    group = await service.get_rule_group(session, group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Rule group not found")

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
        rules=rules,
    )


@router.put("/rule-groups/{group_id}", response_model=RuleGroupResponse)
async def update_rule_group(
    group_id: int,
    request: RuleGroupUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update a rule group"""
    service = RulesService()
    group = await service.update_rule_group(session, group_id, request)

    if not group:
        raise HTTPException(status_code=404, detail="Rule group not found")

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
        rules=[],
    )


# --- Rule Endpoints ---

@router.post("/valuation-rules", response_model=RuleResponse)
async def create_rule(
    request: RuleCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new valuation rule"""
    service = RulesService()

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
    success = await service.delete_rule(session, rule_id)

    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"message": "Rule deleted successfully"}


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
        result = await service.apply_ruleset_to_all_listings(
            session, request.ruleset_id
        )
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


# --- Package Endpoints ---

@router.post("/rulesets/{ruleset_id}/package")
async def export_ruleset_package(
    ruleset_id: int,
    request: PackageMetadataRequest,
    session: AsyncSession = Depends(get_session),
):
    """Export a ruleset as a .dbrs package file"""
    service = RulesetPackagingService()

    # Create package metadata
    metadata = create_package_metadata(
        name=request.name,
        version=request.version,
        author=request.author or "Unknown",
        description=request.description or "",
        min_app_version=request.min_app_version,
        required_custom_fields=request.required_custom_fields,
        tags=request.tags or []
    )

    try:
        # Export to package
        package = await service.export_ruleset_to_package(
            session=session,
            ruleset_id=ruleset_id,
            metadata=metadata,
            include_examples=request.include_examples or False
        )

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.dbrs',
            delete=False
        ) as tmp:
            tmp.write(package.to_json())
            tmp_path = Path(tmp.name)

        # Return file
        return FileResponse(
            path=str(tmp_path),
            filename=f"{request.name.replace(' ', '_')}_v{request.version}.dbrs",
            media_type="application/json"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/rulesets/install", response_model=PackageInstallResponse)
async def install_ruleset_package(
    file: UploadFile = File(...),
    actor: str = Query("system", description="User installing the package"),
    merge_strategy: str = Query("replace", description="Conflict resolution strategy"),
    session: AsyncSession = Depends(get_session),
):
    """Install a .dbrs package file"""
    service = RulesetPackagingService()

    try:
        # Read package file
        content = await file.read()
        package = RulesetPackage.from_json(content.decode('utf-8'))

        # Install package
        results = await service.install_package(
            session=session,
            package=package,
            actor=actor,
            merge_strategy=merge_strategy
        )

        return PackageInstallResponse(
            success=True,
            message="Package installed successfully",
            rulesets_created=results["rulesets_created"],
            rulesets_updated=results["rulesets_updated"],
            rule_groups_created=results["rule_groups_created"],
            rules_created=results["rules_created"],
            warnings=results.get("warnings", [])
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")


@router.post("/rulesets/{ruleset_id}/package/preview")
async def preview_package_export(
    ruleset_id: int,
    request: PackageMetadataRequest,
    session: AsyncSession = Depends(get_session),
):
    """Preview what will be included in a package export"""
    service = RulesetPackagingService()

    metadata = create_package_metadata(
        name=request.name,
        version=request.version,
        author=request.author or "Unknown",
        description=request.description or "",
        min_app_version=request.min_app_version,
        required_custom_fields=request.required_custom_fields,
        tags=request.tags or []
    )

    try:
        package = await service.export_ruleset_to_package(
            session=session,
            ruleset_id=ruleset_id,
            metadata=metadata,
            include_examples=False
        )

        dependencies = package.get_dependencies()

        return PackageExportResponse(
            package_name=package.metadata.name,
            package_version=package.metadata.version,
            rulesets_count=len(package.rulesets),
            rule_groups_count=len(package.rule_groups),
            rules_count=len(package.rules),
            custom_fields_count=len(package.custom_field_definitions),
            dependencies=dependencies,
            estimated_size_kb=len(package.to_json()) / 1024,
            readme=package.generate_readme()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")
