"""Ingestion service package for URL-based listing imports.

This package is organized into focused modules:
- deduplication: Duplicate detection using vendor IDs and hashes
- normalizer: Data normalization and enrichment
- events: Event emission for listing lifecycle
- service: Main ingestion orchestration
"""

from .deduplication import DeduplicationResult, DeduplicationService
from .events import (
    IngestionEventService,
    ListingCreatedEvent,
    PriceChangedEvent,
    should_emit_price_change,
)
from .normalizer import ListingNormalizer
from .service import IngestionResult, IngestionService

__all__ = [
    # Deduplication
    "DeduplicationResult",
    "DeduplicationService",
    # Normalizer
    "ListingNormalizer",
    # Events
    "IngestionEventService",
    "ListingCreatedEvent",
    "PriceChangedEvent",
    "should_emit_price_change",
    # Main service
    "IngestionResult",
    "IngestionService",
]
