"""Endpoints for entity and field metadata."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.field_metadata import FieldMetadataService


router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/metadata")
async def get_entities_metadata(
    db: AsyncSession = Depends(session_dependency),
) -> dict:
    """Get metadata for all entities and fields for rule builder."""
    service = FieldMetadataService()
    entities = await service.get_entities_metadata(db)

    return {
        "entities": [
            {
                "key": entity.key,
                "label": entity.label,
                "fields": [
                    {
                        "key": field.key,
                        "label": field.label,
                        "data_type": field.data_type,
                        "description": field.description,
                        "options": field.options,
                        "is_custom": field.is_custom,
                        "validation": field.validation,
                    }
                    for field in entity.fields
                ],
            }
            for entity in entities
        ],
        "operators": [
            {
                "value": op.value,
                "label": op.label,
                "field_types": op.field_types,
            }
            for op in FieldMetadataService.OPERATORS
        ],
    }
