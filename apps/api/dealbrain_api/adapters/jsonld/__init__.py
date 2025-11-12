"""
JSON-LD/Microdata adapter for generic retailer websites.

This module provides a universal fallback adapter for extracting product data from
any website using structured data (JSON-LD, Microdata, RDFa), meta tags (OpenGraph,
Twitter Card), or HTML element patterns.

Main Components:
---------------
- JsonLdAdapter: Main adapter class (orchestrates extraction workflow)
- StructuredDataExtractor: JSON-LD/Microdata/RDFa extraction
- MetaTagExtractor: OpenGraph/Twitter Card fallback
- HtmlElementExtractor: HTML element pattern matching (final fallback)
- PriceParser: Price parsing utilities
- SpecParser: CPU/RAM/storage extraction
- ImageParser: Image URL extraction
- SchemaMapper: Schema.org to NormalizedListingSchema mapping

Usage:
------
    from dealbrain_api.adapters.jsonld import JsonLdAdapter

    adapter = JsonLdAdapter()
    listing = await adapter.extract("https://example.com/product")

This maintains backward compatibility with the original monolithic module while
providing a cleaner internal structure.
"""

# Main adapter export for backward compatibility
from .base import JsonLdAdapter

# Optional: Export sub-components for advanced usage
from .extractors import HtmlElementExtractor, MetaTagExtractor, StructuredDataExtractor
from .normalizers import SchemaMapper
from .parsers import ImageParser, PriceParser, SpecParser

# Export get_settings for test mocking compatibility
from dealbrain_api.settings import get_settings

__all__ = [
    # Primary export (backward compatible)
    "JsonLdAdapter",
    # Sub-components (optional, for advanced usage)
    "StructuredDataExtractor",
    "MetaTagExtractor",
    "HtmlElementExtractor",
    "PriceParser",
    "SpecParser",
    "ImageParser",
    "SchemaMapper",
    # Settings (for test mocking)
    "get_settings",
]
