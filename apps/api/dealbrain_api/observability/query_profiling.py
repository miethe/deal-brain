"""SQLAlchemy query profiling and slow query logging.

This module provides query performance monitoring with:
- Automatic slow query logging (configurable threshold)
- Query execution time tracking
- N+1 query detection warnings
- Integration with OpenTelemetry tracing
"""

from __future__ import annotations

import logging
import time
from typing import Any

from opentelemetry import trace
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Slow query threshold in milliseconds
SLOW_QUERY_THRESHOLD_MS = 500

# Track queries per request to detect N+1 issues
_query_counts: dict[str, int] = {}


def setup_query_profiling(engine: Engine, slow_query_threshold_ms: int = 500) -> None:
    """Set up query profiling event listeners.

    Args:
        engine: SQLAlchemy engine instance
        slow_query_threshold_ms: Threshold for logging slow queries (default: 500ms)
    """
    global SLOW_QUERY_THRESHOLD_MS
    SLOW_QUERY_THRESHOLD_MS = slow_query_threshold_ms

    # Listen for query execution events
    event.listen(engine, "before_cursor_execute", before_cursor_execute, named=True)
    event.listen(engine, "after_cursor_execute", after_cursor_execute, named=True)

    logger.info(
        f"Query profiling enabled (slow query threshold: {slow_query_threshold_ms}ms)"
    )


def before_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool
) -> None:
    """Hook called before query execution.

    Records start time for query duration calculation.

    Args:
        conn: Database connection
        cursor: Database cursor
        statement: SQL statement being executed
        parameters: Query parameters
        context: Execution context
        executemany: Whether this is an executemany operation
    """
    conn.info.setdefault("query_start_time", []).append(time.time())


def after_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool
) -> None:
    """Hook called after query execution.

    Logs slow queries and tracks query counts for N+1 detection.

    Args:
        conn: Database connection
        cursor: Database cursor
        statement: SQL statement executed
        parameters: Query parameters
        context: Execution context
        executemany: Whether this was an executemany operation
    """
    # Calculate query duration
    start_time = conn.info["query_start_time"].pop()
    duration_ms = (time.time() - start_time) * 1000

    # Log slow queries
    if duration_ms > SLOW_QUERY_THRESHOLD_MS:
        # Truncate statement for logging (avoid massive logs)
        truncated_statement = statement[:500] + "..." if len(statement) > 500 else statement

        logger.warning(
            f"SLOW QUERY ({duration_ms:.2f}ms): {truncated_statement}",
            extra={
                "query_duration_ms": duration_ms,
                "query_statement": truncated_statement,
                "slow_query": True
            }
        )

        # Add span event for OpenTelemetry
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(
                "slow_query",
                attributes={
                    "db.statement": truncated_statement[:200],
                    "db.duration_ms": duration_ms
                }
            )

    # Track query counts for N+1 detection
    # Count similar queries (first 100 chars of statement)
    query_signature = statement[:100]
    _query_counts[query_signature] = _query_counts.get(query_signature, 0) + 1

    # Warn if same query pattern executed many times (potential N+1)
    if _query_counts[query_signature] > 10:
        logger.warning(
            f"Potential N+1 query detected: Same query pattern executed "
            f"{_query_counts[query_signature]} times: {query_signature}...",
            extra={
                "query_count": _query_counts[query_signature],
                "query_signature": query_signature,
                "n_plus_one_warning": True
            }
        )


def reset_query_counts() -> None:
    """Reset query count tracking.

    Should be called at the start of each request to track queries per request.
    """
    global _query_counts
    _query_counts.clear()


@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
    """Set SQLite-specific pragmas for better performance.

    Only applied to SQLite connections. No effect on PostgreSQL.

    Args:
        dbapi_conn: Database connection
        connection_record: Connection record
    """
    # Only apply to SQLite
    if "sqlite" in str(type(dbapi_conn)):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


__all__ = ["setup_query_profiling", "reset_query_counts"]
