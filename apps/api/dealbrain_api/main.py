"""Entrypoint for running Deal Brain API locally."""

from __future__ import annotations

import uvicorn

from .app import create_app


APP_HOST = "0.0.0.0"
APP_PORT = 8000


def run() -> None:
    """Launch the FastAPI app with Uvicorn."""
    uvicorn.run(
        "dealbrain_api.main:get_app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        factory=True,
    )


def get_app():
    """Factory used by uvicorn to instantiate the app."""
    return create_app()


if __name__ == "__main__":  # pragma: no cover
    run()
