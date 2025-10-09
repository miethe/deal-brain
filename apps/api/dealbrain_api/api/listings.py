from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import Condition, ListingStatus
from dealbrain_core.schemas import ListingCreate, ListingRead

from ..db import session_dependency
from ..models import Listing, ValuationRuleset
from ..services.custom_fields import CustomFieldService
from ..services.listings import (
    apply_listing_metrics,
    bulk_update_listing_metrics,
    bulk_update_listings,
    create_listing,
    partial_update_listing,
    sync_listing_components,
    update_listing,
    update_listing_metrics,
    update_listing_overrides,
    VALUATION_DISABLED_RULESETS_KEY,
)
from ..services import ports as ports_service
from .schemas.listings import (
    AppliedRuleDetail,
    BulkRecalculateRequest,
    BulkRecalculateResponse,
    ListingBulkUpdateRequest,
    ListingBulkUpdateResponse,
    ListingFieldSchema,
    ListingPartialUpdateRequest,
    ListingSchemaResponse,
    ListingValuationOverrideRequest,
    ListingValuationOverrideResponse,
    PortEntry,
    PortsResponse,
    UpdatePortsRequest,
    ValuationBreakdownResponse,
)
from .schemas.custom_fields import CustomFieldResponse

router = APIRouter(prefix="/v1/listings", tags=["listings"])
custom_field_service = CustomFieldService()


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
        key="primary_storage_gb",
        label="Primary Storage (GB)",
        data_type="number",
        editable=True,
    ),
    ListingFieldSchema(
        key="primary_storage_type",
        label="Primary Storage Type",
        data_type="enum",
        options=["SSD", "HDD", "Hybrid"],
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
        options=["SSD", "HDD", "Hybrid"],
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
    was calculated, including all applied rules and their individual contributions.

    Args:
        listing_id: ID of the listing to get breakdown for
        session: Database session

    Returns:
        Detailed valuation breakdown

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

    # Parse valuation breakdown JSON
    breakdown = listing.valuation_breakdown or {}

    # Format applied rules
    applied_rules = []
    for rule_data in breakdown.get("applied_rules", []):
        applied_rules.append(AppliedRuleDetail(
            rule_group_name=rule_data.get("group_name", "Unknown"),
            rule_name=rule_data.get("rule_name", "Unknown"),
            rule_description=rule_data.get("description"),
            adjustment_amount=rule_data.get("adjustment", 0.0),
            conditions_met=rule_data.get("conditions_met", []),
            actions_applied=rule_data.get("actions_applied", []),
        ))

    return ValuationBreakdownResponse(
        listing_id=listing.id,
        listing_title=listing.title,
        base_price_usd=listing.price_usd or 0.0,
        adjusted_price_usd=listing.adjusted_price_usd or listing.price_usd or 0.0,
        total_adjustment=breakdown.get("total_adjustment", 0.0),
        active_ruleset=breakdown.get("ruleset_name", "None"),
        applied_rules=applied_rules,
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
