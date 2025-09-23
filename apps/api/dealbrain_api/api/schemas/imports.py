"""Pydantic schemas for the revamped importer API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class MappingSuggestionModel(BaseModel):
    column: str
    confidence: float
    reason: str | None = None


class FieldMappingModel(BaseModel):
    field: str
    label: str
    required: bool
    data_type: str
    column: str | None = None
    status: Literal["auto", "manual", "missing"]
    confidence: float = 0.0
    suggestions: list[MappingSuggestionModel] = Field(default_factory=list)


class EntityMappingModel(BaseModel):
    sheet: str | None = None
    fields: dict[str, FieldMappingModel] = Field(default_factory=dict)


class SheetColumnModel(BaseModel):
    name: str
    samples: list[str] = Field(default_factory=list)


class SheetMetaModel(BaseModel):
    sheet_name: str
    row_count: int
    columns: list[SheetColumnModel] = Field(default_factory=list)
    entity: str | None = None
    entity_label: str | None = None
    confidence: float = 0.0
    declared_entity: str | None = None


class ComponentMatchSuggestionModel(BaseModel):
    match: str
    confidence: float


class ComponentMatchModel(BaseModel):
    row_index: int
    value: str
    status: Literal["auto", "review", "unmatched"]
    auto_match: str | None = None
    suggestions: list[ComponentMatchSuggestionModel] = Field(default_factory=list)


class EntityPreviewModel(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list)
    total_rows: int = 0
    mapped_field_count: int = 0
    component_matches: list[ComponentMatchModel] | None = None


class CpuConflictFieldModel(BaseModel):
    field: str
    existing: Any
    incoming: Any


class CpuConflictModel(BaseModel):
    name: str
    existing: dict[str, Any]
    incoming: dict[str, Any]
    fields: list[CpuConflictFieldModel]


class ImportSessionSnapshotModel(BaseModel):
    id: UUID
    filename: str
    content_type: str | None
    status: str
    checksum: str | None
    sheet_meta: list[SheetMetaModel]
    mappings: dict[str, EntityMappingModel]
    preview: dict[str, EntityPreviewModel]
    conflicts: dict[str, Any]
    declared_entities: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ImportSessionListModel(BaseModel):
    sessions: list[ImportSessionSnapshotModel]


class UpdateFieldMappingPayload(BaseModel):
    column: str | None = None
    status: Literal["auto", "manual", "missing"] | None = None
    confidence: float | None = None


class UpdateEntityMappingPayload(BaseModel):
    sheet: str | None = None
    fields: dict[str, UpdateFieldMappingPayload] | None = None


class UpdateMappingsRequest(BaseModel):
    mappings: dict[str, UpdateEntityMappingPayload]


class ConflictResolutionModel(BaseModel):
    entity: Literal["cpu"]
    identifier: str
    action: Literal["update", "skip", "keep"]


class ComponentOverrideModel(BaseModel):
    entity: Literal["listing"]
    row_index: int
    cpu_match: str | None = None
    gpu_match: str | None = None


class CommitImportRequest(BaseModel):
    conflict_resolutions: list[ConflictResolutionModel] = Field(default_factory=list)
    component_overrides: list[ComponentOverrideModel] = Field(default_factory=list)
    notes: str | None = None


class CommitImportResponse(BaseModel):
    status: str
    counts: dict[str, int]
    session: ImportSessionSnapshotModel


__all__ = [
    "ImportSessionSnapshotModel",
    "ImportSessionListModel",
    "UpdateMappingsRequest",
    "CommitImportRequest",
    "CommitImportResponse",
    "CpuConflictModel",
    "ComponentMatchModel",
]
