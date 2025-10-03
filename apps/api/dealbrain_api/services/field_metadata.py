"""Service for providing entity and field metadata to frontend."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .field_registry import FieldRegistry


@dataclass
class OperatorDefinition:
    """Operator metadata for frontend."""
    value: str
    label: str
    field_types: list[str]  # Applicable data types


@dataclass
class FieldMetadata:
    """Field metadata for condition builder."""
    key: str
    label: str
    data_type: str
    description: str | None = None
    options: list[str] | None = None  # For enum/dropdown fields
    validation: dict[str, Any] | None = None
    is_custom: bool = False


@dataclass
class EntityMetadata:
    """Entity metadata for condition builder."""
    key: str
    label: str
    fields: list[FieldMetadata]


class FieldMetadataService:
    """Provides structured metadata for rule builder UI."""

    OPERATORS = [
        OperatorDefinition("equals", "Equals", ["string", "number", "enum", "boolean"]),
        OperatorDefinition("not_equals", "Not Equals", ["string", "number", "enum", "boolean"]),
        OperatorDefinition("greater_than", "Greater Than", ["number", "date"]),
        OperatorDefinition("less_than", "Less Than", ["number", "date"]),
        OperatorDefinition("gte", "Greater Than or Equal", ["number", "date"]),
        OperatorDefinition("lte", "Less Than or Equal", ["number", "date"]),
        OperatorDefinition("contains", "Contains", ["string"]),
        OperatorDefinition("starts_with", "Starts With", ["string"]),
        OperatorDefinition("ends_with", "Ends With", ["string"]),
        OperatorDefinition("in", "In", ["string", "enum", "number"]),
        OperatorDefinition("not_in", "Not In", ["string", "enum", "number"]),
        OperatorDefinition("between", "Between", ["number", "date"]),
    ]

    def __init__(self, field_registry: FieldRegistry | None = None):
        self.field_registry = field_registry or FieldRegistry()

    async def get_entities_metadata(self, db: AsyncSession) -> list[EntityMetadata]:
        """Fetch all entities with their fields."""
        entities = []

        # Listing entity
        listing_schema = await self.field_registry.schema_for(db, "listing")
        listing_fields = [
            FieldMetadata(
                key=f["key"],
                label=f["label"],
                data_type=f["data_type"],
                description=f.get("description"),
                options=f.get("options"),
                is_custom=f.get("origin") == "custom",
            )
            for f in listing_schema["fields"]
        ]
        entities.append(EntityMetadata(key="listing", label="Listing", fields=listing_fields))

        # CPU entity (nested under listing.cpu)
        entities.append(
            EntityMetadata(
                key="cpu",
                label="CPU",
                fields=[
                    FieldMetadata("cpu_mark_multi", "CPU Mark (Multi-Core)", "number",
                                  description="PassMark multi-core benchmark score"),
                    FieldMetadata("cpu_mark_single", "CPU Mark (Single-Core)", "number",
                                  description="PassMark single-core benchmark score"),
                    FieldMetadata("name", "CPU Name", "string"),
                    FieldMetadata("manufacturer", "Manufacturer", "enum", options=["Intel", "AMD"]),
                    FieldMetadata("cores", "Cores", "number"),
                    FieldMetadata("threads", "Threads", "number"),
                    FieldMetadata("tdp_w", "TDP (Watts)", "number", description="Thermal Design Power"),
                ],
            )
        )

        # GPU entity
        entities.append(
            EntityMetadata(
                key="gpu",
                label="GPU",
                fields=[
                    FieldMetadata("gpu_mark", "GPU Mark", "number", description="PassMark GPU benchmark score"),
                    FieldMetadata("metal_score", "Metal Score", "number", description="Metal benchmark score"),
                    FieldMetadata("name", "GPU Name", "string"),
                    FieldMetadata("manufacturer", "Manufacturer", "enum", options=["NVIDIA", "AMD", "Intel"]),
                ],
            )
        )

        return entities

    def get_operators_for_field_type(self, field_type: str) -> list[OperatorDefinition]:
        """Get valid operators for a given field type."""
        return [op for op in self.OPERATORS if field_type in op.field_types]


__all__ = ["FieldMetadataService", "FieldMetadata", "EntityMetadata", "OperatorDefinition"]
