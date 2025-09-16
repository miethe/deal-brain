"""API router exports for Deal Brain."""

from fastapi import APIRouter

from . import catalog, listings, imports, rankings, dashboard

router = APIRouter()
router.include_router(catalog.router)
router.include_router(listings.router)
router.include_router(rankings.router)
router.include_router(dashboard.router)
router.include_router(imports.router)

__all__ = ["router"]
