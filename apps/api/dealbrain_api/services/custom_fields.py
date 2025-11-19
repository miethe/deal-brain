"""Service layer helpers for managing custom field definitions."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import (
    Cpu,
    CustomFieldAuditLog,
    CustomFieldAttributeHistory,
    CustomFieldDefinition,
    Gpu,
    Listing,
    PortsProfile,
)
from ..settings import get_settings

logger = logging.getLogger(__name__)
analytics_logger = logging.getLogger("dealbrain.analytics")

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

ENTITY_MODEL_MAP = {
    "listing": Listing,
    "cpu": Cpu,
    "gpu": Gpu,
    "ports_profile": PortsProfile,
    # Note: valuation_rule removed - now using ValuationRuleV2, ValuationRuleset, etc.
}


@dataclass
class FieldUsageSummary:
    field_id: int
    entity: str
    key: str
    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


class FieldDependencyError(RuntimeError):
    def __init__(self, message: str, usage: FieldUsageSummary) -> None:
        super().__init__(message)
        self.usage = usage


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

    async def get_field(self, db: AsyncSession, field_id: int) -> CustomFieldDefinition:
        record = await db.get(CustomFieldDefinition, field_id)
        if not record:
            raise LookupError("Custom field not found")
        return record

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
        is_locked: bool = False,
        visibility: str = "public",
        created_by: str | None = None,
        validation: dict | None = None,
        display_order: int | None = None,
        actor: str | None = None,
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
            raise ValueError(
                f"Custom field '{normalized_key}' already exists for entity '{entity}'"
            )

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
            is_locked=is_locked,
            visibility=visibility,
            created_by=created_by,
            validation_json=normalized_validation,
            display_order=display_order if display_order is not None else 100,
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)

        snapshot = self._snapshot(record)
        self._write_audit_event(
            db,
            field_id=record.id,
            action="created",
            actor=actor or created_by,
            payload={"after": snapshot},
        )
        self._emit_event(
            "field_definition.created", {"field_id": record.id, "entity": record.entity}
        )
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
        is_locked: bool | None = None,
        visibility: str | None = None,
        created_by: str | None = None,
        validation: dict | None = None,
        display_order: int | None = None,
        force: bool = False,
        actor: str | None = None,
    ) -> CustomFieldDefinition:
        record = await self.get_field(db, field_id)
        before = self._snapshot(record)
        previous_options = list(record.options or []) if record.options else []
        previous_type = record.data_type

        if record.is_locked:
            if data_type is not None and data_type.lower() != record.data_type:
                raise ValueError(
                    f"Locked field '{record.key}' - type cannot be changed to maintain data integrity"
                )
            if is_locked is not None and is_locked is False:
                raise ValueError(f"Locked field '{record.key}' cannot be unlocked")

        if label is not None:
            record.label = label
        if data_type is not None:
            normalized_type = data_type.lower()
            self._validate_field_type(normalized_type)
            record.data_type = normalized_type
            record.options = self._normalize_options(
                normalized_type,
                options if options is not None else record.options,
            )
            record.validation_json = self._normalize_validation(
                normalized_type,
                validation if validation is not None else record.validation_json,
            )
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
            if not is_active and not force:
                usage = await self.field_usage(db, record)
                if usage.total:
                    raise FieldDependencyError(
                        f"Field '{record.key}' is used {usage.total} time(s) and cannot be deactivated without force",
                        usage,
                    )
            record.is_active = is_active
        if visibility is not None:
            record.visibility = visibility
        if created_by is not None:
            record.created_by = created_by
        if display_order is not None:
            record.display_order = display_order
        if is_locked and not record.is_locked:
            record.is_locked = True

        await db.flush()
        await db.refresh(record)

        current_options = list(record.options or []) if record.options else []
        removed_options: set[str] = set()
        if previous_options and previous_type in {"enum", "multi_select"}:
            removed_options = set(previous_options) - set(current_options)

        for option in sorted(removed_options):

            def _matches(
                value: Any, *, option_value: str = option, value_kind: str = previous_type
            ) -> bool:
                if value is None:
                    return False
                if value_kind == "multi_select":
                    if isinstance(value, list):
                        return option_value in value
                    return False
                return value == option_value

            await self._archive_field_attributes(
                db,
                record,
                reason=f"option_retired:{option}",
                remove_from_record=False,
                value_filter=_matches,
            )
            self._emit_event(
                "field_definition.option_retired",
                {"field_id": record.id, "entity": record.entity, "option": option},
            )

        after = self._snapshot(record)
        diff = self._diff(before, after)
        if diff:
            self._write_audit_event(
                db,
                field_id=record.id,
                action="updated",
                actor=actor or created_by,
                payload={
                    "before": {key: before[key] for key in diff},
                    "after": {key: after[key] for key in diff},
                },
            )
            self._emit_event(
                "field_definition.updated",
                {"field_id": record.id, "entity": record.entity, "changes": sorted(diff)},
            )
        return record

    async def add_field_option(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        value: str,
        actor: str | None = None,
    ) -> CustomFieldDefinition:
        """Add an option to a dropdown/multi-select field.

        Args:
            db: Database session
            field_id: ID of the field to modify
            value: Option value to add
            actor: Username of user making the change

        Returns:
            Updated field definition

        Raises:
            LookupError: If field not found
            ValueError: If field type doesn't support options or value already exists
        """
        record = await self.get_field(db, field_id)

        # Validate field type supports options
        if record.data_type not in {"enum", "multi_select"}:
            raise ValueError(
                f"Cannot add options to field of type '{record.data_type}'. "
                "Only 'enum' and 'multi_select' fields support options."
            )

        # Get current options
        current_options = list(record.options or [])

        # Check if option already exists
        if value in current_options:
            raise ValueError(f"Option '{value}' already exists in field '{record.key}'")

        # Add new option
        current_options.append(value)
        record.options = current_options

        await db.flush()
        await db.refresh(record)

        # Audit logging
        self._write_audit_event(
            db,
            field_id=record.id,
            action="option_added",
            actor=actor,
            payload={"option": value, "total_options": len(current_options)},
        )

        self._emit_event(
            "field_definition.option_added",
            {"field_id": record.id, "entity": record.entity, "option": value},
        )

        return record

    async def delete_field(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        hard_delete: bool = False,
        force: bool = False,
        actor: str | None = None,
    ) -> FieldUsageSummary:
        record = await self.get_field(db, field_id)
        if record.is_locked:
            raise ValueError(f"Locked field '{record.key}' cannot be deleted")
        usage = await self.field_usage(db, record)
        if usage.total and not force:
            raise FieldDependencyError(
                f"Field '{record.key}' is still used {usage.total} time(s)",
                usage,
            )

        await self._archive_field_attributes(db, record, reason="field_deleted")

        snapshot = self._snapshot(record)
        action = "hard_deleted" if hard_delete else "soft_deleted"
        payload = {"before": snapshot, "usage": usage.counts}

        if hard_delete:
            self._write_audit_event(
                db,
                field_id=record.id,
                action=action,
                actor=actor,
                payload=payload,
            )
            await db.delete(record)
        else:
            record.is_active = False
            record.deleted_at = datetime.utcnow()
            self._write_audit_event(
                db,
                field_id=record.id,
                action=action,
                actor=actor,
                payload=payload,
            )

        await db.flush()
        self._emit_event(
            "field_definition.deleted",
            {
                "field_id": field_id,
                "entity": record.entity,
                "hard": hard_delete,
                "usage": usage.counts,
            },
        )
        return usage

    async def field_usage(
        self,
        db: AsyncSession,
        field: CustomFieldDefinition,
    ) -> FieldUsageSummary:
        model = ENTITY_MODEL_MAP.get(field.entity)
        counts: dict[str, int] = {}
        if model is None:
            logger.debug("No usage mapping registered for entity '%s'", field.entity)
            return FieldUsageSummary(
                field_id=field.id, entity=field.entity, key=field.key, counts=counts
            )

        column = getattr(model, "attributes_json", None)
        if column is not None:
            stmt = select(func.count()).select_from(model).where(column[field.key].isnot(None))
            result = await db.scalar(stmt)
            counts[field.entity] = int(result or 0)
        return FieldUsageSummary(
            field_id=field.id, entity=field.entity, key=field.key, counts=counts
        )

    async def list_usage(
        self,
        db: AsyncSession,
        *,
        entity: str | None = None,
        field_ids: Sequence[int] | None = None,
    ) -> list[FieldUsageSummary]:
        records = await self.list_fields(
            db,
            entity=entity,
            include_inactive=True,
            include_deleted=True,
        )
        if field_ids is not None:
            id_filter = set(field_ids)
            records = [record for record in records if record.id in id_filter]
        usage: list[FieldUsageSummary] = []
        for record in records:
            usage.append(await self.field_usage(db, record))
        return usage

    async def history(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        limit: int = 200,
    ) -> list[CustomFieldAuditLog]:
        await self.get_field(db, field_id)
        result = await db.execute(
            select(CustomFieldAuditLog)
            .where(CustomFieldAuditLog.field_id == field_id)
            .order_by(CustomFieldAuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def _archive_field_attributes(
        self,
        db: AsyncSession,
        field: CustomFieldDefinition,
        *,
        reason: str,
        remove_from_record: bool = True,
        value_filter: Callable[[Any], bool] | None = None,
    ) -> None:
        model = ENTITY_MODEL_MAP.get(field.entity)
        if model is None:
            return
        column = getattr(model, "attributes_json", None)
        if column is None:
            return

        result = await db.execute(select(model).where(column[field.key].isnot(None)))
        records = result.scalars().all()
        for record_instance in records:
            attributes = dict(getattr(record_instance, "attributes_json", {}) or {})
            if field.key not in attributes:
                continue
            value = attributes[field.key]
            if value_filter and not value_filter(value):
                continue
            history = CustomFieldAttributeHistory(
                field_id=field.id,
                entity=field.entity,
                record_id=getattr(record_instance, "id"),
                attribute_key=field.key,
                previous_value=value,
                reason=reason,
            )
            db.add(history)
            if remove_from_record:
                attributes.pop(field.key, None)
                record_instance.attributes_json = attributes

    def _normalize_key(self, raw_key: str) -> str:
        key = raw_key.strip().lower().replace(" ", "_")
        key = re.sub(r"[^a-z0-9_]+", "_", key)
        return re.sub(r"_+", "_", key).strip("_")

    def _validate_field_type(self, data_type: str) -> None:
        if data_type not in self.allowed_types:
            supported = ", ".join(self.allowed_types)
            raise ValueError(
                f"Unsupported custom field type '{data_type}'. Supported types: {supported}"
            )

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
            if not isinstance(values, list) or not all(
                isinstance(item, (str, int, float, bool)) for item in values
            ):
                raise ValueError("Validation 'allowed_values' must be a list of primitive values")
            normalized["allowed_values"] = [value for value in values]

        return normalized or None

    def _snapshot(self, record: CustomFieldDefinition) -> dict[str, Any]:
        return {
            "entity": record.entity,
            "key": record.key,
            "label": record.label,
            "data_type": record.data_type,
            "description": record.description,
            "required": record.required,
            "default_value": record.default_value,
            "options": list(record.options or []) if record.options else None,
            "is_active": record.is_active,
            "is_locked": record.is_locked,
            "visibility": record.visibility,
            "created_by": record.created_by,
            "validation": record.validation_json or None,
            "display_order": record.display_order,
            "deleted_at": record.deleted_at.isoformat() if record.deleted_at else None,
        }

    def _diff(self, before: dict[str, Any], after: dict[str, Any]) -> set[str]:
        changed: set[str] = set()
        for key, value in after.items():
            if before.get(key) != value:
                changed.add(key)
        return changed

    def _write_audit_event(
        self,
        db: AsyncSession,
        *,
        field_id: int,
        action: str,
        actor: str | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        audit = CustomFieldAuditLog(
            field_id=field_id,
            action=action,
            actor=actor,
            payload_json=payload or None,
        )
        db.add(audit)

    def _emit_event(self, name: str, payload: dict[str, Any]) -> None:
        settings = get_settings()
        if settings.analytics_enabled:
            analytics_logger.info("event=%s payload=%s", name, payload)


__all__ = [
    "CustomFieldService",
    "ALLOWED_FIELD_TYPES",
    "UNSET",
    "FieldDependencyError",
    "FieldUsageSummary",
    "ENTITY_MODEL_MAP",
]
