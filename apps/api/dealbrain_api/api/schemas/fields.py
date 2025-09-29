"""Pydantic schemas for global field management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from dealbrain_core.schemas import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionRead,
    CustomFieldDefinitionUpdate,
)


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
]
