"""
Server-Sent Events (SSE) endpoint for real-time updates.

Provides SSE endpoint for streaming real-time events to connected clients.
Clients connect via EventSource and receive events published to Redis pub/sub channel.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from ..cache import cache_manager
from ..events import EVENTS_CHANNEL
from ..telemetry import get_logger

logger = get_logger("dealbrain.api.events")

router = APIRouter(prefix="/v1/events", tags=["events"])


async def event_stream(request: Request):
    """
    Stream events to client via SSE.

    Subscribes to Redis pub/sub channel and streams events to connected client.
    Handles client disconnection gracefully and cleans up subscriptions.

    Yields:
        dict: SSE event with 'event' and 'data' keys

    Example event:
        {
            "event": "listing.created",
            "data": '{"listing_id": 123, "timestamp": "2025-11-19T12:00:00Z"}'
        }
    """
    logger.info("sse.connection.opened")

    redis = await cache_manager.get_redis()
    pubsub = redis.pubsub()

    try:
        await pubsub.subscribe(EVENTS_CHANNEL)
        logger.debug("sse.subscribed", channel=EVENTS_CHANNEL)

        # Send initial comment to establish connection
        yield {
            "event": "connected",
            "data": '{"status": "connected"}',
        }

        # Stream events until client disconnects
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("sse.connection.closed")
                break

            # Get message from Redis pub/sub (non-blocking)
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)

            if message and message["type"] == "message":
                try:
                    # message["data"] is already the JSON string from publish_event
                    event_data = message["data"]

                    # Parse to extract event type
                    import json

                    parsed = json.loads(event_data)
                    event_type = parsed.get("type", "unknown")

                    # Stream to client
                    yield {
                        "event": event_type,
                        "data": json.dumps(parsed.get("data", {})),
                    }

                    logger.debug("sse.event.sent", event_type=event_type)

                except Exception as exc:
                    logger.error("sse.event.parse_error", error=str(exc))
                    continue

            # Prevent busy loop
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        logger.info("sse.connection.cancelled")
    except Exception as exc:
        logger.error("sse.connection.error", error=str(exc))
    finally:
        # Clean up subscription
        try:
            await pubsub.unsubscribe(EVENTS_CHANNEL)
            await pubsub.close()
            logger.debug("sse.unsubscribed", channel=EVENTS_CHANNEL)
        except Exception as exc:
            logger.warning("sse.cleanup_error", error=str(exc))


@router.get("", response_class=EventSourceResponse)
async def stream_events(request: Request):
    """
    SSE endpoint for real-time event streaming.

    Clients connect using EventSource:
        const eventSource = new EventSource('/api/v1/events')
        eventSource.addEventListener('listing.created', (event) => {
            const data = JSON.parse(event.data)
            console.log('New listing:', data.listing_id)
        })

    Supported events:
    - listing.created: New listing created
    - listing.updated: Listing updated
    - listing.deleted: Listing deleted
    - valuation.recalculated: Valuations recalculated
    - import.completed: Import job completed

    Returns:
        EventSourceResponse: SSE stream with events
    """
    return EventSourceResponse(event_stream(request))


__all__ = ["router"]
