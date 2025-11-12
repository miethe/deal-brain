"""
Schema endpoints for listings.

Provides listing field schema including core fields and custom fields.
Extracted from monolithic listings.py for better modularity and maintainability.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import Condition, ListingStatus, RamGeneration

from ...db import session_dependency
from ...telemetry import get_logger
from ...services.custom_fields import CustomFieldService
from ..schemas.listings import ListingFieldSchema, ListingSchemaResponse
from ..schemas.custom_fields import CustomFieldResponse

router = APIRouter()
custom_field_service = CustomFieldService()
logger = get_logger("dealbrain.api.listings.schema")


# Core listing fields that are always available
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


@router.get("/schema", response_model=ListingSchemaResponse)
async def get_listing_schema(session: AsyncSession = Depends(session_dependency)) -> ListingSchemaResponse:
    """Get the complete schema for listing fields.

    Returns:
        Combined schema including core fields and custom fields configured for the listing entity.
    """
    try:
        custom_fields = await custom_field_service.list_fields(session, entity="listing")
        custom_field_models = [CustomFieldResponse.model_validate(field) for field in custom_fields]
        return ListingSchemaResponse(core_fields=CORE_LISTING_FIELDS, custom_fields=custom_field_models)
    except OperationalError as e:
        logger.error(f"Database connection error in get_listing_schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please try again later."
        )
    except ProgrammingError as e:
        logger.error(f"Database schema error in get_listing_schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error. Please contact support."
        )
    except DatabaseError as e:
        logger.error(f"Database error in get_listing_schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )
