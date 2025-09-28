"""Service layer helpers for managing custom field definitions."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import CustomFieldDefinition

ALLOWED_FIELD_TYPES: tuple[str, ...] = (
    "string",
    "number",
    "boolean",
    "enum",
    "multi_select",
    "text",
    "json",
)
VALIDATION_KEYS: set[str] = {
    "pattern",
    "min",
    "max",
    "min_length",
    "max_length",
    "allowed_values",
}
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
        include_deleted: bool = False,
    ) -> list[CustomFieldDefinition]:
        query = select(CustomFieldDefinition)
        if entity:
            query = query.where(CustomFieldDefinition.entity == entity)
        if not include_inactive:
            query = query.where(CustomFieldDefinition.is_active.is_(True))
        if not include_deleted:
            query = query.where(CustomFieldDefinition.deleted_at.is_(None))
        query = query.order_by(
            CustomFieldDefinition.entity.asc(),
            CustomFieldDefinition.display_order.asc(),
            CustomFieldDefinition.label.asc(),
        )
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
        validation: dict | None = None,
        display_order: int | None = None,
    ) -> CustomFieldDefinition:
        normalized_key = self._normalize_key(key or label)
        normalized_type = data_type.lower()
        self._validate_field_type(normalized_type)
        normalized_options = self._normalize_options(normalized_type, options)
        normalized_validation = self._normalize_validation(normalized_type, validation)

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
            validation_json=normalized_validation,
            display_order=display_order if display_order is not None else 100,
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
        validation: dict | None = None,
        display_order: int | None = None,
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
            record.validation_json = self._normalize_validation(normalized_type, validation if validation is not None else record.validation_json)
        elif options is not None:
            record.options = self._normalize_options(record.data_type, options)
        if validation is not None:
            record.validation_json = self._normalize_validation(record.data_type, validation)
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
        if display_order is not None:
            record.display_order = display_order

        await db.flush()
        await db.refresh(record)
        return record

    async def delete_field(self, db: AsyncSession, *, field_id: int, hard_delete: bool = False) -> None:
        record = await db.get(CustomFieldDefinition, field_id)
        if not record:
            raise LookupError("Custom field not found")
        if hard_delete:
            await db.delete(record)
            await db.flush()
            return
        record.is_active = False
        record.deleted_at = datetime.utcnow()
        await db.flush()

    def _normalize_key(self, raw_key: str) -> str:
        key = raw_key.strip().lower().replace(" ", "_")
        key = re.sub(r"[^a-z0-9_]+", "_", key)
        return re.sub(r"_+", "_", key).strip("_")

    def _validate_field_type(self, data_type: str) -> None:
        if data_type not in self.allowed_types:
            supported = ", ".join(self.allowed_types)
            raise ValueError(f"Unsupported custom field type '{data_type}'. Supported types: {supported}")

    def _normalize_options(self, data_type: str, options: list[str] | None) -> list[str] | None:
        if data_type in {"enum", "multi_select"}:
            if not options:
                raise ValueError("Enumerated custom fields require at least one option")
            return [str(option) for option in options]
        return None

    def _normalize_validation(self, data_type: str, validation: dict | None) -> dict | None:
        if not validation:
            return None
        if not isinstance(validation, dict):
            raise ValueError("Validation rules must be supplied as an object")
        unknown_keys = set(validation) - VALIDATION_KEYS
        if unknown_keys:
            raise ValueError(f"Unsupported validation keys: {', '.join(sorted(unknown_keys))}")

        normalized: dict[str, Any] = {}

        if "pattern" in validation:
            pattern = validation["pattern"]
            if not isinstance(pattern, str):
                raise ValueError("Validation 'pattern' must be a string")
            normalized["pattern"] = pattern

        def _ensure_number(value: Any, key: str) -> float:
            if isinstance(value, (int, float)):
                return float(value)
            raise ValueError(f"Validation '{key}' must be numeric")

        if data_type == "number":
            if "min" in validation:
                normalized["min"] = _ensure_number(validation["min"], "min")
            if "max" in validation:
                normalized["max"] = _ensure_number(validation["max"], "max")
        else:
            if "min" in validation or "max" in validation:
                raise ValueError("Only numeric fields support 'min'/'max' validation")

        if data_type == "string":
            if "min_length" in validation:
                normalized["min_length"] = int(validation["min_length"])
            if "max_length" in validation:
                normalized["max_length"] = int(validation["max_length"])
        else:
            if "min_length" in validation or "max_length" in validation:
                raise ValueError("Length validation only applies to string fields")

        if "allowed_values" in validation:
            values = validation["allowed_values"]
            if not isinstance(values, list) or not all(isinstance(item, (str, int, float, bool)) for item in values):
                raise ValueError("Validation 'allowed_values' must be a list of primitive values")
            normalized["allowed_values"] = [value for value in values]

        return normalized or None


__all__ = ["CustomFieldService", "ALLOWED_FIELD_TYPES", "UNSET"]
