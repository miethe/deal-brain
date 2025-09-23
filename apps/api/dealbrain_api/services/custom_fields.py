"""Service layer helpers for managing custom field definitions."""

from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import CustomFieldDefinition

ALLOWED_FIELD_TYPES: tuple[str, ...] = ("string", "number", "boolean", "enum", "text", "json")
UNSET = object()


class CustomFieldService:
    """CRUD helpers for custom fields."""

    def __init__(self, allowed_types: Iterable[str] | None = None) -> None:
        self.allowed_types = tuple(allowed_types) if allowed_types else ALLOWED_FIELD_TYPES

    async def list_fields(
        self,
        db: AsyncSession,
        *,
        entity: str | None = None,
        include_inactive: bool = False,
    ) -> list[CustomFieldDefinition]:
        query = select(CustomFieldDefinition)
        if entity:
            query = query.where(CustomFieldDefinition.entity == entity)
        if not include_inactive:
            query = query.where(CustomFieldDefinition.is_active.is_(True))
        query = query.order_by(CustomFieldDefinition.entity.asc(), CustomFieldDefinition.key.asc())
        result = await db.execute(query)
        return result.scalars().all()

    async def create_field(
        self,
        db: AsyncSession,
        *,
        entity: str,
        key: str,
        label: str,
        data_type: str = "string",
        description: str | None = None,
        required: bool = False,
        default_value: object | None = None,
        options: list[str] | None = None,
        is_active: bool = True,
        visibility: str = "public",
        created_by: str | None = None,
    ) -> CustomFieldDefinition:
        normalized_key = self._normalize_key(key or label)
        normalized_type = data_type.lower()
        self._validate_field_type(normalized_type)
        normalized_options = self._normalize_options(normalized_type, options)

        existing = await db.scalar(
            select(CustomFieldDefinition).where(
                CustomFieldDefinition.entity == entity,
                CustomFieldDefinition.key == normalized_key,
            )
        )
        if existing:
            raise ValueError(f"Custom field '{normalized_key}' already exists for entity '{entity}'")

        record = CustomFieldDefinition(
            entity=entity,
            key=normalized_key,
            label=label,
            data_type=normalized_type,
            description=description,
            required=required,
            default_value=default_value,
            options=normalized_options,
            is_active=is_active,
            visibility=visibility,
            created_by=created_by,
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        label: str | None = None,
        data_type: str | None = None,
        description: str | None = None,
        required: bool | None = None,
        default_value: object | None = UNSET,
        options: list[str] | None = None,
        is_active: bool | None = None,
        visibility: str | None = None,
        created_by: str | None = None,
    ) -> CustomFieldDefinition:
        record = await db.get(CustomFieldDefinition, field_id)
        if not record:
            raise LookupError("Custom field not found")

        if label is not None:
            record.label = label
        if data_type is not None:
            normalized_type = data_type.lower()
            self._validate_field_type(normalized_type)
            record.data_type = normalized_type
            record.options = self._normalize_options(normalized_type, options if options is not None else record.options)
        elif options is not None:
            record.options = self._normalize_options(record.data_type, options)
        if description is not None:
            record.description = description
        if required is not None:
            record.required = required
        if default_value is not UNSET:
            record.default_value = default_value
        if is_active is not None:
            record.is_active = is_active
        if visibility is not None:
            record.visibility = visibility
        if created_by is not None:
            record.created_by = created_by

        await db.flush()
        await db.refresh(record)
        return record

    def _normalize_key(self, raw_key: str) -> str:
        key = raw_key.strip().lower().replace(" ", "_")
        key = re.sub(r"[^a-z0-9_]+", "_", key)
        return re.sub(r"_+", "_", key).strip("_")

    def _validate_field_type(self, data_type: str) -> None:
        if data_type not in self.allowed_types:
            supported = ", ".join(self.allowed_types)
            raise ValueError(f"Unsupported custom field type '{data_type}'. Supported types: {supported}")

    def _normalize_options(self, data_type: str, options: list[str] | None) -> list[str] | None:
        if data_type == "enum":
            if not options:
                raise ValueError("Enum custom fields require at least one option")
            return [str(option) for option in options]
        return None


__all__ = ["CustomFieldService", "ALLOWED_FIELD_TYPES", "UNSET"]
