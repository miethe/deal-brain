from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import Condition, ListingStatus
from dealbrain_core.schemas import ListingCreate, ListingRead

from ..db import session_dependency
from ..models import Listing
from ..services.custom_fields import CustomFieldService
from ..services.listings import (
    apply_listing_metrics,
    bulk_update_listings,
    create_listing,
    partial_update_listing,
    sync_listing_components,
    update_listing,
)
from .schemas.listings import (
    ListingBulkUpdateRequest,
    ListingBulkUpdateResponse,
    ListingFieldSchema,
    ListingPartialUpdateRequest,
    ListingSchemaResponse,
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
    ),
    ListingFieldSchema(
        key="gpu_id",
        label="GPU",
        data_type="reference",
    ),
    ListingFieldSchema(
        key="ram_gb",
        label="RAM (GB)",
        data_type="number",
    ),
    ListingFieldSchema(
        key="primary_storage_gb",
        label="Primary Storage (GB)",
        data_type="number",
    ),
    ListingFieldSchema(
        key="primary_storage_type",
        label="Primary Storage Type",
        data_type="enum",
        options=["SSD", "HDD", "Hybrid"],
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


@router.get("/schema", response_model=ListingSchemaResponse)
async def get_listing_schema(session: AsyncSession = Depends(session_dependency)) -> ListingSchemaResponse:
    custom_fields = await custom_field_service.list_fields(session, entity="listing")
    custom_field_models = [CustomFieldResponse.model_validate(field) for field in custom_fields]
    return ListingSchemaResponse(core_fields=CORE_LISTING_FIELDS, custom_fields=custom_field_models)
