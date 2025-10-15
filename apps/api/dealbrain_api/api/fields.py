"""REST endpoints for managing global field definitions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services import field_values as field_values_service
from ..services.custom_fields import UNSET, CustomFieldService, FieldDependencyError
from .schemas.fields import (
    FieldAuditEntry,
    FieldAuditResponse,
    FieldCreateRequest,
    FieldDeleteResponse,
    FieldListResponse,
    FieldResponse,
    FieldUpdateRequest,
    FieldUsageRecord,
    FieldUsageResponse,
    FieldValuesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/fields", tags=["fields"])
service = CustomFieldService()


def _serialize_usage(summary) -> FieldUsageRecord:
    return FieldUsageRecord(
        field_id=summary.field_id,
        entity=summary.entity,
        key=summary.key,
        total=summary.total,
        counts=summary.counts,
    )


@router.get("", response_model=FieldListResponse)
async def list_fields(
    entity: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    include_deleted: bool = Query(default=False),
    db: AsyncSession = Depends(session_dependency),
) -> FieldListResponse:
    records = await service.list_fields(
        db,
        entity=entity,
        include_inactive=include_inactive,
        include_deleted=include_deleted,
    )
    return FieldListResponse(fields=[FieldResponse.model_validate(record) for record in records])


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    request: FieldCreateRequest,
    actor: str | None = Query(default=None, description="User performing the action"),
    db: AsyncSession = Depends(session_dependency),
) -> FieldResponse:
    try:
        record = await service.create_field(
            db,
            entity=request.entity,
            key=request.key,
            label=request.label,
            data_type=request.data_type,
            description=request.description,
            required=request.required,
            default_value=request.default_value,
            options=request.options,
            is_active=request.is_active,
            is_locked=request.is_locked,
            visibility=request.visibility,
            created_by=request.created_by,
            validation=request.validation,
            display_order=request.display_order,
            actor=actor,
        )
    except ValueError as exc:  # validation error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return FieldResponse.model_validate(record)


@router.patch("/{field_id}", response_model=FieldResponse)
async def update_field(
    field_id: int,
    request: FieldUpdateRequest,
    force: bool = Query(default=False, description="Allow update despite dependencies"),
    actor: str | None = Query(default=None, description="User performing the action"),
    db: AsyncSession = Depends(session_dependency),
) -> FieldResponse:
    payload = request.model_dump(exclude_unset=True)
    try:
        record = await service.update_field(
            db,
            field_id=field_id,
            label=payload.get("label"),
            data_type=payload.get("data_type"),
            description=payload.get("description"),
            required=payload.get("required"),
            default_value=payload.get("default_value", UNSET),
            options=payload.get("options"),
            is_active=payload.get("is_active"),
            is_locked=payload.get("is_locked"),
            visibility=payload.get("visibility"),
            created_by=payload.get("created_by"),
            validation=payload.get("validation"),
            display_order=payload.get("display_order"),
            force=force,
            actor=actor,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FieldDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "usage": {"total": exc.usage.total, "counts": exc.usage.counts},
            },
        ) from exc
    return FieldResponse.model_validate(record)


@router.delete("/{field_id}", response_model=FieldDeleteResponse)
async def delete_field(
    field_id: int,
    hard_delete: bool = Query(default=False),
    force: bool = Query(default=False, description="Allow delete despite dependencies"),
    actor: str | None = Query(default=None, description="User performing the action"),
    db: AsyncSession = Depends(session_dependency),
) -> FieldDeleteResponse:
    try:
        usage = await service.delete_field(
            db,
            field_id=field_id,
            hard_delete=hard_delete,
            force=force,
            actor=actor,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FieldDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "usage": {"total": exc.usage.total, "counts": exc.usage.counts},
            },
        ) from exc
    return FieldDeleteResponse.model_validate(
        {
            "field_id": usage.field_id,
            "entity": usage.entity,
            "key": usage.key,
            "total": usage.total,
            "counts": usage.counts,
        }
    )


@router.get("/{field_id}/history", response_model=FieldAuditResponse)
async def field_history(
    field_id: int,
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(session_dependency),
) -> FieldAuditResponse:
    try:
        events = await service.history(db, field_id=field_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FieldAuditResponse(
        events=[
            FieldAuditEntry(
                id=event.id,
                field_id=event.field_id,
                action=event.action,
                actor=event.actor,
                payload=event.payload_json,
                created_at=event.created_at,
                updated_at=event.updated_at,
            )
            for event in events
        ]
    )


@router.get("/usage", response_model=FieldUsageResponse)
async def field_usage(
    entity: str | None = Query(default=None),
    db: AsyncSession = Depends(session_dependency),
) -> FieldUsageResponse:
    summaries = await service.list_usage(db, entity=entity)
    return FieldUsageResponse(usage=[_serialize_usage(summary) for summary in summaries])


@router.get(
    "/{field_name}/values",
    response_model=FieldValuesResponse,
    summary="Get distinct values for a field",
    description="Returns distinct values for a given field to power autocomplete functionality",
)
async def get_field_values(
    field_name: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of values to return"),
    search: str | None = Query(None, description="Optional search filter"),
    db: AsyncSession = Depends(session_dependency),
) -> FieldValuesResponse:
    """
    Get distinct values for a field across all entities.

    **Examples:**
    - `/fields/listing.condition/values` -> ["New", "Like New", "Good", "Fair"]
    - `/fields/cpu.manufacturer/values?limit=5` -> ["Intel", "AMD", "Apple", ...]
    - `/fields/listing.seller/values?search=ebay` -> ["ebay_seller_1", "ebay_seller_2"]
    """
    try:
        values = await field_values_service.get_field_distinct_values(
            session=db,
            field_name=field_name,
            limit=limit,
            search=search,
        )

        return FieldValuesResponse(
            field_name=field_name,
            values=values,
            count=len(values),
        )

    except ValueError as e:
        logger.warning(f"Invalid field request: {field_name} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error fetching field values: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve field values",
        ) from e


__all__ = ["router"]
