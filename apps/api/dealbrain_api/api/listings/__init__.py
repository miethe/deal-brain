"""
Listings API router aggregation.

This module aggregates all listings-related routers into a single router for backward compatibility.
The monolithic listings.py file was refactored into focused modules:
- crud.py: Basic CRUD operations and pagination
- schema.py: Field schema definitions
- valuation.py: Valuation breakdowns and overrides
- bulk_operations.py: Bulk updates and metric recalculation
- ports.py: Port management

All endpoints remain at their original paths under /v1/listings.
"""

from fastapi import APIRouter

from . import bulk_operations, crud, ports, schema, valuation

# Create main router with base prefix and tags
router = APIRouter(prefix="/v1/listings", tags=["listings"])

# Include all sub-routers
# Note: Order matters for route resolution - more specific routes should come first

# Schema endpoint (no prefix needed, already includes /schema)
router.include_router(schema.router)

# Bulk operations (includes /bulk-update, /bulk-recalculate-metrics)
router.include_router(bulk_operations.router)

# Ports endpoints (includes /{listing_id}/ports)
router.include_router(ports.router)

# Valuation endpoints (includes /{listing_id}/valuation-breakdown, /{listing_id}/valuation-overrides)
router.include_router(valuation.router)

# CRUD endpoints (includes /, /{listing_id}, etc.)
# This should be last as it includes the most generic routes
router.include_router(crud.router)

# Export the main router
__all__ = ["router"]
