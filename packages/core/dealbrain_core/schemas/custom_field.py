"""Schemas for custom field definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import DealBrainModel


class CustomFieldDefinitionBase(DealBrainModel):
    entity: str
    key: str
    label: str
    data_type: str = "string"
    description: str | None = None
    required: bool = False
    default_value: Any | None = None
    options: list[str] | None = None
    is_active: bool = True
    is_locked: bool = False
    visibility: str = "public"
    created_by: str | None = None
    validation: dict[str, Any] | None = None
    display_order: int = 100


class CustomFieldDefinitionCreate(CustomFieldDefinitionBase):
    pass


class CustomFieldDefinitionUpdate(DealBrainModel):
    label: str | None = None
    data_type: str | None = None
    description: str | None = None
    required: bool | None = None
    default_value: Any | None = None
    options: list[str] | None = None
    is_active: bool | None = None
    is_locked: bool | None = None
    visibility: str | None = None
    created_by: str | None = None
    validation: dict[str, Any] | None = None
    display_order: int | None = None


class CustomFieldDefinitionRead(CustomFieldDefinitionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


__all__ = [
    "CustomFieldDefinitionCreate",
    "CustomFieldDefinitionRead",
    "CustomFieldDefinitionUpdate",
]
