"""Validation utilities for valuation rules API"""

from typing import Any
from fastapi import HTTPException, status

# Valid entity keys for basic-managed groups
VALID_ENTITY_KEYS = {
    "Listing",
    "CPU",
    "GPU",
    "RamSpec",
    "StorageProfile",
    "PortsProfile"
}


def validate_basic_managed_group(
    group_metadata: dict[str, Any] | None,
    operation: str
) -> None:
    """Prevent manual edits to basic-managed groups.

    Args:
        group_metadata: The metadata_json from the group
        operation: The operation being attempted (e.g., 'update', 'delete')

    Raises:
        HTTPException: 403 Forbidden if group is basic-managed
    """
    if group_metadata and group_metadata.get("basic_managed"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot {operation} basic-managed rule groups. "
                   "These groups are automatically managed by the Basic mode interface."
        )


def validate_entity_key(entity_key: str | None) -> None:
    """Ensure entity key is from valid set.

    Args:
        entity_key: The entity key to validate

    Raises:
        HTTPException: 400 Bad Request if entity key is invalid
    """
    if entity_key is not None and entity_key not in VALID_ENTITY_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity_key: '{entity_key}'. "
                   f"Must be one of: {', '.join(sorted(VALID_ENTITY_KEYS))}"
        )


def validate_modifiers_json(
    modifiers: dict[str, Any] | None,
    action_type: str
) -> None:
    """Validate modifiers match action type.

    Args:
        modifiers: The modifiers dictionary from the action
        action_type: The action type (e.g., 'fixed_value', 'per_unit')

    Raises:
        HTTPException: 400 Bad Request if modifiers are invalid
    """
    if not modifiers:
        return

    # Validate clamp-related fields
    has_clamp = modifiers.get("clamp", False)
    has_min = "min_usd" in modifiers
    has_max = "max_usd" in modifiers

    if has_clamp and not (has_min or has_max):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="When 'clamp' is true, at least one of 'min_usd' or 'max_usd' must be specified"
        )

    if (has_min or has_max) and not has_clamp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'clamp' must be true when 'min_usd' or 'max_usd' are specified"
        )

    # Validate min/max values
    if has_min and has_max:
        min_val = modifiers.get("min_usd")
        max_val = modifiers.get("max_usd")
        if min_val is not None and max_val is not None and min_val > max_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'min_usd' ({min_val}) cannot be greater than 'max_usd' ({max_val})"
            )

    # Validate unit field
    valid_units = {"multiplier", "usd", "percentage", "formula"}
    unit = modifiers.get("unit")
    if unit and unit not in valid_units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid unit: '{unit}'. Must be one of: {', '.join(sorted(valid_units))}"
        )


def extract_metadata_fields(metadata: dict[str, Any] | None) -> tuple[bool | None, str | None]:
    """Extract basic_managed and entity_key from metadata.

    Args:
        metadata: The metadata dictionary

    Returns:
        Tuple of (basic_managed, entity_key)
    """
    if not metadata:
        return None, None

    basic_managed = metadata.get("basic_managed")
    entity_key = metadata.get("entity_key")

    return basic_managed, entity_key


def merge_metadata_fields(
    existing_metadata: dict[str, Any] | None,
    basic_managed: bool | None = None,
    entity_key: str | None = None,
    additional_metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Merge basic_managed and entity_key into metadata dictionary.

    Args:
        existing_metadata: Current metadata dictionary
        basic_managed: Basic managed flag to set
        entity_key: Entity key to set
        additional_metadata: Additional metadata to merge

    Returns:
        Merged metadata dictionary
    """
    metadata = dict(existing_metadata or {})

    # Merge additional metadata first
    if additional_metadata:
        metadata.update(additional_metadata)

    # Set basic_managed and entity_key if provided
    if basic_managed is not None:
        metadata["basic_managed"] = basic_managed
    if entity_key is not None:
        metadata["entity_key"] = entity_key

    return metadata