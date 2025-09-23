"""API router exports for Deal Brain."""

from fastapi import APIRouter

from . import catalog, listings, imports, rankings, dashboard, custom_fields

router = APIRouter()
router.include_router(catalog.router)
router.include_router(listings.router)
router.include_router(rankings.router)
router.include_router(dashboard.router)
router.include_router(imports.router)
router.include_router(custom_fields.router)

__all__ = ["router"]
