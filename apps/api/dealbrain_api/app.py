from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .api import router as api_router
from .settings import get_settings
from .telemetry import ObservabilityMiddleware, init_telemetry


def create_app() -> FastAPI:
    """Create and configure the FastAPI app instance."""
    settings = get_settings()
    init_telemetry(settings)
    app = FastAPI(title="Deal Brain API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ObservabilityMiddleware)

    # Instrument the app for Prometheus metrics
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    app.include_router(api_router)

    return app
