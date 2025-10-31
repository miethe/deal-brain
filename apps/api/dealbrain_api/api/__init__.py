"""API router exports for Deal Brain."""

from fastapi import APIRouter

from . import (
    admin,
    baseline,
    catalog,
    custom_fields,
    dashboard,
    entities,
    field_data,
    fields,
    health,
    imports,
    ingestion,
    listings,
    metrics,
    rankings,
    rules,
    settings,
    telemetry,
)

router = APIRouter()
router.include_router(admin.router)
router.include_router(baseline.router)
router.include_router(catalog.router)
router.include_router(listings.router)
router.include_router(rankings.router)
router.include_router(dashboard.router)
router.include_router(health.router)
router.include_router(imports.router)
router.include_router(ingestion.router)
router.include_router(fields.router)
router.include_router(custom_fields.router)
router.include_router(field_data.router)
router.include_router(metrics.router)
router.include_router(rules.router)
router.include_router(entities.router)
router.include_router(settings.router)
router.include_router(telemetry.router)

__all__ = ["router"]
