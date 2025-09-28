"""API routes for managing custom field definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.custom_fields import CustomFieldService, UNSET
from .schemas.custom_fields import (
    CustomFieldCreateRequest,
    CustomFieldListResponse,
    CustomFieldResponse,
    CustomFieldUpdateRequest,
)

router = APIRouter(prefix="/v1/reference/custom-fields", tags=["custom-fields"])
service = CustomFieldService()


@router.get("", response_model=CustomFieldListResponse)
async def list_custom_fields(
    entity: str | None = Query(default=None, description="Filter by entity type"),
    include_inactive: bool = Query(default=False),
    include_deleted: bool = Query(default=False),
    db: AsyncSession = Depends(session_dependency),
) -> CustomFieldListResponse:
    records = await service.list_fields(
        db,
        entity=entity,
        include_inactive=include_inactive,
        include_deleted=include_deleted,
    )
    return CustomFieldListResponse(fields=[CustomFieldResponse.model_validate(record) for record in records])


@router.post("", response_model=CustomFieldResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    request: CustomFieldCreateRequest,
    db: AsyncSession = Depends(session_dependency),
) -> CustomFieldResponse:
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
            visibility=request.visibility,
            created_by=request.created_by,
            validation=request.validation,
            display_order=request.display_order,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CustomFieldResponse.model_validate(record)


@router.patch("/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(
    field_id: int,
    request: CustomFieldUpdateRequest,
    db: AsyncSession = Depends(session_dependency),
) -> CustomFieldResponse:
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
            visibility=payload.get("visibility"),
            created_by=payload.get("created_by"),
            validation=payload.get("validation"),
            display_order=payload.get("display_order"),
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CustomFieldResponse.model_validate(record)



@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_field(
    field_id: int,
    hard_delete: bool = Query(default=False, description="Permanently remove the field"),
    db: AsyncSession = Depends(session_dependency),
):
    try:
        await service.delete_field(db, field_id=field_id, hard_delete=hard_delete)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None


__all__ = ["router"]
