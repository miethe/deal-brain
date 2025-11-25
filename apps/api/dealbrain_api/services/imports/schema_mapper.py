"""Schema mapping and inference for import sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from pandas import DataFrame
from rapidfuzz import fuzz

from .specs import IMPORT_SCHEMAS, ImportSchema, SchemaField, iter_schemas
from .utils import normalize_text


@dataclass
class MappingCandidate:
    """Represents a candidate column mapping with confidence score."""

    column: str
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "confidence": round(self.confidence, 4),
            "reason": self.reason,
        }


class SchemaMapper:
    """Handles schema inference and field mapping for workbook sheets."""

    @staticmethod
    def inspect_workbook(
        workbook: Mapping[str, DataFrame],
        *,
        declared_entities: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Inspect workbook sheets and infer entity types.

        Args:
            workbook: Dictionary of sheet names to DataFrames
            declared_entities: Optional mapping of sheet names to declared entity types

        Returns:
            List of sheet metadata dictionaries with inferred entity types
        """
        sheet_meta: list[dict[str, Any]] = []
        for sheet_name, dataframe in workbook.items():
            columns = [str(column) for column in dataframe.columns]
            declared_entity = (declared_entities or {}).get(sheet_name)

            if declared_entity:
                best_schema = IMPORT_SCHEMAS.get(declared_entity)
                confidence = 1.0 if best_schema else 0.0
            else:
                best_schema, confidence = SchemaMapper._infer_schema(sheet_name, columns)

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
                    "declared_entity": declared_entity,
                }
            )
        return sheet_meta

    @staticmethod
    def _infer_schema(sheet_name: str, columns: Iterable[str]) -> tuple[ImportSchema | None, float]:
        """
        Infer the most likely schema for a sheet based on column names.

        Args:
            sheet_name: Name of the sheet
            columns: List of column names

        Returns:
            Tuple of (best matching schema, confidence score)
        """
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

    @staticmethod
    def generate_initial_mappings(sheet_meta: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Generate initial field mappings for all sheets.

        Args:
            sheet_meta: List of sheet metadata from inspect_workbook

        Returns:
            Dictionary mapping entity types to their field mappings
        """
        mappings: dict[str, Any] = {}
        for entry in sheet_meta:
            entity = entry.get("declared_entity") or entry.get("entity")
            if not entity or entity in mappings:
                continue
            schema = IMPORT_SCHEMAS.get(entity)
            if not schema:
                continue
            columns = [column_info["name"] for column_info in entry.get("columns", [])]
            mappings[entity] = {
                "sheet": entry["sheet_name"],
                "fields": SchemaMapper._auto_map_fields(schema, columns),
            }
        return mappings

    @staticmethod
    def _auto_map_fields(schema: ImportSchema, columns: list[str]) -> dict[str, Any]:
        """
        Automatically map schema fields to workbook columns.

        Args:
            schema: Import schema definition
            columns: List of available column names

        Returns:
            Dictionary of field mappings with confidence scores
        """
        field_mappings: dict[str, Any] = {}
        for field in schema.fields:
            suggestions = SchemaMapper._rank_columns(field, columns)
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

    @staticmethod
    def _rank_columns(field: SchemaField, columns: list[str]) -> list[MappingCandidate]:
        """
        Rank columns by their likelihood of matching a field.

        Args:
            field: Schema field to match
            columns: Available column names

        Returns:
            List of mapping candidates sorted by confidence (descending)
        """
        candidates: list[MappingCandidate] = []
        normalized_aliases = {normalize_text(alias) for alias in field.all_keys}
        for column in columns:
            normalized_column = normalize_text(column)
            if not normalized_column:
                continue
            if normalized_column in normalized_aliases:
                candidates.append(MappingCandidate(column=column, confidence=1.0, reason="exact"))
                continue
            best_alias, score = SchemaMapper._best_alias_score(
                normalized_column, normalized_aliases
            )
            if score > 0.0:
                candidates.append(
                    MappingCandidate(column=column, confidence=score, reason=f"fuzzy:{best_alias}")
                )
        return sorted(candidates, key=lambda candidate: candidate.confidence, reverse=True)

    @staticmethod
    def _best_alias_score(column: str, aliases: set[str]) -> tuple[str, float]:
        """
        Find the best matching alias for a column using fuzzy matching.

        Args:
            column: Normalized column name
            aliases: Set of normalized field aliases

        Returns:
            Tuple of (best matching alias, confidence score)
        """
        best_alias = ""
        best_score = 0.0
        for alias in aliases:
            score = fuzz.token_set_ratio(column, alias) / 100
            if score > best_score:
                best_score = score
                best_alias = alias
        return best_alias, best_score

    @staticmethod
    def merge_mappings(
        current: Mapping[str, Any],
        incoming: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Merge incoming mapping updates with current mappings.

        Args:
            current: Current mapping configuration
            incoming: Incoming mapping updates

        Returns:
            Merged mapping configuration
        """
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
                        "required": (
                            existing.get("required")
                            if "required" in existing
                            else mapping.get("required", field_def.required if field_def else False)
                        ),
                        "data_type": existing.get("data_type")
                        or mapping.get("data_type")
                        or (field_def.data_type if field_def else "string"),
                        "column": mapping.get("column"),
                        "status": mapping.get("status", existing.get("status", "manual")),
                        "confidence": mapping.get("confidence", existing.get("confidence", 0.0)),
                        "suggestions": mapping.get("suggestions", existing.get("suggestions", [])),
                    }
        return merged


__all__ = ["MappingCandidate", "SchemaMapper"]
