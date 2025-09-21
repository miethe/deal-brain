"""Service helpers that orchestrate spreadsheet import sessions."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import UUID, uuid4

import pandas as pd
from fastapi import UploadFile
from pandas import DataFrame
from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition
from dealbrain_core.schemas import (
    CpuCreate,
    GpuCreate,
    ListingComponentCreate,
    ListingCreate,
    PortsProfileCreate,
    PortCreate,
    ProfileCreate,
    SpreadsheetSeed,
    ValuationRuleCreate,
)

from ...models.core import Cpu, Gpu, ImportSession, ImportSessionAudit
from ...seeds import apply_seed
from ...settings import Settings, get_settings
from .specs import IMPORT_SCHEMAS, ImportSchema, SchemaField, iter_schemas
from .utils import checksum_bytes, ensure_directory, load_dataframe_preview, normalize_text


@dataclass
class MappingCandidate:
    column: str
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "confidence": round(self.confidence, 4),
            "reason": self.reason,
        }


class ImportSessionService:
    """Coordinates the importer workflow: upload, mapping, preview, and conflicts."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def create_session(
        self,
        db: AsyncSession,
        *,
        upload: UploadFile,
        created_by: str | None = None,
    ) -> ImportSession:
        raw_bytes = await upload.read()
        if not raw_bytes:
            raise ValueError("Uploaded file is empty")

        session_id = uuid4()
        filename = upload.filename or f"import-{session_id}.xlsx"
        upload_root = self.settings.upload_root / str(session_id) / "source"
        ensure_directory(upload_root)
        file_path = upload_root / filename
        file_path.write_bytes(raw_bytes)

        workbook = self._load_workbook(file_path)
        sheet_meta = self._inspect_workbook(workbook)
        mappings = self._generate_initial_mappings(sheet_meta)
        preview = self._build_preview(workbook, mappings)

        import_session = ImportSession(
            id=session_id,
            filename=filename,
            content_type=upload.content_type,
            checksum=checksum_bytes(raw_bytes),
            upload_path=str(file_path),
            status="mapping_required",
            sheet_meta_json=sheet_meta,
            mappings_json=mappings,
            preview_json=preview,
            conflicts_json={},
            created_by=created_by,
        )
        db.add(import_session)
        await db.flush()
        await db.refresh(import_session)

        self._record_audit(db, import_session, event="session_created", payload={
            "filename": filename,
            "sheet_count": len(workbook),
        })
        return import_session

    async def refresh_preview(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        workbook = self._load_workbook(Path(import_session.upload_path))
        preview = self._build_preview(workbook, import_session.mappings_json, limit=limit)
        preview = await self._enrich_listing_preview(db, preview, import_session, workbook)
        import_session.preview_json = preview
        await db.flush()
        return preview

    async def update_mappings(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        mappings: dict[str, Any],
    ) -> ImportSession:
        merged_mappings = self._merge_mappings(import_session.mappings_json, mappings)
        import_session.mappings_json = merged_mappings
        preview = await self.refresh_preview(db, import_session)
        self._record_audit(db, import_session, event="mappings_updated", payload={"entities": list(mappings.keys())})
        return import_session

    async def compute_conflicts(
        self,
        db: AsyncSession,
        import_session: ImportSession,
    ) -> dict[str, Any]:
        workbook = self._load_workbook(Path(import_session.upload_path))
        conflicts: dict[str, Any] = {}
        if cpu_conflicts := await self._detect_cpu_conflicts(db, workbook, import_session.mappings_json):
            conflicts["cpu"] = cpu_conflicts
        import_session.conflicts_json = conflicts
        await db.flush()
        return conflicts

    async def commit(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        conflict_resolutions: Mapping[str, str],
        component_overrides: Mapping[int, dict[str, Any]],
    ) -> dict[str, int]:
        workbook = self._load_workbook(Path(import_session.upload_path))
        self._validate_conflicts(import_session.conflicts_json, conflict_resolutions)

        cpu_lookup = await self._load_cpu_lookup(db)
        gpu_lookup = await self._load_gpu_lookup(db)

        seed = self._build_seed(
            workbook,
            import_session.mappings_json,
            conflict_resolutions=conflict_resolutions,
            component_overrides=component_overrides,
            cpu_lookup=cpu_lookup,
            gpu_lookup=gpu_lookup,
        )

        await apply_seed(seed)

        counts = {
            "cpus": len(seed.cpus),
            "gpus": len(seed.gpus),
            "valuation_rules": len(seed.valuation_rules),
            "ports_profiles": len(seed.ports_profiles),
            "listings": len(seed.listings),
        }

        import_session.status = "completed"
        import_session.conflicts_json = {}
        self._record_audit(db, import_session, event="commit_success", payload=counts)
        await db.flush()
        return counts

    def _load_workbook(self, path: Path) -> dict[str, DataFrame]:
        suffix = path.suffix.lower()
        if suffix in {".xlsx", ".xlsm", ".xls"}:
            sheets = pd.read_excel(path, sheet_name=None, dtype=object)
        elif suffix in {".csv", ".tsv"}:
            sep = "," if suffix == ".csv" else "\t"
            sheets = {path.stem: pd.read_csv(path, sep=sep, dtype=object)}
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
        normalized: dict[str, DataFrame] = {}
        for name, df in sheets.items():
            dataframe = df if isinstance(df, DataFrame) else pd.DataFrame(df)
            dataframe.columns = [str(column) for column in dataframe.columns]
            normalized[name] = dataframe
        return normalized

    def _validate_conflicts(
        self,
        conflicts: Mapping[str, Any] | None,
        resolutions: Mapping[str, str],
    ) -> None:
        if not conflicts:
            return
        cpu_conflicts = conflicts.get("cpu") or []
        unresolved = [conflict["name"] for conflict in cpu_conflicts if conflict["name"] not in resolutions]
        if unresolved:
            raise ValueError(f"Unresolved CPU conflicts: {', '.join(unresolved)}")
        invalid = [
            name
            for name, action in resolutions.items()
            if action not in {"update", "skip", "keep"}
        ]
        if invalid:
            raise ValueError(f"Invalid resolution actions for: {', '.join(invalid)}")

    async def _load_cpu_lookup(self, db: AsyncSession) -> dict[str, int]:
        result = await db.execute(select(Cpu.id, Cpu.name))
        lookup: dict[str, int] = {}
        for cpu_id, name in result.all():
            if not name:
                continue
            lookup[normalize_text(str(name))] = cpu_id
        return lookup

    async def _load_gpu_lookup(self, db: AsyncSession) -> dict[str, int]:
        result = await db.execute(select(Gpu.id, Gpu.name))
        lookup: dict[str, int] = {}
        for gpu_id, name in result.all():
            if not name:
                continue
            lookup[normalize_text(str(name))] = gpu_id
        return lookup

    def _build_seed(
        self,
        workbook: Mapping[str, DataFrame],
        mappings: Mapping[str, Any],
        *,
        conflict_resolutions: Mapping[str, str],
        component_overrides: Mapping[int, dict[str, Any]],
        cpu_lookup: Mapping[str, int],
        gpu_lookup: Mapping[str, int],
    ) -> SpreadsheetSeed:
        seed = SpreadsheetSeed()

        cpu_mapping = mappings.get("cpu") if mappings else None
        if cpu_mapping:
            dataframe = workbook.get(cpu_mapping.get("sheet"))
            if dataframe is not None:
                seed.cpus = self._build_cpus(dataframe, cpu_mapping.get("fields", {}), conflict_resolutions)

        gpu_mapping = mappings.get("gpu") if mappings else None
        if gpu_mapping:
            dataframe = workbook.get(gpu_mapping.get("sheet"))
            if dataframe is not None:
                seed.gpus = self._build_gpus(dataframe, gpu_mapping.get("fields", {}))

        rules_mapping = mappings.get("valuation_rule") if mappings else None
        if rules_mapping:
            dataframe = workbook.get(rules_mapping.get("sheet"))
            if dataframe is not None:
                seed.valuation_rules = self._build_rules(dataframe, rules_mapping.get("fields", {}))

        ports_mapping = mappings.get("ports_profile") if mappings else None
        if ports_mapping:
            dataframe = workbook.get(ports_mapping.get("sheet"))
            if dataframe is not None:
                seed.ports_profiles = self._build_ports_profiles(dataframe, ports_mapping.get("fields", {}))

        listing_mapping = mappings.get("listing") if mappings else None
        if listing_mapping:
            dataframe = workbook.get(listing_mapping.get("sheet"))
            if dataframe is not None:
                seed.listings = self._build_listings(
                    dataframe,
                    listing_mapping.get("fields", {}),
                    component_overrides=component_overrides,
                    cpu_lookup=cpu_lookup,
                    gpu_lookup=gpu_lookup,
                )

        if not seed.profiles:
            seed.profiles = self._default_profiles()
        if not seed.ports_profiles:
            seed.ports_profiles = self._default_ports_profiles()

        return seed

    def _build_cpus(
        self,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        conflict_resolutions: Mapping[str, str],
    ) -> list[CpuCreate]:
        name_column = field_mappings.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []
        cpus: list[CpuCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = self._to_str(row.get(name_column))
            if not name:
                continue
            action = conflict_resolutions.get(name)
            if action in {"skip", "keep"}:
                continue
            cpu = CpuCreate(
                name=name,
                manufacturer=self._to_str(self._extract_value(row, field_mappings, "manufacturer")) or "Unknown",
                socket=self._to_str(self._extract_value(row, field_mappings, "socket")),
                cores=self._to_int(self._extract_value(row, field_mappings, "cores")),
                threads=self._to_int(self._extract_value(row, field_mappings, "threads")),
                tdp_w=self._to_int(self._extract_value(row, field_mappings, "tdp_w")),
                igpu_model=self._to_str(self._extract_value(row, field_mappings, "igpu_model")),
                cpu_mark_multi=self._to_int(self._extract_value(row, field_mappings, "cpu_mark_multi")),
                cpu_mark_single=self._to_int(self._extract_value(row, field_mappings, "cpu_mark_single")),
                release_year=self._to_int(self._extract_value(row, field_mappings, "release_year")),
                notes=self._to_str(self._extract_value(row, field_mappings, "notes")),
            )
            cpus.append(cpu)
        return cpus

    def _build_gpus(
        self,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
    ) -> list[GpuCreate]:
        name_column = field_mappings.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []
        gpus: list[GpuCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = self._to_str(row.get(name_column))
            if not name:
                continue
            gpu = GpuCreate(
                name=name,
                manufacturer=self._to_str(self._extract_value(row, field_mappings, "manufacturer")) or "Unknown",
                gpu_mark=self._to_int(self._extract_value(row, field_mappings, "gpu_mark")),
                metal_score=self._to_int(self._extract_value(row, field_mappings, "metal_score")),
                notes=self._to_str(self._extract_value(row, field_mappings, "notes")),
            )
            gpus.append(gpu)
        return gpus

    def _build_rules(
        self,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
    ) -> list[ValuationRuleCreate]:
        name_column = field_mappings.get("name", {}).get("column")
        component_column = field_mappings.get("component_type", {}).get("column")
        unit_value_column = field_mappings.get("unit_value_usd", {}).get("column")
        if not name_column or not component_column or not unit_value_column:
            return []
        rules: list[ValuationRuleCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = self._to_str(row.get(name_column))
            component_value = self._to_str(row.get(component_column))
            unit_value = self._to_float(row.get(unit_value_column))
            if not name or not component_value or unit_value is None:
                continue
            rules.append(
                ValuationRuleCreate(
                    name=name,
                    component_type=self._parse_component_type(component_value),
                    metric=self._parse_metric(self._extract_value(row, field_mappings, "metric")),
                    unit_value_usd=unit_value,
                    condition_new=self._to_float(self._extract_value(row, field_mappings, "condition_new")) or 1.0,
                    condition_refurb=self._to_float(self._extract_value(row, field_mappings, "condition_refurb")) or 0.75,
                    condition_used=self._to_float(self._extract_value(row, field_mappings, "condition_used")) or 0.6,
                    notes=self._to_str(self._extract_value(row, field_mappings, "notes")),
                )
            )
        return rules

    def _build_ports_profiles(
        self,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
    ) -> list[PortsProfileCreate]:
        name_column = field_mappings.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []
        profiles: list[PortsProfileCreate] = []
        for row in dataframe.fillna("").to_dict(orient="records"):
            name = self._to_str(row.get(name_column))
            if not name:
                continue
            profiles.append(
                PortsProfileCreate(
                    name=name,
                    description=self._to_str(self._extract_value(row, field_mappings, "description")),
                    ports=self._parse_ports_blob(self._extract_value(row, field_mappings, "ports")) or None,
                )
            )
        return profiles

    def _build_listings(
        self,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        *,
        component_overrides: Mapping[int, dict[str, Any]],
        cpu_lookup: Mapping[str, int],
        gpu_lookup: Mapping[str, int],
    ) -> list[ListingCreate]:
        title_column = field_mappings.get("title", {}).get("column")
        price_column = field_mappings.get("price_usd", {}).get("column")
        if not title_column or title_column not in dataframe.columns:
            return []

        cpu_column = field_mappings.get("cpu_name", {}).get("column")
        match_lookup: dict[int, dict[str, Any]] = {}
        if cpu_column:
            matches = self._match_components(dataframe, cpu_column, list(cpu_lookup.keys()), limit=None)
            match_lookup = {match["row_index"]: match for match in matches}

        listings: list[ListingCreate] = []
        records = dataframe.fillna("").to_dict(orient="records")
        for index, row in enumerate(records):
            title = self._to_str(row.get(title_column))
            if not title:
                continue
            price_value = self._to_float(row.get(price_column)) or 0.0
            condition_value = self._parse_condition(self._extract_value(row, field_mappings, "condition"))

            override = component_overrides.get(index, {})
            match_data = match_lookup.get(index)
            cpu_assignment = self._resolve_cpu_assignment(override, match_data)
            cpu_id = cpu_lookup.get(normalize_text(cpu_assignment)) if cpu_assignment else None

            gpu_assignment = self._to_str(
                override.get("gpu_match") if override else self._extract_value(row, field_mappings, "gpu_name")
            )
            gpu_id = gpu_lookup.get(normalize_text(gpu_assignment)) if gpu_assignment else None

            listing = ListingCreate(
                title=title,
                price_usd=price_value,
                condition=condition_value,
                cpu_id=cpu_id,
                gpu_id=gpu_id,
                ports_profile_id=None,
                ram_gb=self._to_int(self._extract_value(row, field_mappings, "ram_gb")) or 0,
                ram_notes=self._to_str(self._extract_value(row, field_mappings, "ram_notes")),
                primary_storage_gb=self._parse_storage_capacity(self._extract_value(row, field_mappings, "primary_storage_gb")),
                primary_storage_type=self._to_str(self._extract_value(row, field_mappings, "primary_storage_type")),
                secondary_storage_gb=self._parse_storage_capacity(self._extract_value(row, field_mappings, "secondary_storage_gb")) or None,
                secondary_storage_type=self._to_str(self._extract_value(row, field_mappings, "secondary_storage_type")),
                os_license=self._to_str(self._extract_value(row, field_mappings, "os_license")),
                notes=self._to_str(self._extract_value(row, field_mappings, "notes")),
                components=None,
            )

            components: list[ListingComponentCreate] = []
            gpu_name_raw = self._to_str(self._extract_value(row, field_mappings, "gpu_name"))
            if gpu_name_raw and not gpu_id:
                components.append(
                    ListingComponentCreate(
                        component_type=ComponentType.GPU,
                        name=gpu_name_raw,
                        metadata_json=None,
                    )
                )
            listing.components = components or None
            listings.append(listing)
        return listings

    def _resolve_cpu_assignment(
        self,
        override: Mapping[str, Any] | None,
        match_data: Mapping[str, Any] | None,
    ) -> str | None:
        if override and override.get("cpu_match"):
            return self._to_str(override.get("cpu_match"))
        if match_data and match_data.get("status") == "auto":
            return self._to_str(match_data.get("auto_match"))
        return None

    def _parse_condition(self, value: Any) -> Condition:
        text = self._to_str(value)
        if not text:
            return Condition.USED
        normalized = text.lower().strip()
        if normalized in Condition._value2member_map_:
            return Condition(normalized)
        aliases = {
            "refurbished": Condition.REFURB,
            "refurb": Condition.REFURB,
            "new": Condition.NEW,
            "used": Condition.USED,
        }
        return aliases.get(normalized, Condition.USED)

    def _parse_component_type(self, value: Any) -> ComponentType:
        text = normalize_text(str(value))
        mapping = {
            "memory": ComponentType.RAM,
            "ram": ComponentType.RAM,
            "ssd": ComponentType.SSD,
            "hdd": ComponentType.HDD,
            "storage": ComponentType.SSD,
            "os": ComponentType.OS_LICENSE,
            "os license": ComponentType.OS_LICENSE,
            "wifi": ComponentType.WIFI,
            "gpu": ComponentType.GPU,
        }
        if text in mapping:
            return mapping[text]
        if text in ComponentType._value2member_map_:
            return ComponentType(text)
        return ComponentType.MISC

    def _parse_metric(self, value: Any) -> ComponentMetric:
        text = self._to_str(value)
        if not text:
            return ComponentMetric.FLAT
        normalized = normalize_text(text)
        if "tb" in normalized:
            return ComponentMetric.PER_TB
        if "gb" in normalized:
            return ComponentMetric.PER_GB
        if normalized in ComponentMetric._value2member_map_:
            return ComponentMetric(normalized)
        return ComponentMetric.FLAT

    def _parse_ports_blob(self, value: Any) -> list[PortCreate]:
        text = self._to_str(value)
        if not text:
            return []
        try:
            data = json.loads(text)
            ports: list[PortCreate] = []
            if isinstance(data, list):
                for entry in data:
                    if not isinstance(entry, dict):
                        continue
                    port_type = entry.get("type")
                    if not port_type:
                        continue
                    ports.append(
                        PortCreate(
                            type=str(port_type),
                            count=int(entry.get("count") or 1),
                            spec_notes=self._to_str(entry.get("spec_notes")),
                        )
                    )
            return ports
        except (ValueError, TypeError):
            return []

    def _get_cell(
        self,
        row: Mapping[str, Any],
        field_mappings: Mapping[str, Any],
        key: str,
    ) -> Any:
        mapping = field_mappings.get(key, {})
        column = mapping.get("column")
        if not column:
            return None
        return row.get(column)

    def _extract_value(
        self,
        row: Mapping[str, Any],
        field_mappings: Mapping[str, Any],
        key: str,
    ) -> Any:
        value = self._get_cell(row, field_mappings, key)
        return self._coerce_value(value)

    def _to_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _to_int(self, value: Any) -> int | None:
        float_value = self._to_float(value)
        if float_value is None:
            return None
        try:
            return int(round(float_value))
        except (TypeError, ValueError):
            return None

    def _to_float(self, value: Any) -> float | None:
        if value is None:
            return None
        text = str(value).strip().replace("$", "").replace(",", "")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_storage_capacity(self, value: Any) -> int:
        text = self._to_str(value)
        if not text:
            return 0
        lowered = text.lower().replace("tb", "000").replace("gb", "").strip()
        parts = lowered.split()
        candidate = parts[0] if parts else lowered
        try:
            return int(float(candidate))
        except (ValueError, TypeError):
            return 0

    def _default_profiles(self) -> list[ProfileCreate]:
        return [
            ProfileCreate(
                name="Proxmox",
                description="Heavy virtualization workloads",
                weights_json={
                    "cpu_mark_multi": 0.5,
                    "ram_capacity": 0.2,
                    "expandability": 0.2,
                    "perf_per_watt": 0.1,
                },
                is_default=True,
            ),
            ProfileCreate(
                name="Plex",
                description="Media server and transcoding",
                weights_json={
                    "cpu_mark_single": 0.4,
                    "encoder_capability": 0.4,
                    "perf_per_watt": 0.2,
                },
            ),
        ]

    def _default_ports_profiles(self) -> list[PortsProfileCreate]:
        return [
            PortsProfileCreate(
                name="Baseline SFF",
                description="Default configuration with typical SFF connectivity",
                ports=[
                    PortCreate(type="usb_a", count=4),
                    PortCreate(type="usb_c", count=2),
                    PortCreate(type="rj45_2_5g", count=1),
                    PortCreate(type="hdmi", count=1),
                ],
            )
        ]

    def _inspect_workbook(self, workbook: Mapping[str, DataFrame]) -> list[dict[str, Any]]:
        sheet_meta: list[dict[str, Any]] = []
        for sheet_name, dataframe in workbook.items():
            columns = [str(column) for column in dataframe.columns]
            best_schema, confidence = self._infer_schema(sheet_name, columns)
            sheet_meta.append(
                {
                    "sheet_name": sheet_name,
                    "row_count": int(dataframe.shape[0]),
                    "columns": [
                        {
                            "name": column,
                            "samples": [
                                value
                                for value in dataframe[column]
                                .fillna(" ")
                                .astype(str)
                                .head(3)
                                .tolist()
                                if value.strip()
                            ],
                        }
                        for column in columns
                    ],
                    "entity": best_schema.entity if best_schema else None,
                    "entity_label": best_schema.label if best_schema else None,
                    "confidence": round(confidence, 3),
                }
            )
        return sheet_meta

    def _infer_schema(self, sheet_name: str, columns: Iterable[str]) -> tuple[ImportSchema | None, float]:
        best_schema: ImportSchema | None = None
        best_score = 0.0
        for schema in iter_schemas():
            score = schema.score_columns(columns) + schema.keyword_bonus(sheet_name)
            if score > best_score:
                best_score = score
                best_schema = schema
        if best_score < 0.25:
            return None, best_score
        return best_schema, min(best_score, 1.0)

    def _generate_initial_mappings(self, sheet_meta: list[dict[str, Any]]) -> dict[str, Any]:
        mappings: dict[str, Any] = {}
        for entry in sheet_meta:
            entity = entry.get("entity")
            if not entity or entity in mappings:
                continue
            schema = IMPORT_SCHEMAS.get(entity)
            if not schema:
                continue
            columns = [column_info["name"] for column_info in entry.get("columns", [])]
            mappings[entity] = {
                "sheet": entry["sheet_name"],
                "fields": self._auto_map_fields(schema, columns),
            }
        return mappings

    def _auto_map_fields(self, schema: ImportSchema, columns: list[str]) -> dict[str, Any]:
        field_mappings: dict[str, Any] = {}
        for field in schema.fields:
            suggestions = self._rank_columns(field, columns)
            best = suggestions[0] if suggestions else None
            mapped_column = best.column if best and best.confidence >= 0.65 else None
            status = "auto" if mapped_column else "missing"
            field_mappings[field.key] = {
                "field": field.key,
                "label": field.label,
                "required": field.required,
                "data_type": field.data_type,
                "column": mapped_column,
                "confidence": round(best.confidence, 4) if best else 0.0,
                "status": status,
                "suggestions": [candidate.to_dict() for candidate in suggestions[:5]],
            }
        return field_mappings

    def _rank_columns(self, field: SchemaField, columns: list[str]) -> list[MappingCandidate]:
        candidates: list[MappingCandidate] = []
        normalized_aliases = {normalize_text(alias) for alias in field.all_keys}
        for column in columns:
            normalized_column = normalize_text(column)
            if not normalized_column:
                continue
            if normalized_column in normalized_aliases:
                candidates.append(MappingCandidate(column=column, confidence=1.0, reason="exact"))
                continue
            best_alias, score = self._best_alias_score(normalized_column, normalized_aliases)
            if score > 0.0:
                candidates.append(
                    MappingCandidate(column=column, confidence=score, reason=f"fuzzy:{best_alias}")
                )
        return sorted(candidates, key=lambda candidate: candidate.confidence, reverse=True)

    def _best_alias_score(self, column: str, aliases: set[str]) -> tuple[str, float]:
        best_alias = ""
        best_score = 0.0
        for alias in aliases:
            score = fuzz.token_set_ratio(column, alias) / 100
            if score > best_score:
                best_score = score
                best_alias = alias
        return best_alias, best_score

    def _build_preview(
        self,
        workbook: Mapping[str, DataFrame],
        mappings: Mapping[str, Any],
        limit: int = 5,
    ) -> dict[str, Any]:
        preview: dict[str, Any] = {}
        for entity, config in mappings.items():
            sheet = config.get("sheet")
            fields = config.get("fields", {})
            schema = IMPORT_SCHEMAS.get(entity)
            dataframe = workbook.get(sheet)
            if not schema or dataframe is None:
                continue
            rows = self._preview_rows(schema, dataframe, fields, limit=limit)
            preview[entity] = rows
        return preview

    def _preview_rows(
        self,
        schema: ImportSchema,
        dataframe: DataFrame,
        field_mappings: Mapping[str, Any],
        *,
        limit: int,
    ) -> dict[str, Any]:
        required_missing = [
            field.key
            for field in schema.fields
            if field.required and not field_mappings.get(field.key, {}).get("column")
        ]
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(load_dataframe_preview(dataframe, limit=limit)):
            mapped_row: dict[str, Any] = {"__row": index}
            for field in schema.fields:
                column = field_mappings.get(field.key, {}).get("column")
                mapped_row[field.key] = row.get(column) if column else None
            rows.append(mapped_row)
        return {
            "rows": rows,
            "missing_required_fields": required_missing,
            "total_rows": int(dataframe.shape[0]),
            "mapped_field_count": sum(1 for field in schema.fields if field_mappings.get(field.key, {}).get("column")),
        }

    def _merge_mappings(
        self,
        current: Mapping[str, Any],
        incoming: Mapping[str, Any],
    ) -> dict[str, Any]:
        merged = {entity: {**data} for entity, data in current.items()}
        for entity, payload in incoming.items():
            entity_settings = merged.setdefault(entity, {})
            if "sheet" in payload:
                entity_settings["sheet"] = payload["sheet"]
            incoming_fields = payload.get("fields")
            if incoming_fields:
                fields = entity_settings.setdefault("fields", {})
                schema = IMPORT_SCHEMAS.get(entity)
                for field_key, mapping in incoming_fields.items():
                    existing = fields.get(field_key, {})
                    field_def = schema.field_by_key(field_key) if schema else None
                    fields[field_key] = {
                        "field": field_key,
                        "label": existing.get("label")
                        or mapping.get("label")
                        or (field_def.label if field_def else field_key.replace("_", " ").title()),
                        "required": existing.get("required")
                        if "required" in existing
                        else mapping.get("required", field_def.required if field_def else False),
                        "data_type": existing.get("data_type")
                        or mapping.get("data_type")
                        or (field_def.data_type if field_def else "string"),
                        "column": mapping.get("column"),
                        "status": mapping.get("status", existing.get("status", "manual")),
                        "confidence": mapping.get("confidence", existing.get("confidence", 0.0)),
                        "suggestions": mapping.get("suggestions", existing.get("suggestions", [])),
                    }
        return merged

    async def _enrich_listing_preview(
        self,
        db: AsyncSession,
        preview: dict[str, Any],
        import_session: ImportSession,
        workbook: Mapping[str, DataFrame],
    ) -> dict[str, Any]:
        listing_preview = preview.get("listing")
        mapping = import_session.mappings_json.get("listing") if import_session.mappings_json else None
        if not listing_preview or not mapping:
            return preview
        sheet_cpu_column = mapping.get("fields", {}).get("cpu_name", {}).get("column")
        if not sheet_cpu_column:
            return preview

        dataframe = workbook.get(mapping.get("sheet"))
        if dataframe is None:
            return preview

        cpu_names = await self._load_cpu_names(db)
        suggestions = self._match_components(dataframe, sheet_cpu_column, cpu_names)
        listing_preview["component_matches"] = suggestions
        preview["listing"] = listing_preview
        return preview

    async def _load_cpu_names(self, db: AsyncSession) -> list[str]:
        result = await db.execute(select(Cpu.name))
        return [row[0] for row in result.all() if row[0]]

    def _match_components(
        self,
        dataframe: DataFrame,
        column: str,
        cpu_names: list[str],
        *,
        limit: int | None = 100,
    ) -> list[dict[str, Any]]:
        if column not in dataframe.columns:
            return []
        values = dataframe[column].fillna("").astype(str).tolist()
        matches: list[dict[str, Any]] = []
        iterable = values if limit is None else values[:limit]
        for idx, value in enumerate(iterable):
            normalized = value.strip()
            if not normalized:
                matches.append(
                    {
                        "row_index": idx,
                        "value": value,
                        "status": "unmatched",
                        "suggestions": [],
                    }
                )
                continue
            suggestions = process.extract(normalized, cpu_names, scorer=fuzz.WRatio, limit=3)
            structured = [
                {"match": suggestion[0], "confidence": round(suggestion[1] / 100, 4)}
                for suggestion in suggestions
            ]
            top_confidence = structured[0]["confidence"] if structured else 0.0
            status = "unmatched"
            auto = None
            if top_confidence >= 0.9:
                status = "auto"
                auto = structured[0]["match"]
            elif top_confidence >= 0.75:
                status = "review"
            matches.append(
                {
                    "row_index": idx,
                    "value": value,
                    "status": status,
                    "auto_match": auto,
                    "suggestions": structured,
                }
            )
        return matches

    async def _detect_cpu_conflicts(
        self,
        db: AsyncSession,
        workbook: Mapping[str, DataFrame],
        mappings: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        cpu_mapping = mappings.get("cpu") if mappings else None
        if not cpu_mapping:
            return []
        sheet = cpu_mapping.get("sheet")
        dataframe = workbook.get(sheet)
        if dataframe is None:
            return []

        fields = cpu_mapping.get("fields", {})
        name_column = fields.get("name", {}).get("column")
        if not name_column or name_column not in dataframe.columns:
            return []

        records = dataframe.fillna("").to_dict(orient="records")
        incoming: dict[str, dict[str, Any]] = {}
        for row in records:
            name = str(row.get(name_column, "")).strip()
            if not name:
                continue
            incoming[name] = {
                key: self._coerce_value(row.get(mapping.get("column"))) if mapping.get("column") else None
                for key, mapping in fields.items()
            }
        if not incoming:
            return []

        existing = await db.execute(select(Cpu).where(Cpu.name.in_(incoming.keys())))
        conflicts: list[dict[str, Any]] = []
        for cpu in existing.scalars():
            desired = incoming.get(cpu.name)
            if not desired:
                continue
            diff = self._cpu_differences(cpu, desired)
            if diff:
                conflicts.append(
                    {
                        "name": cpu.name,
                        "existing": diff["existing"],
                        "incoming": diff["incoming"],
                        "fields": diff["fields"],
                    }
                )
        return conflicts

    def _cpu_differences(self, cpu: Cpu, incoming: Mapping[str, Any]) -> dict[str, Any] | None:
        tracked_fields = [
            "manufacturer",
            "socket",
            "cores",
            "threads",
            "tdp_w",
            "igpu_model",
            "cpu_mark_multi",
            "cpu_mark_single",
            "release_year",
            "notes",
        ]
        diffs: list[dict[str, Any]] = []
        for field in tracked_fields:
            new_value = self._normalize_numeric(incoming.get(field), field)
            existing_value = getattr(cpu, field)
            if new_value in (None, "") and existing_value in (None, ""):
                continue
            if str(existing_value) != str(new_value):
                diffs.append(
                    {
                        "field": field,
                        "existing": existing_value,
                        "incoming": new_value,
                    }
                )
        if not diffs:
            return None
        return {
            "existing": {field: getattr(cpu, field) for field in tracked_fields},
            "incoming": {field: self._normalize_numeric(incoming.get(field), field) for field in tracked_fields},
            "fields": diffs,
        }

    def _normalize_numeric(self, value: Any, field: str) -> Any:
        if value in (None, ""):
            return None
        if field in {"cores", "threads", "tdp_w", "cpu_mark_multi", "cpu_mark_single", "release_year"}:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return value
        return value

    def _coerce_value(self, value: Any) -> Any:
        if value is None:
            return None
        if value == "":
            return None
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
        return value

    def _record_audit(
        self,
        db: AsyncSession,
        import_session: ImportSession,
        *,
        event: str,
        payload: Mapping[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        audit = ImportSessionAudit(
            session_id=import_session.id,
            event=event,
            message=message,
            payload_json=payload if payload is not None else None,
        )
        db.add(audit)


__all__ = ["ImportSessionService", "MappingCandidate"]
