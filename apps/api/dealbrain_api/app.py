from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .api import router as api_router
from .settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI app instance."""
    settings = get_settings()
    app = FastAPI(title="Deal Brain API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    app.include_router(api_router)

    instrumentator = Instrumentator()

    @app.on_event("startup")
    async def _startup() -> None:
        instrumentator.instrument(app).expose(app)

    return app

