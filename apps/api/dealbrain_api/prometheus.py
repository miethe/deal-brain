"""Prometheus metric declarations safe across package import aliases."""

from __future__ import annotations

from typing import Any, TypeVar

from prometheus_client import REGISTRY
from prometheus_client.metrics import Metric

MetricType = TypeVar("MetricType", bound=Metric)


def get_or_create_metric(
    metric_type: type[MetricType], name: str, documentation: str, *args: Any, **kwargs: Any
) -> MetricType:
    """Return a registered metric when this module is imported under a second package name."""
    try:
        return metric_type(name, documentation, *args, **kwargs)
    except ValueError as exc:
        if "Duplicated timeseries" not in str(exc):
            raise

        registered = REGISTRY._names_to_collectors.get(name)
        if not isinstance(registered, metric_type):
            raise
        return registered
