"""Helpers for managing telemetry context."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any, Mapping

from structlog import contextvars as struct_contextvars

_request_id_var: ContextVar[str | None] = ContextVar("dealbrain_request_id", default=None)
_user_id_var: ContextVar[str | None] = ContextVar("dealbrain_user_id", default=None)


def new_request_id() -> str:
    """Generate a correlation id for requests/tasks."""
    return uuid.uuid4().hex


def bind_request_context(request_id: str, **extra: Any) -> None:
    """Bind request-id and optional fields into the structlog context."""
    _request_id_var.set(request_id)
    struct_contextvars.bind_contextvars(request_id=request_id, **extra)


def bind_user_context(user_id: str | None) -> None:
    """Augment the context with a user identifier when available."""
    _user_id_var.set(user_id)
    if user_id is None:
        struct_contextvars.unbind_contextvars("user_id")
    else:
        struct_contextvars.bind_contextvars(user_id=user_id)


def clear_context(*keys: str) -> None:
    """Clear context variables, optionally scoping to specific keys."""
    if keys:
        struct_contextvars.unbind_contextvars(*keys)
    else:
        struct_contextvars.clear_contextvars()
    _request_id_var.set(None)
    _user_id_var.set(None)


def current_context() -> Mapping[str, Any]:
    """Return the current context dictionary."""
    context: dict[str, Any] = {}
    request_id = _request_id_var.get()
    if request_id is not None:
        context["request_id"] = request_id
    user_id = _user_id_var.get()
    if user_id is not None:
        context["user_id"] = user_id
    return context
