"""API router exports for Deal Brain."""

from fastapi import APIRouter

from . import catalog, custom_fields, dashboard, field_data, fields, imports, listings, rankings

router = APIRouter()
router.include_router(catalog.router)
router.include_router(listings.router)
router.include_router(rankings.router)
router.include_router(dashboard.router)
router.include_router(imports.router)
router.include_router(fields.router)
router.include_router(custom_fields.router)
router.include_router(field_data.router)

__all__ = ["router"]
