"""
Server-Sent Events (SSE) infrastructure for real-time updates.

This module provides event types, schemas, and utilities for streaming real-time
updates to connected clients via SSE.

Architecture:
- Event producers publish events to Redis pub/sub channel 'dealbrain:events'
- SSE endpoint subscribes to channel and streams to connected clients
- Clients receive events and invalidate caches/update UI

Event Flow:
1. Service layer calls publish_event() after creating/updating/deleting entities
2. Event published to Redis channel 'dealbrain:events'
3. SSE endpoint receives event and streams to all connected clients
4. Frontend EventSource listeners receive events and trigger handlers
5. React Query invalidates caches, UI updates automatically

Supported Events:
- listing.created: New listing created
- listing.updated: Listing fields updated
- listing.deleted: Listing deleted
- valuation.recalculated: Listing valuations recalculated
- import.completed: Import job completed
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from redis import asyncio as aioredis

from ..cache import cache_manager
from ..telemetry import get_logger

logger = get_logger("dealbrain.events")


class EventType(str, Enum):
    """SSE event types for real-time updates."""

    LISTING_CREATED = "listing.created"
    LISTING_UPDATED = "listing.updated"
    LISTING_DELETED = "listing.deleted"
    VALUATION_RECALCULATED = "valuation.recalculated"
    IMPORT_COMPLETED = "import.completed"


class ListingCreatedData(BaseModel):
    """Data payload for listing.created event."""

    listing_id: int = Field(..., description="ID of created listing")
    timestamp: str = Field(..., description="ISO 8601 timestamp of event")


class ListingUpdatedData(BaseModel):
    """Data payload for listing.updated event."""

    listing_id: int = Field(..., description="ID of updated listing")
    changes: list[str] = Field(default_factory=list, description="List of field names that changed")
    timestamp: str = Field(..., description="ISO 8601 timestamp of event")


class ListingDeletedData(BaseModel):
    """Data payload for listing.deleted event."""

    listing_id: int = Field(..., description="ID of deleted listing")
    timestamp: str = Field(..., description="ISO 8601 timestamp of event")


class ValuationRecalculatedData(BaseModel):
    """Data payload for valuation.recalculated event."""

    listing_ids: list[int] = Field(..., description="IDs of recalculated listings")
    timestamp: str = Field(..., description="ISO 8601 timestamp of event")


class ImportCompletedData(BaseModel):
    """Data payload for import.completed event."""

    import_job_id: int = Field(..., description="ID of completed import job")
    listings_created: int = Field(..., description="Number of listings created")
    listings_updated: int = Field(..., description="Number of listings updated")
    timestamp: str = Field(..., description="ISO 8601 timestamp of event")


class Event(BaseModel):
    """Base event structure for SSE."""

    type: EventType = Field(..., description="Event type identifier")
    data: dict[str, Any] = Field(..., description="Event payload data")


# Redis pub/sub channel for events
EVENTS_CHANNEL = "dealbrain:events"


async def publish_event(event_type: EventType, data: dict[str, Any]) -> None:
    """
    Publish event to Redis pub/sub channel.

    Events are published to 'dealbrain:events' channel and consumed by SSE endpoint.

    Args:
        event_type: Type of event to publish
        data: Event payload data

    Example:
        await publish_event(
            EventType.LISTING_CREATED,
            {"listing_id": 123, "timestamp": datetime.utcnow().isoformat()}
        )
    """
    try:
        redis = await cache_manager.get_redis()

        event = Event(type=event_type, data=data)
        message = event.model_dump_json()

        await redis.publish(EVENTS_CHANNEL, message)

        logger.debug(
            "event.published",
            event_type=event_type.value,
            data=data,
        )
    except Exception as exc:
        # Log error but don't fail the request
        logger.error(
            "event.publish_failed",
            event_type=event_type.value,
            error=str(exc),
        )


__all__ = [
    "EventType",
    "Event",
    "ListingCreatedData",
    "ListingUpdatedData",
    "ListingDeletedData",
    "ValuationRecalculatedData",
    "ImportCompletedData",
    "EVENTS_CHANNEL",
    "publish_event",
]
