"""Ingestion metrics and raw payload storage for telemetry and debugging."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dealbrain_core.enums import SourceDataType

from ..db import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .listings import Listing


class RawPayload(Base, TimestampMixin):
    """Stores raw adapter payloads for URL-ingested listings.

    Preserves original data from adapters (JSON-LD, API responses, HTML) for
    debugging, re-processing, and audit trails. TTL-based cleanup prevents
    unbounded storage growth.
    """

    __tablename__ = "raw_payload"
    __table_args__ = (Index("ix_raw_payload_listing_adapter", "listing_id", "adapter"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listing.id", ondelete="CASCADE"), nullable=False
    )
    adapter: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=SourceDataType.JSON.value
    )
    payload: Mapped[dict[str, Any] | str] = mapped_column(JSON, nullable=False)
    ttl_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    listing: Mapped[Listing] = relationship(lazy="selectin")


class IngestionMetric(Base, TimestampMixin):
    """Tracks adapter performance metrics for telemetry dashboard.

    Aggregates success rates, latencies, and field completeness per adapter.
    Supports time-series analysis for monitoring adapter health and identifying
    regressions.

    Example aggregation queries:
        -- Recent adapter success rate
        SELECT adapter,
               SUM(success_count)::float / NULLIF(SUM(success_count + failure_count), 0) AS success_rate
        FROM ingestion_metric
        WHERE measured_at >= NOW() - INTERVAL '24 hours'
        GROUP BY adapter;

        -- P95 latency trend
        SELECT DATE_TRUNC('hour', measured_at) AS hour,
               adapter,
               AVG(p95_latency_ms) AS avg_p95_latency
        FROM ingestion_metric
        WHERE measured_at >= NOW() - INTERVAL '7 days'
        GROUP BY hour, adapter
        ORDER BY hour DESC;

        -- Field completeness by adapter
        SELECT adapter,
               AVG(field_completeness_pct) AS avg_completeness
        FROM ingestion_metric
        WHERE measured_at >= NOW() - INTERVAL '7 days'
        GROUP BY adapter
        ORDER BY avg_completeness DESC;
    """

    __tablename__ = "ingestion_metric"
    __table_args__ = (Index("ix_ingestion_metric_adapter_measured", "adapter", "measured_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    adapter: Mapped[str] = mapped_column(String(64), nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    p50_latency_ms: Mapped[int | None] = mapped_column(Integer)
    p95_latency_ms: Mapped[int | None] = mapped_column(Integer)
    field_completeness_pct: Mapped[float | None]
    measured_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
