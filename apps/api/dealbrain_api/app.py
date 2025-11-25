import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .api import router as api_router
from .settings import get_settings
from .telemetry import ObservabilityMiddleware, init_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    Handles:
    - Startup: No specific actions (browser pool lazy-initialized on first use)
    - Shutdown: Close browser pool to release resources gracefully
    """
    # Startup
    logger.info("FastAPI application starting up...")
    yield
    # Shutdown
    logger.info("FastAPI application shutting down...")
    try:
        from .adapters.browser_pool import BrowserPool

        # Close browser pool if it exists
        pool = BrowserPool._instance
        if pool is not None and pool._initialized:
            logger.info("Closing browser pool...")
            await pool.close_all()
            logger.info("Browser pool closed successfully")
        else:
            logger.info("No browser pool to close")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


def create_app() -> FastAPI:
    """Create and configure the FastAPI app instance."""
    settings = get_settings()
    init_telemetry(settings)
    app = FastAPI(
        title="Deal Brain API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

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
