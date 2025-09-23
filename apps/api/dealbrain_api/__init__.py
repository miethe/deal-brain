"""Deal Brain FastAPI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI

__all__ = ["create_app"]


def create_app() -> "FastAPI":
    """Factory wrapper that defers heavy imports until needed."""
    from .app import create_app as _create_app

    return _create_app()
