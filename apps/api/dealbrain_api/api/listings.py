from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dealbrain_core.enums import Condition, ListingStatus, RamGeneration
from dealbrain_core.schemas import ListingCreate, ListingRead

from ..db import session_dependency
from ..telemetry import get_logger
from ..models import Listing, ValuationRuleset, ValuationRuleV2, ValuationRuleGroup
from ..services.custom_fields import CustomFieldService
from ..services.listings import (
    apply_listing_metrics,
    bulk_update_listing_metrics,
    bulk_update_listings,
    complete_partial_import,
    create_listing,
    delete_listing,
    get_paginated_listings,
    partial_update_listing,
    sync_listing_components,
    update_listing,
    update_listing_metrics,
    update_listing_overrides,
    VALUATION_DISABLED_RULESETS_KEY,
)
from ..services import ports as ports_service
from .schemas.listings import (
    BulkRecalculateRequest,
    BulkRecalculateResponse,
    CompletePartialImportRequest,
    CompletePartialImportResponse,
    LegacyValuationLine,
    ListingBulkUpdateRequest,
    ListingBulkUpdateResponse,
    ListingFieldSchema,
    ListingPartialUpdateRequest,
    ListingSchemaResponse,
    ListingValuationOverrideRequest,
    ListingValuationOverrideResponse,
    PaginatedListingsResponse,
    PortEntry,
    PortsResponse,
    UpdatePortsRequest,
    ValuationAdjustmentAction,
    ValuationAdjustmentDetail,
    ValuationBreakdownResponse,
)
from .schemas.custom_fields import CustomFieldResponse

router = APIRouter(prefix="/v1/listings", tags=["listings"])
custom_field_service = CustomFieldService()
logger = get_logger("dealbrain.api.listings")


CORE_LISTING_FIELDS: list[ListingFieldSchema] = [
    ListingFieldSchema(
        key="title",
        label="Title",
        data_type="string",
        required=True,
        description="Canonical listing label",
        validation={"min_length": 3},
    ),
    ListingFieldSchema(
        key="listing_url",
        label="Listing URL",
        data_type="string",
        description="Primary external link for the listing",
    ),
    ListingFieldSchema(
        key="other_urls",
        label="Additional Links",
        data_type="list",
        description="Supplemental URLs with optional labels",
        editable=True,
    ),
    ListingFieldSchema(
        key="price_usd",
        label="Price (USD)",
        data_type="number",
        required=True,
        validation={"min": 0},
    ),
    ListingFieldSchema(
        key="condition",
        label="Condition",
        data_type="enum",
        options=[condition.value for condition in Condition],
    ),
    ListingFieldSchema(
        key="status",
        label="Status",
        data_type="enum",
        options=[status_.value for status_ in ListingStatus],
    ),
    ListingFieldSchema(
        key="cpu_id",
        label="CPU",
        data_type="reference",
        description="Linked CPU identifier",
        editable=True,
    ),
    ListingFieldSchema(
        key="ram_spec_id",
        label="RAM Spec",
        data_type="reference",
        description="Linked RAM specification",
        editable=True,
    ),
    ListingFieldSchema(
        key="gpu_id",
        label="GPU",
        data_type="reference",
        editable=True,
    ),
    ListingFieldSchema(
        key="ram_gb",
        label="RAM (GB)",
        data_type="number",
        editable=True,
    ),
    ListingFieldSchema(
        key="ram_type",
        label="RAM Type",
        data_type="enum",
        editable=False,
        options=[generation.value for generation in RamGeneration],
        description="Resolved RAM generation from linked spec",
    ),
    ListingFieldSchema(
        key="ram_speed_mhz",
        label="RAM Speed (MHz)",
        data_type="number",
        editable=False,
        description="Resolved RAM speed from linked spec",
    ),
    ListingFieldSchema(
        key="primary_storage_gb",
        label="Primary Storage (GB)",
        data_type="number",
        editable=True,
    ),
    ListingFieldSchema(
        key="primary_storage_type",
        label="Primary Storage Type",
        data_type="enum",
        options=["NVMe", "SSD", "HDD", "Hybrid", "eMMC", "UFS"],
        editable=True,
    ),
    ListingFieldSchema(
        key="primary_storage_profile_id",
        label="Primary Storage Profile",
        data_type="reference",
        description="Linked storage profile for the primary drive",
        editable=True,
    ),
    ListingFieldSchema(
        key="secondary_storage_gb",
        label="Secondary Storage (GB)",
        data_type="number",
    ),
    ListingFieldSchema(
        key="secondary_storage_type",
        label="Secondary Storage Type",
        data_type="enum",
        options=["NVMe", "SSD", "HDD", "Hybrid", "eMMC", "UFS"],
    ),
    ListingFieldSchema(
        key="secondary_storage_profile_id",
        label="Secondary Storage Profile",
        data_type="reference",
        description="Linked storage profile for the secondary drive",
        editable=True,
    ),
    ListingFieldSchema(
        key="os_license",
        label="OS License",
        data_type="string",
    ),
    ListingFieldSchema(
        key="ruleset_id",
        label="Assigned Ruleset",
        data_type="reference",
        description="Static valuation ruleset override",
    ),
    ListingFieldSchema(
        key="notes",
        label="Notes",
        data_type="text",
        editable=True,
    ),
]


@router.get("", response_model=list[ListingRead])
async def list_listings(
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    result = await session.execute(select(Listing).order_by(Listing.created_at.desc()).offset(offset).limit(limit))
    listings = result.scalars().unique().all()
    return [ListingRead.model_validate(listing) for listing in listings]


@router.get("/paginated", response_model=PaginatedListingsResponse)
async def get_paginated_listings_endpoint(
    limit: int = Query(default=50, ge=1, le=500, description="Number of items per page (1-500)"),
    cursor: str | None = Query(default=None, description="Pagination cursor from previous response"),
    sort_by: str = Query(default="updated_at", regex=r"^[a-z_]+$", description="Column to sort by"),
    sort_order: str = Query(default="desc", regex=r"^(asc|desc)$", description="Sort direction (asc or desc)"),
    form_factor: str | None = Query(default=None, description="Filter by form factor"),
    manufacturer: str | None = Query(default=None, description="Filter by manufacturer"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price filter"),
    session: AsyncSession = Depends(session_dependency),
) -> PaginatedListingsResponse:
    """Get paginated listings with cursor-based pagination.

    This endpoint implements high-performance cursor-based pagination with:
    - Composite key (sort_column, id) for stable pagination
    - Base64-encoded cursors to prevent client manipulation
    - Cached total count (5 minutes TTL)
    - Support for dynamic sorting and filtering

    Performance: <100ms response time for 500-row pages.

    Query Parameters:
        limit: Number of items per page (1-500, default 50)
        cursor: Pagination cursor from previous response (optional)
        sort_by: Column to sort by (default "updated_at")
        sort_order: Sort direction ("asc" or "desc", default "desc")
        form_factor: Filter by form factor (optional)
        manufacturer: Filter by manufacturer (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)

    Returns:
        PaginatedListingsResponse with:
        - items: List of listings in current page
        - total: Total count of listings (cached)
        - limit: Requested page size
        - next_cursor: Cursor for next page (null if last page)
        - has_next: Whether more pages are available

    Example:
        GET /v1/listings/paginated?limit=50&sort_by=price_usd&sort_order=asc
        GET /v1/listings/paginated?cursor=eyJpZCI6MTIzLCJzb3J0X3ZhbHVlIjoiMjAyNC0wMS0wMVQwMDowMDowMCJ9&limit=50

    Raises:
        400: Invalid parameters (invalid sort column, cursor format, etc.)
        500: Server error
    """
    try:
        result = await get_paginated_listings(
            session,
            limit=limit,
            cursor=cursor,
            sort_by=sort_by,
            sort_order=sort_order,
            form_factor=form_factor,
            manufacturer=manufacturer,
            min_price=min_price,
            max_price=max_price,
        )

        return PaginatedListingsResponse(
            items=[ListingRead.model_validate(listing) for listing in result["items"]],
            total=result["total"],
            limit=result["limit"],
            next_cursor=result["next_cursor"],
            has_next=result["has_next"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing_endpoint(
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    listing_data = payload.model_dump(exclude={"components"}, exclude_none=True)
    listing = await create_listing(session, listing_data)
    await sync_listing_components(
        session,
        listing,
        [component.model_dump(exclude_none=True) for component in (payload.components or [])],
    )
    await apply_listing_metrics(session, listing)
    await session.refresh(listing)
    return ListingRead.model_validate(listing)



@router.get("/schema", response_model=ListingSchemaResponse)
async def get_listing_schema(session: AsyncSession = Depends(session_dependency)) -> ListingSchemaResponse:
    custom_fields = await custom_field_service.list_fields(session, entity="listing")
    custom_field_models = [CustomFieldResponse.model_validate(field) for field in custom_fields]
    return ListingSchemaResponse(core_fields=CORE_LISTING_FIELDS, custom_fields=custom_field_models)


@router.get("/{listing_id}", response_model=ListingRead)
async def get_listing(listing_id: int, session: AsyncSession = Depends(session_dependency)) -> ListingRead:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingRead.model_validate(listing)


@router.put("/{listing_id}", response_model=ListingRead)
async def update_listing_endpoint(
    listing_id: int,
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing_data = payload.model_dump(exclude={"components"}, exclude_none=True)
    await update_listing(session, listing, listing_data)
    await sync_listing_components(
        session,
        listing,
        [component.model_dump(exclude_none=True) for component in (payload.components or [])],
    )
    await apply_listing_metrics(session, listing)
    await session.refresh(listing)
    return ListingRead.model_validate(listing)


@router.patch("/{listing_id}", response_model=ListingRead)
async def patch_listing_endpoint(
    listing_id: int,
    request: ListingPartialUpdateRequest,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    updated = await partial_update_listing(
        session,
        listing,
        fields=request.fields or {},
        attributes=request.attributes or {},
    )
    return ListingRead.model_validate(updated)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_listing_endpoint(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> None:
    """Delete a listing and all related data.

    Cascade deletes:
    - ListingComponent records
    - ListingScoreSnapshot records
    - RawPayload records
    - EntityFieldValue records for this listing

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: Listing not found
    """
    try:
        await delete_listing(session, listing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _serialize_listing_override(listing: Listing) -> ListingValuationOverrideResponse:
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
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if request.mode == "static":
        ruleset = await session.get(ValuationRuleset, request.ruleset_id)
        if not ruleset:
            raise HTTPException(status_code=404, detail="Ruleset not found")
        if not ruleset.is_active:
            raise HTTPException(status_code=400, detail="Ruleset is inactive and cannot be assigned")

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


@router.post("/bulk-update", response_model=ListingBulkUpdateResponse)
async def bulk_update_listings_endpoint(
    request: ListingBulkUpdateRequest,
    session: AsyncSession = Depends(session_dependency),
) -> ListingBulkUpdateResponse:
    if not request.listing_ids:
        return ListingBulkUpdateResponse(updated=[], updated_count=0)
    listings = await bulk_update_listings(
        session,
        request.listing_ids,
        fields=request.fields or {},
        attributes=request.attributes or {},
    )
    if not listings:
        raise HTTPException(status_code=404, detail="No listings matched the provided identifiers")
    return ListingBulkUpdateResponse(
        updated=[ListingRead.model_validate(listing) for listing in listings],
        updated_count=len(listings),
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
    # Get listing
    result = await session.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
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
                ValuationRuleV2.id.notin_(active_rule_ids)
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


@router.post("/{listing_id}/recalculate-metrics", response_model=ListingRead)
async def recalculate_listing_metrics(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency)
):
    """Recalculate all performance metrics for a listing."""
    try:
        listing = await update_listing_metrics(session, listing_id)
        return ListingRead.model_validate(listing)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk-recalculate-metrics", response_model=BulkRecalculateResponse)
async def bulk_recalculate_metrics(
    request: BulkRecalculateRequest,
    session: AsyncSession = Depends(session_dependency)
):
    """Recalculate metrics for multiple listings.

    If listing_ids is None or empty, updates all listings.
    """
    count = await bulk_update_listing_metrics(
        session,
        request.listing_ids
    )
    return BulkRecalculateResponse(
        updated_count=count,
        message=f"Updated {count} listing(s)"
    )


@router.post("/{listing_id}/ports", response_model=PortsResponse)
async def update_listing_ports(
    listing_id: int,
    request: UpdatePortsRequest,
    session: AsyncSession = Depends(session_dependency)
):
    """Create or update ports for a listing."""
    try:
        ports_data = [p.model_dump() for p in request.ports]
        await ports_service.update_listing_ports(session, listing_id, ports_data)
        ports = await ports_service.get_listing_ports(session, listing_id)
        return PortsResponse(ports=[PortEntry(**p) for p in ports])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{listing_id}/ports", response_model=PortsResponse)
async def get_listing_ports(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency)
):
    """Get ports for a listing."""
    ports = await ports_service.get_listing_ports(session, listing_id)
    return PortsResponse(ports=[PortEntry(**p) for p in ports])


@router.patch(
    "/{listing_id}/complete",
    response_model=CompletePartialImportResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_partial_import_endpoint(
    listing_id: int,
    request: CompletePartialImportRequest,
    session: AsyncSession = Depends(session_dependency),
    # current_user: dict = Depends(get_current_user),  # TODO: Add auth when available
) -> CompletePartialImportResponse:
    """
    Complete a partial import by providing missing fields.

    This endpoint allows users to fill in missing data (typically price)
    for listings that were partially imported from URL extraction. After
    completion, the listing's quality is updated to "full" and metrics
    are calculated.

    Args:
        listing_id: ID of the partial listing to complete
        request: Completion data (at minimum, price)
        session: Database session
        current_user: Authenticated user (TODO)

    Returns:
        Updated listing with metrics calculated and quality="full"

    Raises:
        404: Listing not found
        400: Listing is not partial or validation failed
        422: Invalid request data

    Example:
        PATCH /v1/listings/123/complete
        {"price": 299.99}

        → Returns: {"id": 123, "quality": "full", ...}
    """
    try:
        updated_listing = await complete_partial_import(
            session=session,
            listing_id=listing_id,
            completion_data=request.model_dump(),
            user_id="system",  # TODO: Use current_user["id"] when auth is available
        )
        await session.commit()

        return CompletePartialImportResponse(
            id=updated_listing.id,
            title=updated_listing.title,
            price_usd=updated_listing.price_usd,
            quality=updated_listing.quality,
            missing_fields=updated_listing.missing_fields or [],
            adjusted_price_usd=updated_listing.adjusted_price_usd,
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error completing partial import for listing {listing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete import"
        )
