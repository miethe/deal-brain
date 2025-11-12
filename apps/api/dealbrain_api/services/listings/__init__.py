"""Listings service module.

This module provides comprehensive listing management functionality including:
- CRUD operations (create, update, delete)
- Valuation and pricing calculations
- Performance metrics computation
- Component management
- Cursor-based pagination
- URL ingestion integration

All functions are re-exported here for backward compatibility with existing imports.
"""

# Re-export all public functions for backward compatibility

# CRUD operations
from .crud import (
    MUTABLE_LISTING_FIELDS,
    bulk_update_listings,
    create_listing,
    delete_listing,
    get_default_profile,
    partial_update_listing,
    update_listing,
)

# Component management
from .components import (
    build_component_inputs,
    complete_partial_import,
    create_from_ingestion,
    sync_listing_components,
    upsert_from_url,
)

# Valuation and pricing
from .valuation import (
    VALUATION_DISABLED_RULESETS_KEY,
    apply_listing_metrics,
    storage_component_type,
    update_listing_overrides,
)

# Performance metrics
from .metrics import (
    bulk_update_listing_metrics,
    calculate_cpu_performance_metrics,
    update_listing_metrics,
)

# Pagination
from .pagination import (
    decode_cursor,
    encode_cursor,
    get_paginated_listings,
)

__all__ = [
    # Constants
    "MUTABLE_LISTING_FIELDS",
    "VALUATION_DISABLED_RULESETS_KEY",
    # CRUD
    "create_listing",
    "update_listing",
    "delete_listing",
    "partial_update_listing",
    "bulk_update_listings",
    "get_default_profile",
    # Components
    "sync_listing_components",
    "build_component_inputs",
    "complete_partial_import",
    "create_from_ingestion",
    "upsert_from_url",
    # Valuation
    "apply_listing_metrics",
    "storage_component_type",
    "update_listing_overrides",
    # Metrics
    "calculate_cpu_performance_metrics",
    "update_listing_metrics",
    "bulk_update_listing_metrics",
    # Pagination
    "encode_cursor",
    "decode_cursor",
    "get_paginated_listings",
]
