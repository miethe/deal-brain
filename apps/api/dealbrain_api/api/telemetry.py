"""Endpoints for receiving frontend telemetry events."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from ..settings import get_settings
from ..telemetry import get_logger

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class TelemetryLogEntry(BaseModel):
    """Payload for frontend telemetry submissions."""

    level: Literal["debug", "info", "warn", "error"] = Field(default="info")
    event: str = Field(..., description="Event identifier, e.g. frontend.import.success")
    payload: dict[str, Any] | None = Field(default=None, description="Structured payload data")
    session_id: str | None = Field(default=None, description="Client session identifier")
    user: dict[str, Any] | None = Field(default=None, description="Optional user context")
    timestamp: datetime | None = Field(default=None, description="Client timestamp")


@router.post("/logs", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry_log(
    entry: TelemetryLogEntry,
    request: Request,
) -> dict[str, bool]:
    """Accept telemetry events from the frontend and emit to backend logger."""
    logger = get_logger("dealbrain.frontend")
    client = request.client.host if request.client else None
    settings = get_settings()

    log_kwargs = {
        "event": entry.event,
        "session_id": entry.session_id,
        "client": client,
        "environment": settings.environment,
        "payload": entry.payload,
        "user": entry.user,
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
    }

    if entry.level == "error":
        logger.error("frontend.event", **log_kwargs)
    elif entry.level == "warn":
        logger.warning("frontend.event", **log_kwargs)
    elif entry.level == "debug":
        logger.debug("frontend.event", **log_kwargs)
    else:
        logger.info("frontend.event", **log_kwargs)

    return {"accepted": True}


__all__ = ["router"]
