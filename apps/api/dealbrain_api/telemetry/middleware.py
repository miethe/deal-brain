"""FastAPI middleware for request observability."""

from __future__ import annotations

import time

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .context import bind_request_context, clear_context, new_request_id

logger = structlog.get_logger("dealbrain.api.request")


class ObservabilityMiddleware:
    """ASGI middleware that enriches requests with telemetry context and logging."""

    def __init__(self, app: ASGIApp, record_headers: bool = False) -> None:
        self.app = app
        self.record_headers = record_headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id_value = request.headers.get("x-request-id") or new_request_id()

        bind_request_context(
            request_id_value,
            http_method=request.method,
            http_path=request.url.path,
        )
        if hasattr(request.state, "__dict__"):
            request.state.request_id = request_id_value  # type: ignore[attr-defined]

        start = time.perf_counter()
        response_status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal response_status_code
            if message["type"] == "http.response.start":
                response_status_code = message["status"]
                headers = list(message.get("headers") or [])
                headers.append((b"x-request-id", request_id_value.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request.failed",
                request_id=request_id_value,
                method=request.method,
                path=request.url.path,
                client_host=request.client.host if request.client else None,
                duration_ms=round(duration_ms, 2),
            )
            clear_context()
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000
            log_kwargs = {
                "request_id": request_id_value,
                "method": request.method,
                "path": request.url.path,
                "status_code": response_status_code,
                "duration_ms": round(duration_ms, 2),
                "client_host": request.client.host if request.client else None,
            }
            if self.record_headers:
                log_kwargs["headers"] = dict(request.headers)
            logger.info("request.completed", **log_kwargs)
        finally:
            clear_context()
