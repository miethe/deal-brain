"""Pydantic schemas for listings API extensions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from dealbrain_core.schemas import ListingRead

from .custom_fields import CustomFieldResponse


class ListingFieldSchema(BaseModel):
    key: str
    label: str
    data_type: str
    required: bool = False
    editable: bool = True
    description: str | None = None
    options: list[str] | None = None
    validation: dict[str, Any] | None = None
    origin: Literal["core", "custom"] = "core"


class ListingSchemaResponse(BaseModel):
    core_fields: list[ListingFieldSchema] = Field(default_factory=list)
    custom_fields: list[CustomFieldResponse] = Field(default_factory=list)


class ListingPartialUpdateRequest(BaseModel):
    fields: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None


class ListingBulkUpdateRequest(BaseModel):
    listing_ids: list[int] = Field(default_factory=list)
    fields: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None


class ListingBulkUpdateResponse(BaseModel):
    updated: list[ListingRead]
    updated_count: int


__all__ = [
    "ListingFieldSchema",
    "ListingSchemaResponse",
    "ListingPartialUpdateRequest",
    "ListingBulkUpdateRequest",
    "ListingBulkUpdateResponse",
]
