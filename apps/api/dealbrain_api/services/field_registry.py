"""Service orchestrating combined core/custom field metadata and data operations."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from sqlalchemy import Select, func, select, inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import sqltypes

from dealbrain_core.schemas import CpuRead, ListingRead

from ..models import Cpu, Listing
from .custom_fields import CustomFieldService
from .listings import apply_listing_metrics, create_listing, partial_update_listing


@dataclass(slots=True)
class FieldMeta:
    key: str
    label: str
    data_type: str
    origin: str
    required: bool = False
    editable: bool = True
    locked: bool = False
    description: str | None = None
    options: Sequence[str] | None = None


@dataclass(slots=True)
class EntityMeta:
    entity: str
    label: str
    primary_key: str = "id"
    supports_custom_fields: bool = True
    core_fields: list[FieldMeta] = field(default_factory=list)


@dataclass(slots=True)
class RecordPayload:
    fields: dict[str, Any]
    attributes: dict[str, Any]


class FieldRegistry:
    """Central registry for catalog entities and their field metadata."""

    def __init__(self, *, custom_field_service: CustomFieldService | None = None) -> None:
        self.custom_fields = custom_field_service or CustomFieldService()
        self.entities: dict[str, EntityMeta] = {
            "listing": EntityMeta(
                entity="listing",
                label="Listings",
                core_fields=self._listing_core_fields(),
            ),
            "cpu": EntityMeta(
                entity="cpu",
                label="CPUs",
                supports_custom_fields=True,
                core_fields=self._cpu_core_fields(),
            ),
        }

    def get_entities(self) -> list[EntityMeta]:
        return list(self.entities.values())

    async def schema_for(self, db: AsyncSession, entity: str) -> dict[str, Any]:
        meta = self._require_entity(entity)
        custom: list[dict[str, Any]] = []
        if meta.supports_custom_fields:
            records = await self.custom_fields.list_fields(db, entity=entity, include_inactive=True, include_deleted=False)
            custom = [
                {
                    "id": record.id,
                    "key": record.key,
                    "label": record.label,
                    "data_type": record.data_type,
                    "required": record.required,
                    "locked": record.is_locked,
                    "editable": not record.is_locked,
                    "origin": "custom",
                    "description": record.description,
                    "options": record.options,
                    "is_active": record.is_active,
                }
                for record in records
            ]
        return {
            "entity": entity,
            "label": meta.label,
            "primary_key": meta.primary_key,
            "fields": [asdict(field) for field in meta.core_fields] + custom,
        }

    async def list_records(
        self,
        db: AsyncSession,
        *,
        entity: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        meta = self._require_entity(entity)
        if entity == "listing":
            result = await db.execute(
                select(Listing)
                .options(joinedload(Listing.cpu), joinedload(Listing.gpu))
                .order_by(Listing.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = result.scalars().all()
            total = await self._count(db, Listing)
            serialized = [self._serialize_listing(row) for row in rows]
        elif entity == "cpu":
            result = await db.execute(select(Cpu).order_by(Cpu.name).offset(offset).limit(limit))
            rows = result.scalars().all()
            total = await self._count(db, Cpu)
            serialized = [self._serialize_cpu(row) for row in rows]
        else:
            raise ValueError(f"Unsupported entity '{entity}'")
        return {
            "entity": entity,
            "label": meta.label,
            "records": serialized,
            "pagination": {"limit": limit, "offset": offset, "total": total},
        }

    async def create_record(self, db: AsyncSession, *, entity: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        meta = self._require_entity(entity)
        record_payload = self._normalize_payload(entity, payload)
        if entity == "listing":
            listing_payload = dict(record_payload.fields)
            if record_payload.attributes:
                listing_payload["attributes"] = record_payload.attributes
            listing = await create_listing(db, listing_payload)
            await apply_listing_metrics(db, listing)
            await db.refresh(listing)
            return self._serialize_listing(listing)
        if entity == "cpu":
            cpu_payload = dict(record_payload.fields)
            if record_payload.attributes:
                cpu_payload["attributes_json"] = record_payload.attributes
            cpu = Cpu(**cpu_payload)
            db.add(cpu)
            await db.flush()
            await db.refresh(cpu)
            return self._serialize_cpu(cpu)
        raise ValueError(f"Unsupported entity '{entity}'")

    async def update_record(
        self,
        db: AsyncSession,
        *,
        entity: str,
        record_id: int,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        self._require_entity(entity)
        record_payload = self._normalize_payload(entity, payload, for_update=True)
        if entity == "listing":
            listing = await db.get(Listing, record_id)
            if not listing:
                raise LookupError("Listing not found")
            updated = await partial_update_listing(
                db,
                listing,
                fields=record_payload.fields,
                attributes=record_payload.attributes,
            )
            return self._serialize_listing(updated)
        if entity == "cpu":
            cpu = await db.get(Cpu, record_id)
            if not cpu:
                raise LookupError("CPU not found")
            for field, value in record_payload.fields.items():
                setattr(cpu, field, value)
            if record_payload.attributes:
                merged = dict(cpu.attributes_json or {})
                for key, value in record_payload.attributes.items():
                    if value is None:
                        merged.pop(key, None)
                    else:
                        merged[key] = value
                cpu.attributes_json = merged
            await db.flush()
            await db.refresh(cpu)
            return self._serialize_cpu(cpu)
        raise ValueError(f"Unsupported entity '{entity}'")

    def _normalize_payload(
        self,
        entity: str,
        data: Mapping[str, Any],
        *,
        for_update: bool = False,
    ) -> RecordPayload:
        fields = dict(data.get("fields") or {})
        attributes = dict(data.get("attributes") or {})
        if entity == "listing":
            # Basic validation for numeric coercion
            for key in ("price_usd", "ram_gb", "primary_storage_gb", "secondary_storage_gb"):
                if key in fields and fields[key] is not None:
                    fields[key] = float(fields[key])
        elif entity == "cpu":
            if "attributes_json" in fields:
                maybe_attributes = fields.pop("attributes_json") or {}
                if isinstance(maybe_attributes, Mapping):
                    attributes.update(maybe_attributes)
        return RecordPayload(fields=fields, attributes=attributes)

    async def _count(self, db: AsyncSession, model) -> int:
        result = await db.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    def _require_entity(self, entity: str) -> EntityMeta:
        try:
            return self.entities[entity]
        except KeyError as exc:
            raise ValueError(f"Unknown entity '{entity}'") from exc

    def _listing_core_fields(self) -> list[FieldMeta]:
        from ..api.listings import CORE_LISTING_FIELDS

        fields: list[FieldMeta] = []
        for field_schema in CORE_LISTING_FIELDS:
            fields.append(
                FieldMeta(
                    key=field_schema.key,
                    label=field_schema.label,
                    data_type=field_schema.data_type,
                    required=getattr(field_schema, "required", False),
                    description=field_schema.description,
                    origin="core",
                    editable=getattr(field_schema, "editable", True),
                    locked=True,
                    options=field_schema.options,
                )
            )
        return fields

    def _cpu_core_fields(self) -> list[FieldMeta]:
        mapper = sa_inspect(Cpu)
        skip_keys = {"id", "created_at", "updated_at", "attributes_json"}
        label_overrides = {
            "igpu_model": "iGPU Model",
            "igpu_mark": "iGPU Mark",
            "cpu_mark_multi": "CPU Mark (Multi)",
            "cpu_mark_single": "CPU Mark (Single)",
            "tdp_w": "TDP (W)",
            "passmark_slug": "PassMark Slug",
            "passmark_category": "PassMark Category",
            "passmark_id": "PassMark ID",
        }

        def format_label(key: str) -> str:
            return label_overrides.get(key, key.replace("_", " ").title().replace("Cpu", "CPU"))

        numeric_types = (
            sqltypes.Integer,
            sqltypes.Numeric,
            sqltypes.Float,
            sqltypes.BigInteger,
            sqltypes.SmallInteger,
        )
        text_types = (sqltypes.Text, sqltypes.UnicodeText)

        def infer_type(column_type: sqltypes.TypeEngine) -> str:
            if isinstance(column_type, numeric_types):
                return "number"
            if isinstance(column_type, sqltypes.Boolean):
                return "boolean"
            if isinstance(column_type, text_types):
                return "text"
            if isinstance(column_type, sqltypes.JSON):
                return "json"
            return "string"

        fields: list[FieldMeta] = []
        for column in mapper.columns:
            key = column.key
            if key in skip_keys:
                continue
            fields.append(
                FieldMeta(
                    key=key,
                    label=format_label(key),
                    data_type=infer_type(column.type),
                    required=not column.nullable,
                    origin="core",
                    locked=True,
                )
            )
        return fields

    def _serialize_listing(self, listing: Listing) -> dict[str, Any]:
        data = ListingRead.model_validate(listing).model_dump()
        return {
            "id": data["id"],
            "fields": {k: data.get(k) for k in self._listing_field_keys()},
            "attributes": data.get("attributes", {}) or {},
        }

    def _serialize_cpu(self, cpu: Cpu) -> dict[str, Any]:
        data = CpuRead.model_validate(cpu).model_dump()
        return {
            "id": data["id"],
            "fields": {key: data.get(key) for key in self._cpu_field_keys()},
            "attributes": dict(getattr(cpu, "attributes_json", {}) or {}),
        }

    def _listing_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["listing"].core_fields]

    def _cpu_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["cpu"].core_fields]


__all__ = ["FieldRegistry", "EntityMeta", "FieldMeta"]
