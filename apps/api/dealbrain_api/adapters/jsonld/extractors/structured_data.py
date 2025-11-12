"""Structured data extraction for JSON-LD, Microdata, and RDFa formats."""

import logging
from typing import Any

import extruct
import httpx
from dealbrain_api.adapters.base import AdapterError, AdapterException

logger = logging.getLogger(__name__)


class StructuredDataExtractor:
    """
    Extracts and validates Schema.org Product data from structured formats.

    Supports extraction from:
    1. JSON-LD (most common, easiest to parse)
    2. Microdata (embedded in HTML with itemscope/itemtype)
    3. RDFa (least common, most complex)
    """

    def __init__(self, timeout_s: int, rate_limiter_check: callable):
        """
        Initialize structured data extractor.

        Args:
            timeout_s: HTTP request timeout in seconds
            rate_limiter_check: Async callable to check rate limits before requests
        """
        self.timeout_s = timeout_s
        self._check_rate_limit = rate_limiter_check

    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL with retry logic.

        Makes a GET request with a proper User-Agent to avoid being blocked
        by anti-bot protections. Implements retry logic for transient failures.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            AdapterException: On network errors, timeout, or HTTP errors
        """
        await self._check_rate_limit()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; DealBrainBot/1.0; "
                "+https://github.com/yourusername/deal-brain)"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 404:
                    raise AdapterException(
                        AdapterError.ITEM_NOT_FOUND,
                        f"Page not found: {url}",
                        metadata={"url": url, "status_code": 404},
                    )
                elif response.status_code == 429:
                    raise AdapterException(
                        AdapterError.RATE_LIMITED,
                        "Rate limit exceeded",
                        metadata={"url": url, "status_code": 429},
                    )
                elif response.status_code >= 500:
                    raise AdapterException(
                        AdapterError.NETWORK_ERROR,
                        f"Server error: {response.status_code}",
                        metadata={"url": url, "status_code": response.status_code},
                    )

                response.raise_for_status()
                html = response.text

                # Debug logging: log HTML characteristics
                logger.debug(
                    f"Fetched HTML from {url}: "
                    f"length={len(html)} chars, "
                    f"has_meta_tags={html.count('<meta') if html else 0}"
                )

                return html

        except httpx.TimeoutException as e:
            raise AdapterException(
                AdapterError.TIMEOUT,
                f"Request timed out after {self.timeout_s}s",
                metadata={"url": url, "timeout_s": self.timeout_s},
            ) from e
        except httpx.NetworkError as e:
            raise AdapterException(
                AdapterError.NETWORK_ERROR,
                f"Network error: {e}",
                metadata={"url": url},
            ) from e
        except Exception as e:
            if isinstance(e, AdapterException):
                raise
            raise AdapterException(
                AdapterError.NETWORK_ERROR,
                f"Unexpected error fetching URL: {e}",
                metadata={"url": url},
            ) from e

    def extract_structured_data(self, html: str, url: str) -> dict[str, Any]:
        """
        Extract all structured data from HTML using extruct.

        Args:
            html: HTML content to parse
            url: Base URL for resolving relative URLs

        Returns:
            Dict containing json-ld, microdata, and rdfa data
        """
        return extruct.extract(html, base_url=url)

    def find_product_schema(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Find Schema.org Product in extracted structured data.

        Checks in priority order:
        1. JSON-LD (data['json-ld'])
        2. Microdata (data['microdata'])
        3. RDFa (data['rdfa'])

        Each format may contain multiple items, so we search for the first
        item with @type or type == "Product".

        Args:
            data: Structured data extracted by extruct

        Returns:
            Product schema dict or None if not found
        """
        # Try JSON-LD first (most common)
        if "json-ld" in data and data["json-ld"]:
            for item in data["json-ld"]:
                if self._is_product_schema(item):
                    logger.debug("Found Product schema in JSON-LD")
                    return dict(item)  # Cast to dict

        # Try Microdata second
        if "microdata" in data and data["microdata"]:
            for item in data["microdata"]:
                if self._is_product_schema(item):
                    logger.debug("Found Product schema in Microdata")
                    return dict(item)  # Cast to dict

        # Try RDFa last (least common)
        if "rdfa" in data and data["rdfa"]:
            for item in data["rdfa"]:
                if self._is_product_schema(item):
                    logger.debug("Found Product schema in RDFa")
                    return dict(item)  # Cast to dict

        return None

    def _is_product_schema(self, item: dict[str, Any]) -> bool:
        """
        Check if an item is a Schema.org Product.

        Args:
            item: Schema.org item dict

        Returns:
            True if item is a Product schema
        """
        # Check @type (JSON-LD)
        if "@type" in item:
            item_type = item["@type"]
            # Handle both string and list
            if isinstance(item_type, str):
                return item_type.lower() == "product"
            elif isinstance(item_type, list):
                return any(t.lower() == "product" for t in item_type if isinstance(t, str))

        # Check type (Microdata/RDFa)
        if "type" in item:
            item_type = item["type"]
            if isinstance(item_type, str):
                # Check for full URL or just "Product"
                return "product" in item_type.lower()
            elif isinstance(item_type, list):
                return any("product" in t.lower() for t in item_type if isinstance(t, str))

        return False


__all__ = ["StructuredDataExtractor"]
