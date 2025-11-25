"""Service orchestrating combined core/custom field metadata and data operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from dealbrain_core.schemas import (
    CpuRead,
    GpuRead,
    ListingRead,
    PortsProfileRead,
    ProfileRead,
    RamSpecRead,
    StorageProfileRead,
)
from sqlalchemy import func, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import sqltypes

from ..models import Cpu, Gpu, Listing, PortsProfile, Profile, RamSpec, StorageProfile
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
            "gpu": EntityMeta(
                entity="gpu",
                label="GPUs",
                supports_custom_fields=True,
                core_fields=self._gpu_core_fields(),
            ),
            "ram_spec": EntityMeta(
                entity="ram_spec",
                label="RAM Specs",
                supports_custom_fields=True,
                core_fields=self._ram_spec_core_fields(),
            ),
            "storage_profile": EntityMeta(
                entity="storage_profile",
                label="Storage Profiles",
                supports_custom_fields=True,
                core_fields=self._storage_profile_core_fields(),
            ),
            "ports_profile": EntityMeta(
                entity="ports_profile",
                label="Ports Profiles",
                supports_custom_fields=True,
                core_fields=self._ports_profile_core_fields(),
            ),
            "profile": EntityMeta(
                entity="profile",
                label="Scoring Profiles",
                supports_custom_fields=False,
                core_fields=self._profile_core_fields(),
            ),
        }

    def get_entities(self) -> list[EntityMeta]:
        return list(self.entities.values())

    async def schema_for(self, db: AsyncSession, entity: str) -> dict[str, Any]:
        meta = self._require_entity(entity)
        custom: list[dict[str, Any]] = []
        if meta.supports_custom_fields:
            records = await self.custom_fields.list_fields(
                db, entity=entity, include_inactive=True, include_deleted=False
            )
            core_keys = {f.key for f in meta.core_fields}
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
                if record.key not in core_keys  # avoid duplicate keys colliding with core fields
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
        elif entity == "gpu":
            result = await db.execute(select(Gpu).order_by(Gpu.name).offset(offset).limit(limit))
            rows = result.scalars().all()
            total = await self._count(db, Gpu)
            serialized = [self._serialize_gpu(row) for row in rows]
        elif entity == "ram_spec":
            result = await db.execute(
                select(RamSpec).order_by(RamSpec.id.desc()).offset(offset).limit(limit)
            )
            rows = result.scalars().all()
            total = await self._count(db, RamSpec)
            serialized = [self._serialize_ram_spec(row) for row in rows]
        elif entity == "storage_profile":
            result = await db.execute(
                select(StorageProfile)
                .order_by(StorageProfile.id.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = result.scalars().all()
            total = await self._count(db, StorageProfile)
            serialized = [self._serialize_storage_profile(row) for row in rows]
        elif entity == "ports_profile":
            result = await db.execute(
                select(PortsProfile).order_by(PortsProfile.name).offset(offset).limit(limit)
            )
            rows = result.scalars().all()
            total = await self._count(db, PortsProfile)
            serialized = [self._serialize_ports_profile(row) for row in rows]
        elif entity == "profile":
            result = await db.execute(
                select(Profile).order_by(Profile.name).offset(offset).limit(limit)
            )
            rows = result.scalars().all()
            total = await self._count(db, Profile)
            serialized = [self._serialize_profile(row) for row in rows]
        else:
            raise ValueError(f"Unsupported entity '{entity}'")
        return {
            "entity": entity,
            "label": meta.label,
            "records": serialized,
            "pagination": {"limit": limit, "offset": offset, "total": total},
        }

    async def create_record(
        self, db: AsyncSession, *, entity: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._require_entity(entity)
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
        if entity == "gpu":
            gpu_payload = dict(record_payload.fields)
            if record_payload.attributes:
                gpu_payload["attributes_json"] = record_payload.attributes
            gpu = Gpu(**gpu_payload)
            db.add(gpu)
            await db.flush()
            await db.refresh(gpu)
            return self._serialize_gpu(gpu)
        if entity == "ram_spec":
            ram_spec_payload = dict(record_payload.fields)
            if record_payload.attributes:
                ram_spec_payload["attributes_json"] = record_payload.attributes
            ram_spec = RamSpec(**ram_spec_payload)
            db.add(ram_spec)
            await db.flush()
            await db.refresh(ram_spec)
            return self._serialize_ram_spec(ram_spec)
        if entity == "storage_profile":
            storage_profile_payload = dict(record_payload.fields)
            if record_payload.attributes:
                storage_profile_payload["attributes_json"] = record_payload.attributes
            storage_profile = StorageProfile(**storage_profile_payload)
            db.add(storage_profile)
            await db.flush()
            await db.refresh(storage_profile)
            return self._serialize_storage_profile(storage_profile)
        if entity == "ports_profile":
            ports_profile_payload = dict(record_payload.fields)
            if record_payload.attributes:
                ports_profile_payload["attributes_json"] = record_payload.attributes
            ports_profile = PortsProfile(**ports_profile_payload)
            db.add(ports_profile)
            await db.flush()
            await db.refresh(ports_profile)
            return self._serialize_ports_profile(ports_profile)
        if entity == "profile":
            profile_payload = dict(record_payload.fields)
            # Profile does not have attributes_json
            profile = Profile(**profile_payload)
            db.add(profile)
            await db.flush()
            await db.refresh(profile)
            return self._serialize_profile(profile)
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
        if entity == "gpu":
            gpu = await db.get(Gpu, record_id)
            if not gpu:
                raise LookupError("GPU not found")
            for field, value in record_payload.fields.items():
                setattr(gpu, field, value)
            if record_payload.attributes:
                merged = dict(gpu.attributes_json or {})
                for key, value in record_payload.attributes.items():
                    if value is None:
                        merged.pop(key, None)
                    else:
                        merged[key] = value
                gpu.attributes_json = merged
            await db.flush()
            await db.refresh(gpu)
            return self._serialize_gpu(gpu)
        if entity == "ram_spec":
            ram_spec = await db.get(RamSpec, record_id)
            if not ram_spec:
                raise LookupError("RAM Spec not found")
            for field, value in record_payload.fields.items():
                setattr(ram_spec, field, value)
            if record_payload.attributes:
                merged = dict(ram_spec.attributes_json or {})
                for key, value in record_payload.attributes.items():
                    if value is None:
                        merged.pop(key, None)
                    else:
                        merged[key] = value
                ram_spec.attributes_json = merged
            await db.flush()
            await db.refresh(ram_spec)
            return self._serialize_ram_spec(ram_spec)
        if entity == "storage_profile":
            storage_profile = await db.get(StorageProfile, record_id)
            if not storage_profile:
                raise LookupError("Storage Profile not found")
            for field, value in record_payload.fields.items():
                setattr(storage_profile, field, value)
            if record_payload.attributes:
                merged = dict(storage_profile.attributes_json or {})
                for key, value in record_payload.attributes.items():
                    if value is None:
                        merged.pop(key, None)
                    else:
                        merged[key] = value
                storage_profile.attributes_json = merged
            await db.flush()
            await db.refresh(storage_profile)
            return self._serialize_storage_profile(storage_profile)
        if entity == "ports_profile":
            ports_profile = await db.get(PortsProfile, record_id)
            if not ports_profile:
                raise LookupError("Ports Profile not found")
            for field, value in record_payload.fields.items():
                setattr(ports_profile, field, value)
            if record_payload.attributes:
                merged = dict(ports_profile.attributes_json or {})
                for key, value in record_payload.attributes.items():
                    if value is None:
                        merged.pop(key, None)
                    else:
                        merged[key] = value
                ports_profile.attributes_json = merged
            await db.flush()
            await db.refresh(ports_profile)
            return self._serialize_ports_profile(ports_profile)
        if entity == "profile":
            profile = await db.get(Profile, record_id)
            if not profile:
                raise LookupError("Profile not found")
            for field, value in record_payload.fields.items():
                setattr(profile, field, value)
            # Profile does not support attributes_json
            await db.flush()
            await db.refresh(profile)
            return self._serialize_profile(profile)
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
        elif entity in (  # noqa: SIM102
            "cpu",
            "gpu",
            "ram_spec",
            "storage_profile",
            "ports_profile",
        ):
            if "attributes_json" in fields and isinstance(
                maybe_attributes := fields.pop("attributes_json") or {}, Mapping
            ):
                attributes.update(maybe_attributes)
        # Profile does not have attributes_json, no special handling needed
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
        from ..api.listings.schema import CORE_LISTING_FIELDS

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

    def _gpu_core_fields(self) -> list[FieldMeta]:
        mapper = sa_inspect(Gpu)
        skip_keys = {"id", "created_at", "updated_at", "attributes_json"}
        label_overrides = {
            "gpu_mark": "GPU Mark",
            "metal_score": "Metal Score",
        }

        def format_label(key: str) -> str:
            return label_overrides.get(key, key.replace("_", " ").title().replace("Gpu", "GPU"))

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

    def _ram_spec_core_fields(self) -> list[FieldMeta]:
        mapper = sa_inspect(RamSpec)
        skip_keys = {"id", "created_at", "updated_at", "attributes_json"}
        label_overrides = {
            "ddr_generation": "DDR Generation",
            "speed_mhz": "Speed (MHz)",
            "module_count": "Module Count",
            "capacity_per_module_gb": "Capacity per Module (GB)",
            "total_capacity_gb": "Total Capacity (GB)",
        }

        def format_label(key: str) -> str:
            return label_overrides.get(key, key.replace("_", " ").title())

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
            if isinstance(column_type, sqltypes.Enum):
                return "string"
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

    def _storage_profile_core_fields(self) -> list[FieldMeta]:
        mapper = sa_inspect(StorageProfile)
        skip_keys = {"id", "created_at", "updated_at", "attributes_json"}
        label_overrides = {
            "capacity_gb": "Capacity (GB)",
            "performance_tier": "Performance Tier",
            "form_factor": "Form Factor",
        }

        def format_label(key: str) -> str:
            return label_overrides.get(key, key.replace("_", " ").title())

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
            if isinstance(column_type, sqltypes.Enum):
                return "string"
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

    def _ports_profile_core_fields(self) -> list[FieldMeta]:
        mapper = sa_inspect(PortsProfile)
        skip_keys = {"id", "created_at", "updated_at", "attributes_json"}
        label_overrides: dict[str, str] = {}

        def format_label(key: str) -> str:
            return label_overrides.get(key, key.replace("_", " ").title())

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

    def _profile_core_fields(self) -> list[FieldMeta]:
        mapper = sa_inspect(Profile)
        skip_keys = {"id", "created_at", "updated_at"}
        label_overrides = {
            "weights_json": "Metric Weights",
            "rule_group_weights": "Rule Group Weights",
            "is_default": "Default Profile",
        }

        def format_label(key: str) -> str:
            return label_overrides.get(key, key.replace("_", " ").title())

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

    def _serialize_gpu(self, gpu: Gpu) -> dict[str, Any]:
        data = GpuRead.model_validate(gpu).model_dump()
        return {
            "id": data["id"],
            "fields": {key: data.get(key) for key in self._gpu_field_keys()},
            "attributes": dict(getattr(gpu, "attributes_json", {}) or {}),
        }

    def _serialize_ram_spec(self, ram_spec: RamSpec) -> dict[str, Any]:
        data = RamSpecRead.model_validate(ram_spec).model_dump()
        return {
            "id": data["id"],
            "fields": {key: data.get(key) for key in self._ram_spec_field_keys()},
            "attributes": dict(getattr(ram_spec, "attributes_json", {}) or {}),
        }

    def _serialize_storage_profile(self, storage_profile: StorageProfile) -> dict[str, Any]:
        data = StorageProfileRead.model_validate(storage_profile).model_dump()
        return {
            "id": data["id"],
            "fields": {key: data.get(key) for key in self._storage_profile_field_keys()},
            "attributes": dict(getattr(storage_profile, "attributes_json", {}) or {}),
        }

    def _serialize_ports_profile(self, ports_profile: PortsProfile) -> dict[str, Any]:
        data = PortsProfileRead.model_validate(ports_profile).model_dump()
        return {
            "id": data["id"],
            "fields": {key: data.get(key) for key in self._ports_profile_field_keys()},
            "attributes": dict(getattr(ports_profile, "attributes_json", {}) or {}),
        }

    def _serialize_profile(self, profile: Profile) -> dict[str, Any]:
        data = ProfileRead.model_validate(profile).model_dump()
        return {
            "id": data["id"],
            "fields": {key: data.get(key) for key in self._profile_field_keys()},
            "attributes": {},  # Profile does not support custom fields
        }

    def _listing_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["listing"].core_fields]

    def _cpu_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["cpu"].core_fields]

    def _gpu_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["gpu"].core_fields]

    def _ram_spec_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["ram_spec"].core_fields]

    def _storage_profile_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["storage_profile"].core_fields]

    def _ports_profile_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["ports_profile"].core_fields]

    def _profile_field_keys(self) -> list[str]:
        return [field.key for field in self.entities["profile"].core_fields]


__all__ = ["FieldRegistry", "EntityMeta", "FieldMeta"]
