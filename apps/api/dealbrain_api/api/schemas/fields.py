"""Pydantic schemas for global field management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dealbrain_core.schemas import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionRead,
    CustomFieldDefinitionUpdate,
)
from pydantic import BaseModel, Field


class FieldCreateRequest(CustomFieldDefinitionCreate):
    pass


class FieldUpdateRequest(CustomFieldDefinitionUpdate):
    pass


class FieldResponse(CustomFieldDefinitionRead):
    pass


class FieldListResponse(BaseModel):
    fields: list[FieldResponse] = Field(default_factory=list)


class FieldAuditEntry(BaseModel):
    id: int
    field_id: int
    action: str
    actor: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class FieldAuditResponse(BaseModel):
    events: list[FieldAuditEntry] = Field(default_factory=list)


class FieldUsageRecord(BaseModel):
    field_id: int
    entity: str
    key: str
    total: int
    counts: dict[str, int] = Field(default_factory=dict)


class FieldUsageResponse(BaseModel):
    usage: list[FieldUsageRecord] = Field(default_factory=list)


class FieldDeleteResponse(FieldUsageRecord):
    pass


class FieldValuesResponse(BaseModel):
    """Response schema for field values endpoint."""

    field_name: str = Field(..., description="The field name queried")
    values: list[str] = Field(..., description="Distinct values for the field")
    count: int = Field(..., description="Number of values returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "field_name": "listing.condition",
                    "values": ["New", "Like New", "Good", "Fair"],
                    "count": 4,
                }
            ]
        }
    }


__all__ = [
    "FieldCreateRequest",
    "FieldUpdateRequest",
    "FieldResponse",
    "FieldListResponse",
    "FieldAuditEntry",
    "FieldAuditResponse",
    "FieldUsageRecord",
    "FieldUsageResponse",
    "FieldDeleteResponse",
    "FieldValuesResponse",
]
