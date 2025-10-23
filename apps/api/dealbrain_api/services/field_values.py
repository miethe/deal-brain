"""Service layer for field value autocomplete functionality."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from ..models.core import Cpu, Gpu, Listing

logger = logging.getLogger(__name__)


async def get_field_distinct_values(
    session: AsyncSession,
    field_name: str,
    limit: int = 100,
    search: str | None = None,
) -> list[str]:
    """
    Get distinct values for a given field across all entities.

    Args:
        session: Database session
        field_name: Field name in format "entity.field" (e.g., "listing.condition")
        limit: Maximum number of values to return
        search: Optional search filter

    Returns:
        List of distinct string values

    Raises:
        ValueError: If field_name format is invalid or field not found
    """
    try:
        # Parse field name
        parts = field_name.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid field name format: {field_name}. Expected 'entity.field'")

        entity_name, field_key = parts

        # Map entity names to models and columns
        entity_map = {
            "listing": (Listing, get_listing_column(field_key)),
            "cpu": (Cpu, get_cpu_column(field_key)),
            "gpu": (Gpu, get_gpu_column(field_key)),
        }

        if entity_name not in entity_map:
            raise ValueError(f"Unknown entity: {entity_name}")

        model, column = entity_map[entity_name]

        if column is None:
            raise ValueError(f"Unknown field: {field_key} for entity: {entity_name}")

        # Build query for distinct values
        query = select(distinct(column)).where(column.is_not(None))

        # Apply search filter if provided
        if search:
            # Cast column to string type for search
            from sqlalchemy import String, cast
            query = query.where(func.lower(cast(column, String)).contains(search.lower()))

        # Order and limit
        query = query.order_by(column).limit(limit)

        # Execute query
        result = await session.execute(query)
        values = [str(row[0]) for row in result.fetchall()]

        logger.info(f"Retrieved {len(values)} values for field {field_name}")
        return values

    except Exception as e:
        logger.error(f"Error getting field values for {field_name}: {e}", exc_info=True)
        raise


def get_listing_column(field_key: str) -> InstrumentedAttribute[Any] | None:
    """Map field key to Listing model column."""
    field_map = {
        "condition": Listing.condition,
        "form_factor": Listing.form_factor,
        "manufacturer": Listing.manufacturer,
        "series": Listing.series,
        "model_number": Listing.model_number,
        "listing_url": Listing.listing_url,
        "seller": Listing.seller,
        "device_model": Listing.device_model,
        "os_license": Listing.os_license,
        "status": Listing.status,
        "title": Listing.title,
        "primary_storage_type": Listing.primary_storage_type,
        "secondary_storage_type": Listing.secondary_storage_type,
    }
    return field_map.get(field_key)


def get_cpu_column(field_key: str) -> InstrumentedAttribute[Any] | None:
    """Map field key to CPU model column."""
    field_map = {
        "manufacturer": Cpu.manufacturer,
        "socket": Cpu.socket,
        "name": Cpu.name,
        "igpu_model": Cpu.igpu_model,
        "passmark_category": Cpu.passmark_category,
    }
    return field_map.get(field_key)


def get_gpu_column(field_key: str) -> InstrumentedAttribute[Any] | None:
    """Map field key to GPU model column."""
    field_map = {
        "manufacturer": Gpu.manufacturer,
        "name": Gpu.name,
    }
    return field_map.get(field_key)


__all__ = ["get_field_distinct_values"]
