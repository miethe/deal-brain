"""Declarative schema definitions for the importer mapping engine."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SchemaField:
    key: str
    label: str
    required: bool = False
    data_type: str = "string"
    description: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def all_keys(self) -> tuple[str, ...]:
        return (self.key, self.label, *self.aliases)


@dataclass(frozen=True)
class ImportSchema:
    entity: str
    label: str
    sheet_keywords: tuple[str, ...]
    fields: tuple[SchemaField, ...]

    def field_by_key(self, key: str) -> SchemaField | None:
        return next((field for field in self.fields if field.key == key), None)

    def required_fields(self) -> tuple[SchemaField, ...]:
        return tuple(field for field in self.fields if field.required)

    def optional_fields(self) -> tuple[SchemaField, ...]:
        return tuple(field for field in self.fields if not field.required)

    def score_columns(self, columns: Sequence[str]) -> float:
        """Return a confidence score that a sheet with these columns fits this schema."""
        if not columns:
            return 0.0
        matches = 0
        normalized_columns = {normalize_column(name) for name in columns if name}
        for field in self.fields:
            aliases = {normalize_column(alias) for alias in field.all_keys}
            if normalized_columns & aliases:
                matches += 1
        return matches / len(self.fields)

    def keyword_bonus(self, sheet_name: str) -> float:
        lowered = sheet_name.lower()
        for keyword in self.sheet_keywords:
            if keyword in lowered:
                return 0.15
        return 0.0


_COLUMN_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def normalize_column(value: str) -> str:
    return _COLUMN_NORMALIZE_RE.sub(" ", value.lower()).strip()


IMPORT_SCHEMAS: dict[str, ImportSchema] = {
    "cpu": ImportSchema(
        entity="cpu",
        label="CPUs",
        sheet_keywords=("cpu", "processor", "chip"),
        fields=(
            SchemaField("name", "CPU Name", required=True, aliases=("cpu", "processor", "name")),
            SchemaField("manufacturer", "Manufacturer", aliases=("maker", "brand")),
            SchemaField("socket", "Socket"),
            SchemaField("cores", "Cores", data_type="number"),
            SchemaField("threads", "Threads", data_type="number"),
            SchemaField("tdp_w", "TDP (W)", data_type="number", aliases=("tdp", "tdp w")),
            SchemaField("igpu_model", "Integrated GPU", aliases=("igpu", "graphics")),
            SchemaField("cpu_mark_multi", "CPU Mark (Multi)", data_type="number", aliases=("cpu mark", "multi score")),
            SchemaField("cpu_mark_single", "CPU Mark (Single)", data_type="number", aliases=("single thread", "single score")),
            SchemaField("release_year", "Release Year", data_type="number", aliases=("year",)),
            SchemaField("notes", "Notes", data_type="text"),
        ),
    ),
    "gpu": ImportSchema(
        entity="gpu",
        label="GPUs",
        sheet_keywords=("gpu", "graphics"),
        fields=(
            SchemaField("name", "GPU Name", required=True, aliases=("gpu", "graphics", "model")),
            SchemaField("manufacturer", "Manufacturer", aliases=("maker", "brand")),
            SchemaField("gpu_mark", "GPU Mark", data_type="number", aliases=("gpu score",)),
            SchemaField("metal_score", "Metal Score", data_type="number", aliases=("metal",)),
            SchemaField("notes", "Notes", data_type="text"),
        ),
    ),
    "valuation_rule": ImportSchema(
        entity="valuation_rule",
        label="Valuation Rules",
        sheet_keywords=("valuation", "reference", "rule"),
        fields=(
            SchemaField("name", "Rule Name", required=True, aliases=("reference", "rule")),
            SchemaField("component_type", "Component Type", required=True, aliases=("component", "type")),
            SchemaField("metric", "Metric", aliases=("pricing metric", "unit")),
            SchemaField("unit_value_usd", "Unit Value (USD)", required=True, data_type="number", aliases=("unit value", "unit cost")),
            SchemaField("condition_new", "Condition New", data_type="number", aliases=("multiplier new",)),
            SchemaField("condition_refurb", "Condition Refurb", data_type="number", aliases=("multiplier refurb", "condition refurb")),
            SchemaField("condition_used", "Condition Used", data_type="number", aliases=("multiplier used", "condition used")),
            SchemaField("notes", "Notes", data_type="text"),
        ),
    ),
    "ports_profile": ImportSchema(
        entity="ports_profile",
        label="Ports Profiles",
        sheet_keywords=("port", "connectivity"),
        fields=(
            SchemaField("name", "Profile Name", required=True, aliases=("profile", "name")),
            SchemaField("description", "Description", data_type="text"),
            SchemaField("ports", "Ports", data_type="text", aliases=("port breakdown", "port list")),
        ),
    ),
    "listing": ImportSchema(
        entity="listing",
        label="Listings",
        sheet_keywords=("listing", "device", "sff", "mac"),
        fields=(
            SchemaField("title", "Title", required=True, aliases=("device", "listing")),
            SchemaField("price_usd", "Price (USD)", required=True, data_type="number", aliases=("price", "cost")),
            SchemaField("condition", "Condition", aliases=("state",)),
            SchemaField("cpu_name", "CPU", aliases=("cpu", "processor")),
            SchemaField("gpu_name", "GPU", aliases=("gpu", "graphics")),
            SchemaField("ram_gb", "RAM (GB)", data_type="number", aliases=("memory", "ram")),
            SchemaField("primary_storage_gb", "Primary Storage (GB)", data_type="number", aliases=("storage", "storage 1")),
            SchemaField("primary_storage_type", "Primary Storage Type", aliases=("storage type", "storage 1 type")),
            SchemaField("secondary_storage_gb", "Secondary Storage (GB)", data_type="number", aliases=("storage 2", "secondary storage")),
            SchemaField("secondary_storage_type", "Secondary Storage Type", aliases=("storage 2 type",)),
            SchemaField("os_license", "OS License", aliases=("os", "operating system")),
            SchemaField("notes", "Notes", data_type="text"),
        ),
    ),
}


def iter_schemas() -> Iterable[ImportSchema]:
    return IMPORT_SCHEMAS.values()


__all__ = [
    "SchemaField",
    "ImportSchema",
    "IMPORT_SCHEMAS",
    "iter_schemas",
    "normalize_column",
]
