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


class AddFieldOptionRequest(BaseModel):
    """Request to add an option to a dropdown/multi-select field"""
    value: str = Field(..., min_length=1, description="Option value to add")


class FieldOptionResponse(BaseModel):
    """Response with updated field options"""
    field_id: int
    entity: str
    key: str
    options: list[str]


__all__ = [
    "CustomFieldCreateRequest",
    "CustomFieldUpdateRequest",
    "CustomFieldResponse",
    "CustomFieldListResponse",
    "AddFieldOptionRequest",
    "FieldOptionResponse",
]

