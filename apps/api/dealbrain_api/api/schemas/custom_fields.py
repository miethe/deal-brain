"""Pydantic schemas for custom field API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from dealbrain_core.schemas import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionRead,
    CustomFieldDefinitionUpdate,
)


class CustomFieldCreateRequest(CustomFieldDefinitionCreate):
    pass


class CustomFieldUpdateRequest(CustomFieldDefinitionUpdate):
    default_value: Any | None = Field(default=None)


class CustomFieldResponse(CustomFieldDefinitionRead):
    pass


class CustomFieldListResponse(BaseModel):
    fields: list[CustomFieldResponse] = Field(default_factory=list)


__all__ = [
    "CustomFieldCreateRequest",
    "CustomFieldUpdateRequest",
    "CustomFieldResponse",
    "CustomFieldListResponse",
]

