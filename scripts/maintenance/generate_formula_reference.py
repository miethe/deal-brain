#!/usr/bin/env python3
"""
Generate comprehensive JSON schema documenting all entities, fields, and operations
available for use in baseline rule formulas.

This reference serves as:
1. AI Guidance: Token-efficient documentation for AI systems generating baseline rules
2. User Documentation: Clear reference for users creating custom formulas
3. Import Validation: Exact field paths and types as they should appear in imported JSON

Usage:
    poetry run python scripts/generate_formula_reference.py

Output:
    data/formula_reference.json
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.models.core import (
    Cpu,
    CustomFieldDefinition,
    Gpu,
    Listing,
    Port,
    PortsProfile,
    RamSpec,
    StorageProfile,
)
from dealbrain_core.enums import (
    Condition,
    ListingStatus,
    RamGeneration,
    StorageMedium,
)
from dealbrain_core.rules.formula import FormulaParser

logger = logging.getLogger(__name__)


def get_python_type_name(column_type: Any) -> str:
    """Convert SQLAlchemy column type to Python type name."""
    type_str = str(column_type)

    # Handle common SQLAlchemy types
    if "INTEGER" in type_str or "BIGINT" in type_str:
        return "integer"
    elif "FLOAT" in type_str or "NUMERIC" in type_str or "DECIMAL" in type_str:
        return "float"
    elif "VARCHAR" in type_str or "TEXT" in type_str or "CHAR" in type_str:
        return "string"
    elif "BOOLEAN" in type_str or "BOOL" in type_str:
        return "boolean"
    elif "TIMESTAMP" in type_str or "DATETIME" in type_str or "DATE" in type_str:
        return "datetime"
    elif "JSON" in type_str:
        return "json"
    elif "ARRAY" in type_str:
        return "array"
    elif "UUID" in type_str:
        return "uuid"
    else:
        return "unknown"


def extract_model_fields(model_class: Any, entity_name: str, access_pattern_prefix: str = None) -> dict[str, Any]:
    """
    Extract all fields from a SQLAlchemy model using inspection.

    Args:
        model_class: SQLAlchemy model class
        entity_name: Human-readable entity name
        access_pattern_prefix: Prefix for field access (e.g., "cpu" for cpu.cores)

    Returns:
        Dictionary with field metadata
    """
    inspector = inspect(model_class)
    fields = {}

    for column in inspector.columns:
        # Skip internal/audit fields
        if column.name in ("id", "created_at", "updated_at", "deleted_at"):
            continue

        # Determine field type
        field_type = get_python_type_name(column.type)

        # Handle enums specially
        is_enum = False
        enum_type = None
        enum_values = None

        if hasattr(column.type, 'enum_class'):
            is_enum = True
            enum_class = column.type.enum_class
            enum_type = enum_class.__name__
            enum_values = [e.value for e in enum_class]
            field_type = "enum"

        # Build access pattern
        if access_pattern_prefix:
            example = f"{access_pattern_prefix}.{column.name}"
        else:
            example = f"{entity_name}.{column.name}"

        # Build field metadata
        field_info = {
            "type": field_type,
            "nullable": column.nullable,
            "example": example,
        }

        # Add description based on field name
        field_info["description"] = generate_field_description(column.name, entity_name)

        # Add enum info if applicable
        if is_enum:
            field_info["enum_type"] = enum_type
            field_info["values"] = enum_values

        # Add default value if present
        if column.default is not None and hasattr(column.default, 'arg'):
            default_val = column.default.arg
            if callable(default_val):
                # Skip callable defaults
                pass
            else:
                field_info["default"] = default_val

        fields[column.name] = field_info

    return fields


def generate_field_description(field_name: str, entity_name: str) -> str:
    """Generate human-readable description for a field based on its name."""
    descriptions = {
        # Listing fields
        "title": "Listing title or name",
        "listing_url": "URL to original listing",
        "seller": "Seller name or identifier",
        "price_usd": "Listing price in USD",
        "price_date": "Date when price was recorded",
        "condition": "Item condition (new, refurb, used)",
        "status": "Listing status (active, archived, pending)",
        "device_model": "Device model name or identifier",
        "ram_gb": "Total RAM capacity in gigabytes",
        "ram_notes": "Additional RAM notes or details",
        "primary_storage_gb": "Primary storage capacity in gigabytes",
        "primary_storage_type": "Primary storage type description",
        "secondary_storage_gb": "Secondary storage capacity in gigabytes",
        "secondary_storage_type": "Secondary storage type description",
        "os_license": "Operating system license information",
        "notes": "Additional notes or comments",
        "adjusted_price_usd": "Price adjusted based on valuation rules",
        "score_cpu_multi": "CPU multi-thread performance score",
        "score_cpu_single": "CPU single-thread performance score",
        "score_gpu": "GPU performance score",
        "score_composite": "Composite performance score",
        "dollar_per_cpu_mark": "Price per CPU benchmark point",
        "dollar_per_single_mark": "Price per single-thread benchmark point",
        "dollar_per_cpu_mark_single": "Price per single-thread CPU mark (base)",
        "dollar_per_cpu_mark_single_adjusted": "Price per single-thread CPU mark (adjusted)",
        "dollar_per_cpu_mark_multi": "Price per multi-thread CPU mark (base)",
        "dollar_per_cpu_mark_multi_adjusted": "Price per multi-thread CPU mark (adjusted)",
        "perf_per_watt": "Performance per watt efficiency metric",
        "manufacturer": "Product manufacturer",
        "series": "Product series or line",
        "model_number": "Product model number",
        "form_factor": "Physical form factor (SFF, mini-ITX, etc.)",

        # CPU fields
        "name": f"{entity_name.upper()} model name",
        "socket": "CPU socket type",
        "cores": "Number of physical cores",
        "threads": "Number of logical threads",
        "tdp_w": "Thermal design power in watts",
        "igpu_model": "Integrated GPU model name",
        "cpu_mark_multi": "PassMark multi-thread benchmark score",
        "cpu_mark_single": "PassMark single-thread benchmark score",
        "igpu_mark": "PassMark integrated GPU benchmark score",
        "release_year": "Year of release",
        "passmark_slug": "PassMark URL slug identifier",
        "passmark_category": "PassMark category classification",
        "passmark_id": "PassMark ID",

        # GPU fields
        "gpu_mark": "PassMark GPU benchmark score",
        "metal_score": "Metal API benchmark score",

        # RAM Spec fields
        "label": f"{entity_name} label or identifier",
        "ddr_generation": "DDR generation (DDR3, DDR4, DDR5, etc.)",
        "speed_mhz": "Memory speed in MHz",
        "module_count": "Number of RAM modules",
        "capacity_per_module_gb": "Capacity per module in GB",
        "total_capacity_gb": "Total RAM capacity in GB",

        # Storage Profile fields
        "medium": "Storage medium type (NVME, SATA_SSD, HDD, etc.)",
        "interface": "Storage interface (SATA, NVMe, etc.)",
        "form_factor": "Storage form factor (M.2, 2.5\", etc.)",
        "capacity_gb": "Storage capacity in gigabytes",
        "performance_tier": "Performance tier classification",

        # Ports Profile fields
        "description": f"{entity_name} description",

        # Port fields
        "type": "Port type (USB-A, USB-C, HDMI, etc.)",
        "count": "Number of ports of this type",
        "spec_notes": "Additional port specifications or notes",
    }

    return descriptions.get(field_name, f"{field_name.replace('_', ' ').title()}")


async def get_custom_fields(session: AsyncSession) -> dict[str, list[dict[str, Any]]]:
    """Query database for all custom field definitions grouped by entity."""
    from sqlalchemy import select

    result = await session.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.is_active == True)
        .where(CustomFieldDefinition.deleted_at.is_(None))
        .order_by(CustomFieldDefinition.entity, CustomFieldDefinition.display_order)
    )

    custom_fields_by_entity = {}

    for field in result.scalars():
        entity = field.entity
        if entity not in custom_fields_by_entity:
            custom_fields_by_entity[entity] = []

        field_info = {
            "field_key": field.key,
            "field_type": field.data_type,
            "description": field.description or f"Custom {field.label}",
            "access_pattern": f"{entity}.custom_fields.{field.key}",
            "required": field.required,
        }

        if field.options:
            field_info["options"] = field.options

        if field.default_value is not None:
            field_info["default_value"] = field.default_value

        custom_fields_by_entity[entity].append(field_info)

    return custom_fields_by_entity


def generate_operators_reference() -> dict[str, Any]:
    """Generate reference for all supported operators."""
    return {
        "arithmetic": {
            "+": "Addition",
            "-": "Subtraction",
            "*": "Multiplication",
            "/": "Division (returns float)",
            "//": "Floor division (returns integer)",
            "%": "Modulo (remainder after division)",
            "**": "Exponentiation (power)",
        },
        "comparison": {
            "==": "Equal to",
            "!=": "Not equal to",
            "<": "Less than",
            "<=": "Less than or equal to",
            ">": "Greater than",
            ">=": "Greater than or equal to",
        },
        "logical": {
            "and": "Logical AND (both conditions must be true)",
            "or": "Logical OR (at least one condition must be true)",
            "not": "Logical NOT (negates boolean value)",
        },
    }


def generate_functions_reference() -> dict[str, Any]:
    """Generate reference for all supported functions."""
    parser = FormulaParser()

    functions = {}

    for func_name in parser.ALLOWED_FUNCTIONS.keys():
        if func_name == "abs":
            functions[func_name] = {
                "signature": "abs(value)",
                "description": "Returns the absolute value of a number",
                "example": "abs(cpu.tdp_w - 65)",
                "returns": "float",
            }
        elif func_name == "min":
            functions[func_name] = {
                "signature": "min(a, b, ...)",
                "description": "Returns the smallest of the input values",
                "example": "min(ram_gb, 32)",
                "returns": "float",
            }
        elif func_name == "max":
            functions[func_name] = {
                "signature": "max(a, b, ...)",
                "description": "Returns the largest of the input values",
                "example": "max(cpu.cores, 4)",
                "returns": "float",
            }
        elif func_name == "round":
            functions[func_name] = {
                "signature": "round(value, ndigits=0)",
                "description": "Rounds a number to n decimal places",
                "example": "round(price_usd * 0.15, 2)",
                "returns": "float",
            }
        elif func_name == "int":
            functions[func_name] = {
                "signature": "int(value)",
                "description": "Converts value to integer (truncates decimals)",
                "example": "int(ram_gb / 8)",
                "returns": "integer",
            }
        elif func_name == "float":
            functions[func_name] = {
                "signature": "float(value)",
                "description": "Converts value to floating-point number",
                "example": "float(cpu.cores)",
                "returns": "float",
            }
        elif func_name == "sum":
            functions[func_name] = {
                "signature": "sum(iterable)",
                "description": "Returns sum of all values in an iterable",
                "example": "sum([ram_gb, primary_storage_gb, secondary_storage_gb])",
                "returns": "float",
            }
        elif func_name == "sqrt":
            functions[func_name] = {
                "signature": "sqrt(value)",
                "description": "Returns square root of a number",
                "example": "sqrt(cpu.cpu_mark_multi)",
                "returns": "float",
            }
        elif func_name == "pow":
            functions[func_name] = {
                "signature": "pow(base, exponent)",
                "description": "Returns base raised to the power of exponent",
                "example": "pow(ram_gb, 1.2)",
                "returns": "float",
            }
        elif func_name == "floor":
            functions[func_name] = {
                "signature": "floor(value)",
                "description": "Rounds down to nearest integer",
                "example": "floor(price_usd / 100)",
                "returns": "integer",
            }
        elif func_name == "ceil":
            functions[func_name] = {
                "signature": "ceil(value)",
                "description": "Rounds up to nearest integer",
                "example": "ceil(ram_gb / 8)",
                "returns": "integer",
            }
        elif func_name == "clamp":
            functions[func_name] = {
                "signature": "clamp(value, min_val, max_val)",
                "description": "Constrains value between min and max (inclusive)",
                "example": "clamp(gpu.gpu_mark / 1000, 0, 500)",
                "returns": "float",
            }

    return functions


def generate_syntax_patterns() -> dict[str, Any]:
    """Generate reference for syntax patterns."""
    return {
        "ternary": {
            "syntax": "value_if_true if condition else value_if_false",
            "description": "Conditional expression that returns one value or another based on condition",
            "examples": [
                "50 if cpu.tdp_w > 120 else 0",
                "price_usd * 0.1 if condition == 'new' else 0",
                "ram_gb * 3.0 if ram_spec.ddr_generation == 'ddr5' else ram_gb * 2.5",
            ],
        },
        "field_access": {
            "syntax": "entity.field_name",
            "description": "Access field from a related entity using dot notation",
            "examples": [
                "cpu.cpu_mark_multi",
                "ram_spec.ddr_generation",
                "listing.price_usd",
                "gpu.gpu_mark",
            ],
        },
        "nested_field_access": {
            "syntax": "entity.custom_fields.field_key",
            "description": "Access custom field value from an entity",
            "examples": [
                "listing.custom_fields.warranty_months",
                "cpu.custom_fields.efficiency_rating",
            ],
        },
        "arithmetic": {
            "syntax": "operand operator operand",
            "description": "Standard mathematical operations",
            "examples": [
                "ram_gb * 2.5",
                "cpu.cpu_mark_multi / 1000",
                "price_usd - 100",
                "(ram_gb + primary_storage_gb) * 1.5",
            ],
        },
        "comparison": {
            "syntax": "value operator value",
            "description": "Compare two values, returns boolean",
            "examples": [
                "ram_gb >= 16",
                "cpu.tdp_w < 65",
                "condition == 'new'",
                "ram_spec.ddr_generation != 'ddr3'",
            ],
        },
        "function_call": {
            "syntax": "function_name(arg1, arg2, ...)",
            "description": "Call a built-in function with arguments",
            "examples": [
                "max(ram_gb, 8)",
                "round(price_usd * 0.15, 2)",
                "clamp(gpu.gpu_mark / 1000, 0, 500)",
            ],
        },
    }


def generate_examples() -> dict[str, Any]:
    """Generate example formulas with explanations."""
    return {
        "basic_ram_valuation": {
            "formula": "ram_gb * 2.5",
            "description": "Value RAM at $2.50 per gigabyte",
            "use_case": "Simple per-unit pricing",
        },
        "cpu_performance_valuation": {
            "formula": "(cpu.cpu_mark_multi / 1000) * 8.0",
            "description": "Value CPU based on multi-thread PassMark score",
            "use_case": "Performance-based pricing",
        },
        "conditional_ram_pricing": {
            "formula": "ram_gb * 3.0 if ram_gb >= 16 else ram_gb * 2.5",
            "description": "Higher per-GB price for 16GB+ configurations",
            "use_case": "Tiered pricing",
        },
        "tdp_penalty": {
            "formula": "50 if cpu.tdp_w > 120 else 0",
            "description": "Apply $50 penalty for high-TDP CPUs (over 120W)",
            "use_case": "Conditional penalties",
        },
        "clamped_gpu_value": {
            "formula": "clamp((gpu.gpu_mark / 1000) * 8.0, 0, 500)",
            "description": "GPU valuation with minimum $0 and maximum $500 cap",
            "use_case": "Bounded valuation",
        },
        "ddr_generation_bonus": {
            "formula": "10 if ram_spec.ddr_generation == 'ddr5' else 0",
            "description": "Add $10 bonus for DDR5 RAM",
            "use_case": "Feature-based bonuses",
        },
        "combined_storage_value": {
            "formula": "(primary_storage_gb / 128) * 25 + (secondary_storage_gb / 1024) * 20",
            "description": "Value primary storage at $25 per 128GB, secondary at $20 per 1TB",
            "use_case": "Multi-component valuation",
        },
        "efficiency_based_pricing": {
            "formula": "round((cpu.cpu_mark_multi / max(cpu.tdp_w, 1)) * 2.0, 2)",
            "description": "Value CPU based on performance-per-watt efficiency",
            "use_case": "Efficiency metrics",
        },
        "condition_multiplier": {
            "formula": "(ram_gb * 2.5) * (1.0 if condition == 'new' else 0.85 if condition == 'refurb' else 0.7)",
            "description": "Apply condition-based multiplier to base RAM value",
            "use_case": "Nested conditionals",
        },
        "null_safe_cpu_value": {
            "formula": "(cpu.cpu_mark_multi or 0) / 1000 * 5.0",
            "description": "Handle missing CPU benchmark score gracefully",
            "use_case": "Null handling",
        },
    }


def generate_enum_reference() -> dict[str, Any]:
    """Generate reference for all enum types."""
    return {
        "Condition": {
            "description": "Listing item condition",
            "values": [e.value for e in Condition],
            "usage": "Used in listing.condition field",
        },
        "RamGeneration": {
            "description": "DDR generation for RAM",
            "values": [e.value for e in RamGeneration],
            "usage": "Used in ram_spec.ddr_generation field",
        },
        "StorageMedium": {
            "description": "Storage medium type",
            "values": [e.value for e in StorageMedium],
            "usage": "Used in primary_storage.medium and secondary_storage.medium fields",
        },
        "ListingStatus": {
            "description": "Listing lifecycle status",
            "values": [e.value for e in ListingStatus],
            "usage": "Used in listing.status field",
        },
    }


async def generate_formula_reference() -> dict[str, Any]:
    """Generate complete formula reference schema."""
    async with session_scope() as session:
        # Extract custom fields from database
        custom_fields = await get_custom_fields(session)

    # Build entities reference
    entities = {
        "listing": {
            "description": "Primary listing entity (root context)",
            "access_pattern": "Direct field access (e.g., listing.price_usd or just price_usd)",
            "nullable": False,
            "fields": extract_model_fields(Listing, "listing", "listing"),
        },
        "cpu": {
            "description": "CPU entity (foreign key relationship from listing)",
            "access_pattern": "cpu.field_name",
            "nullable": True,
            "note": "All CPU fields are nullable since listing may not have a CPU",
            "fields": extract_model_fields(Cpu, "cpu", "cpu"),
        },
        "gpu": {
            "description": "GPU entity (foreign key relationship from listing)",
            "access_pattern": "gpu.field_name",
            "nullable": True,
            "note": "All GPU fields are nullable since listing may not have a GPU",
            "fields": extract_model_fields(Gpu, "gpu", "gpu"),
        },
        "ram_spec": {
            "description": "RAM specification entity (foreign key relationship from listing)",
            "access_pattern": "ram_spec.field_name",
            "nullable": True,
            "note": "Detailed RAM specifications beyond simple capacity",
            "fields": extract_model_fields(RamSpec, "ram_spec", "ram_spec"),
        },
        "primary_storage": {
            "description": "Primary storage profile (foreign key relationship from listing)",
            "access_pattern": "primary_storage.field_name",
            "nullable": True,
            "note": "Detailed specifications for primary storage device",
            "fields": extract_model_fields(StorageProfile, "storage", "primary_storage"),
        },
        "secondary_storage": {
            "description": "Secondary storage profile (foreign key relationship from listing)",
            "access_pattern": "secondary_storage.field_name",
            "nullable": True,
            "note": "Detailed specifications for secondary storage device (if present)",
            "fields": extract_model_fields(StorageProfile, "storage", "secondary_storage"),
        },
        "ports_profile": {
            "description": "Connectivity ports profile (foreign key relationship from listing)",
            "access_pattern": "ports_profile.field_name",
            "nullable": True,
            "note": "Collection of connectivity ports and specifications",
            "fields": extract_model_fields(PortsProfile, "ports_profile", "ports_profile"),
        },
    }

    # Build complete reference
    reference = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": (
            "Comprehensive formula reference for baseline rule creation. "
            "This document describes all available entities, fields, operators, "
            "functions, and syntax patterns for writing valuation formulas."
        ),
        "entities": entities,
        "custom_fields": custom_fields,
        "enums": generate_enum_reference(),
        "operators": generate_operators_reference(),
        "functions": generate_functions_reference(),
        "syntax_patterns": generate_syntax_patterns(),
        "examples": generate_examples(),
        "notes": {
            "null_safety": (
                "When accessing nullable fields (especially from foreign key relationships), "
                "use the 'or' operator to provide default values: (cpu.cpu_mark_multi or 0)"
            ),
            "field_access": (
                "Listing fields can be accessed directly (price_usd) or with prefix (listing.price_usd). "
                "Related entity fields must use dot notation (cpu.cores, ram_spec.ddr_generation)."
            ),
            "type_coercion": (
                "The formula engine automatically coerces results to float. "
                "Use int() or round() functions for integer results."
            ),
            "operator_precedence": (
                "Standard Python operator precedence applies: "
                "** (power) > *,/,//,% (multiply/divide) > +,- (add/subtract) > comparisons > and/or. "
                "Use parentheses to control evaluation order."
            ),
        },
    }

    return reference


async def main():
    """Main execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Generating formula reference schema...")

    try:
        # Generate reference
        reference = await generate_formula_reference()

        # Ensure output directory exists
        output_dir = Path(__file__).parent.parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write to file
        output_path = output_dir / "formula_reference.json"
        with open(output_path, "w") as f:
            json.dump(reference, f, indent=2, sort_keys=True)

        logger.info(f"Formula reference generated successfully: {output_path}")

        # Print summary
        entity_count = len(reference["entities"])
        total_fields = sum(len(entity["fields"]) for entity in reference["entities"].values())
        custom_field_count = sum(len(fields) for fields in reference["custom_fields"].values())
        function_count = len(reference["functions"])
        example_count = len(reference["examples"])

        print("\n" + "=" * 60)
        print("FORMULA REFERENCE GENERATION SUMMARY")
        print("=" * 60)
        print(f"Output: {output_path}")
        print(f"Version: {reference['version']}")
        print(f"Generated: {reference['generated_at']}")
        print()
        print(f"Entities: {entity_count}")
        print(f"Standard Fields: {total_fields}")
        print(f"Custom Fields: {custom_field_count}")
        print(f"Functions: {function_count}")
        print(f"Examples: {example_count}")
        print(f"Enums: {len(reference['enums'])}")
        print(f"Operators: {sum(len(ops) for ops in reference['operators'].values())}")
        print()
        print("Entities included:")
        for entity_name, entity_data in reference["entities"].items():
            field_count = len(entity_data["fields"])
            nullable = "nullable" if entity_data.get("nullable") else "required"
            print(f"  - {entity_name}: {field_count} fields ({nullable})")
        print()
        print("Custom fields by entity:")
        if reference["custom_fields"]:
            for entity, fields in reference["custom_fields"].items():
                print(f"  - {entity}: {len(fields)} custom fields")
        else:
            print("  - No custom fields defined")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Failed to generate formula reference: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
