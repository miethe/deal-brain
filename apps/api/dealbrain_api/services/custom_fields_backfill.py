"""Utility helpers to infer custom field definitions from existing data."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import CustomFieldDefinition
from .custom_fields import CustomFieldService, ENTITY_MODEL_MAP


async def inventory_attribute_values(
    db: AsyncSession,
    entity: str,
) -> dict[str, list[Any]]:
    model = ENTITY_MODEL_MAP.get(entity)
    if model is None:
        return {}
    column = getattr(model, "attributes_json", None)
    if column is None:
        return {}

    result = await db.execute(select(column))
    values: dict[str, list[Any]] = defaultdict(list)
    for row in result.scalars():
        if not row:
            continue
        for key, value in row.items():
            if key:
                values[key].append(value)
    return values


def infer_field_shape(values: Iterable[Any]) -> tuple[str, dict[str, Any] | None, list[str] | None]:
    candidates = [value for value in values if value is not None]
    if not candidates:
        return "string", None, None

    if all(isinstance(value, bool) for value in candidates):
        return "boolean", None, None

    if all(isinstance(value, (int, float)) for value in candidates):
        min_value = float(min(candidates))
        max_value = float(max(candidates))
        if min_value == max_value:
            return "number", {"min": min_value, "max": max_value}, None
        return "number", {"min": min_value, "max": max_value}, None

    if all(isinstance(value, list) for value in candidates):
        flattened = {str(item) for value in candidates for item in value}
        options = sorted(flattened)
        return "multi_select", None, options or None

    as_strings = [str(value) for value in candidates]
    unique_strings = sorted(set(as_strings))
    if 1 < len(unique_strings) <= 12:
        return "enum", None, unique_strings

    max_length = max(len(item) for item in as_strings)
    validation: dict[str, Any] | None = {"max_length": max_length} if max_length else None
    return "string", validation, None


async def backfill_field_definitions(
    db: AsyncSession,
    *,
    actor: str | None = None,
    service: CustomFieldService | None = None,
) -> list[CustomFieldDefinition]:
    field_service = service or CustomFieldService()
    created: list[CustomFieldDefinition] = []

    for entity in ENTITY_MODEL_MAP:
        inventory = await inventory_attribute_values(db, entity)
        for display_index, (raw_key, samples) in enumerate(sorted(inventory.items())):
            normalized_key = field_service._normalize_key(raw_key)
            label = raw_key.replace("_", " ").strip().title() or normalized_key.title()

            data_type, validation, options = infer_field_shape(samples)

            existing = await db.scalar(
                select(CustomFieldDefinition).where(
                    CustomFieldDefinition.entity == entity,
                    CustomFieldDefinition.key == normalized_key,
                )
            )
            if existing:
                continue

            try:
                record = await field_service.create_field(
                    db,
                    entity=entity,
                    key=normalized_key,
                    label=label,
                    data_type=data_type,
                    description=None,
                    required=False,
                    default_value=None,
                    options=options,
                    is_active=True,
                    visibility="public",
                    created_by=actor,
                    validation=validation,
                    display_order=100 + display_index,
                    actor=actor,
                )
            except ValueError:
                continue
            created.append(record)

    return created


__all__ = [
    "backfill_field_definitions",
    "inventory_attribute_values",
    "infer_field_shape",
]
