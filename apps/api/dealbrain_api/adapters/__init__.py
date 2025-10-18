"""URL ingestion adapters."""

from .base import (
    AdapterError,
    AdapterException,
    BaseAdapter,
    RateLimitConfig,
    RetryConfig,
)
from .ebay import EbayAdapter
from .jsonld import JsonLdAdapter
from .router import AVAILABLE_ADAPTERS, AdapterRouter

__all__ = [
    "AdapterError",
    "AdapterException",
    "BaseAdapter",
    "RateLimitConfig",
    "RetryConfig",
    "EbayAdapter",
    "JsonLdAdapter",
    "AdapterRouter",
    "AVAILABLE_ADAPTERS",
]
