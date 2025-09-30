"""Endpoints exposing combined field metadata and catalog records."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.field_registry import FieldRegistry

router = APIRouter(prefix="/v1/fields-data", tags=["fields"])
registry = FieldRegistry()


@router.get("/entities")
async def list_entities() -> dict[str, list[dict[str, str]]]:
    entities = [
        {
            "entity": meta.entity,
            "label": meta.label,
            "primary_key": meta.primary_key,
            "supports_custom_fields": str(meta.supports_custom_fields).lower(),
        }
        for meta in registry.get_entities()
    ]
    return {"entities": entities}


@router.get("/{entity}/schema")
async def entity_schema(entity: str, db: AsyncSession = Depends(session_dependency)) -> dict[str, object]:
    try:
        return await registry.schema_for(db, entity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{entity}/records")
async def list_entity_records(
    entity: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(session_dependency),
) -> dict[str, object]:
    try:
        return await registry.list_records(db, entity=entity, limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{entity}/records", status_code=status.HTTP_201_CREATED)
async def create_entity_record(
    entity: str,
    payload: dict,
    db: AsyncSession = Depends(session_dependency),
) -> dict[str, object]:
    try:
        record = await registry.create_record(db, entity=entity, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return record


@router.patch("/{entity}/records/{record_id}")
async def update_entity_record(
    entity: str,
    record_id: int,
    payload: dict,
    db: AsyncSession = Depends(session_dependency),
) -> dict[str, object]:
    try:
        return await registry.update_record(db, entity=entity, record_id=record_id, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


__all__ = ["router"]
