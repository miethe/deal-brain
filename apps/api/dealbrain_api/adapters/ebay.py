"""eBay Browse API adapter for extracting listing data."""

from __future__ import annotations

import logging
import re
from decimal import Decimal
from typing import Any

import httpx
from dealbrain_api.adapters.base import AdapterError, AdapterException, BaseAdapter
from dealbrain_api.settings import get_settings
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)


class EbayAdapter(BaseAdapter):
    """
    eBay Browse API adapter for extracting listing data.

    This adapter uses the eBay Browse API v1 to fetch item details from eBay URLs.
    It parses item IDs from various eBay URL formats, calls the Browse API with
    OAuth authentication, and maps the response to NormalizedListingSchema.

    URL Formats Supported:
    ----------------------
    - https://www.ebay.com/itm/123456789012
    - https://www.ebay.com/itm/Product-Name/123456789012
    - https://ebay.com/itm/123456789012?hash=...
    - https://www.ebay.com/itm/123456789012?_trkparms=...

    eBay API Integration:
    --------------------
    - Endpoint: GET /buy/browse/v1/item/{item_id}
    - Authentication: OAuth 2.0 Application token (from settings)
    - Headers: Authorization: Bearer {access_token}
              X-EBAY-C-MARKETPLACE-ID: EBAY_US

    Data Mapping:
    ------------
    Maps eBay Browse API response fields to NormalizedListingSchema:
    - title: item.title
    - price: item.price.value (converted to Decimal)
    - currency: item.price.currency
    - condition: Normalized from item.condition
    - images: [item.image.imageUrl] (primary image only)
    - seller: item.seller.username
    - marketplace: "ebay"
    - vendor_item_id: item.itemId
    - description: item.description

    Item specifics (CPU, RAM, storage) are extracted from item.localizedAspects
    or item.itemSpecifics array.

    Error Handling:
    --------------
    - ITEM_NOT_FOUND (404): Item does not exist or has been removed
    - INVALID_CREDENTIALS (401): Invalid or expired OAuth token
    - RATE_LIMITED (429): API rate limit exceeded
    - TIMEOUT: Request timeout (retries with exponential backoff)
    - PARSE_ERROR: Failed to parse item ID from URL

    Retry Logic:
    -----------
    - Exponential backoff: 1s, 2s, 4s
    - Max retries: Configured from settings (default 2)
    - Retry on: 429, 500, 503, timeout
    - Don't retry: 400, 401, 404
    """

    # Class attributes for router metadata access
    _adapter_name = "ebay"
    _adapter_domains = ["ebay.com", "www.ebay.com"]
    _adapter_priority = 1

    def __init__(self) -> None:
        """
        Initialize eBay adapter.

        Loads configuration from settings including API key, timeout, and retries.
        Validates that the eBay Browse API key is configured.

        Raises:
            ValueError: If eBay Browse API key is not configured
        """
        settings = get_settings()

        # Initialize base adapter with eBay-specific configuration
        super().__init__(
            name="ebay",
            supported_domains=["ebay.com", "www.ebay.com"],
            priority=1,  # Highest priority (API is most reliable)
            timeout_s=settings.ingestion.ebay.timeout_s,
            max_retries=settings.ingestion.ebay.retries,
            requests_per_minute=60,  # Conservative rate limit
        )

        # eBay Browse API configuration
        self.api_base = "https://api.ebay.com/buy/browse/v1"
        self.api_key = settings.ingestion.ebay.api_key

        if not self.api_key:
            raise ValueError(
                "eBay Browse API key not configured in settings.ingestion.ebay.api_key"
            )

        logger.info(
            f"Initialized EbayAdapter with timeout={self.timeout_s}s, "
            f"retries={self.retry_config.max_retries}"
        )

    async def extract(self, url: str) -> NormalizedListingSchema:
        """
        Extract listing data from eBay URL.

        This is the main entry point that orchestrates the extraction workflow:
        1. Parse item ID from URL
        2. Fetch item data from eBay Browse API (with retry)
        3. Map API response to NormalizedListingSchema

        Args:
            url: eBay item URL to extract data from

        Returns:
            NormalizedListingSchema with normalized listing data

        Raises:
            AdapterException: If extraction fails at any step
        """
        logger.info(f"Extracting listing data from eBay URL: {url}")

        # Step 1: Parse item ID from URL
        item_id = self._parse_item_id(url)
        logger.debug(f"Extracted item ID: {item_id}")

        # Step 2: Fetch item data with retry logic
        item_data = await self.retry_config.execute_with_retry(self._fetch_item, item_id)

        # Step 3: Map to normalized schema
        normalized = self._map_to_schema(item_data)

        logger.info(f"Successfully extracted listing: {normalized.title}")
        return normalized

    def _parse_item_id(self, url: str) -> str:
        """
        Extract eBay item ID from URL.

        Supports various eBay URL formats:
        - https://www.ebay.com/itm/123456789012
        - https://www.ebay.com/itm/Product-Name/123456789012
        - https://ebay.com/itm/123456789012?hash=...

        Args:
            url: eBay URL to parse

        Returns:
            Item ID as string (e.g., "123456789012")

        Raises:
            AdapterException: If item ID cannot be extracted from URL
        """
        # Pattern matches:
        # - /itm/123456789012
        # - /itm/Product-Name/123456789012
        # - /itm/123456789012?params
        # Item IDs are typically 12 digits
        pattern = r"/itm/(?:[^/]+/)?(\d{10,13})(?:\?|$|#)"
        match = re.search(pattern, url)

        if not match:
            raise AdapterException(
                AdapterError.PARSE_ERROR,
                f"Could not extract eBay item ID from URL: {url}",
                metadata={"url": url},
            )

        item_id = match.group(1)
        return item_id

    async def _fetch_item(self, item_id: str) -> dict[str, Any]:
        """
        Fetch item data from eBay Browse API with retry logic.

        Makes a GET request to /buy/browse/v1/item/{item_id} with OAuth
        authentication. Handles eBay-specific error codes and implements
        retry logic for transient failures.

        Args:
            item_id: eBay item ID to fetch

        Returns:
            eBay API response as dictionary

        Raises:
            AdapterException: On API errors (404, 401, rate limit, etc.)
        """
        # Check rate limit before making request
        await self._check_rate_limit()

        url = f"{self.api_base}/item/v1|{item_id}|0"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.get(url, headers=headers)

                # Handle eBay API error responses
                if response.status_code == 404:
                    raise AdapterException(
                        AdapterError.ITEM_NOT_FOUND,
                        f"eBay item {item_id} not found",
                        metadata={"item_id": item_id, "status_code": 404},
                    )
                elif response.status_code == 401:
                    raise AdapterException(
                        AdapterError.INVALID_SCHEMA,
                        "Invalid or expired eBay API credentials",
                        metadata={"status_code": 401},
                    )
                elif response.status_code == 429:
                    raise AdapterException(
                        AdapterError.RATE_LIMITED,
                        "eBay API rate limit exceeded",
                        metadata={"status_code": 429},
                    )
                elif response.status_code >= 500:
                    raise AdapterException(
                        AdapterError.NETWORK_ERROR,
                        f"eBay API server error: {response.status_code}",
                        metadata={"status_code": response.status_code},
                    )

                response.raise_for_status()
                json_data: dict[str, Any] = response.json()
                return json_data

        except httpx.TimeoutException as e:
            raise AdapterException(
                AdapterError.TIMEOUT,
                f"eBay API request timed out after {self.timeout_s}s",
                metadata={"item_id": item_id, "timeout_s": self.timeout_s},
            ) from e
        except httpx.NetworkError as e:
            raise AdapterException(
                AdapterError.NETWORK_ERROR,
                f"Network error calling eBay API: {e}",
                metadata={"item_id": item_id},
            ) from e
        except Exception as e:
            if isinstance(e, AdapterException):
                raise
            raise AdapterException(
                AdapterError.NETWORK_ERROR,
                f"Unexpected error calling eBay API: {e}",
                metadata={"item_id": item_id},
            ) from e

    def _map_to_schema(self, item_data: dict[str, Any]) -> NormalizedListingSchema:
        """
        Map eBay API response to NormalizedListingSchema.

        Extracts fields from the eBay Browse API response and transforms them
        into the canonical NormalizedListingSchema format.

        eBay Response Structure:
        -----------------------
        {
            "itemId": "v1|123456789012|0",
            "title": "Gaming PC Intel Core i7-12700K...",
            "price": {"value": "599.99", "currency": "USD"},
            "condition": "Used",
            "image": {"imageUrl": "https://i.ebayimg.com/..."},
            "seller": {"username": "seller123", "feedbackScore": 1500},
            "shortDescription": "PC description...",
            "localizedAspects": [
                {"name": "Processor", "value": "Intel Core i7-12700K"},
                {"name": "RAM Size", "value": "16 GB"},
                {"name": "SSD Capacity", "value": "512 GB"}
            ]
        }

        Args:
            item_data: Raw eBay API response dictionary

        Returns:
            NormalizedListingSchema with mapped data

        Raises:
            AdapterException: If required fields are missing or invalid
        """
        try:
            # Extract basic fields
            title = item_data.get("title", "")
            if not title:
                raise AdapterException(
                    AdapterError.INVALID_SCHEMA,
                    "Missing required field: title",
                    metadata={"item_data": item_data},
                )

            # Extract and validate price
            price_obj = item_data.get("price", {})
            price_value = price_obj.get("value")
            if not price_value:
                raise AdapterException(
                    AdapterError.INVALID_SCHEMA,
                    "Missing required field: price.value",
                    metadata={"item_data": item_data},
                )

            price = Decimal(str(price_value))
            currency = price_obj.get("currency", "USD")

            # Extract condition and normalize
            condition_raw = item_data.get("condition", "Used")
            condition = self._normalize_condition(condition_raw)

            # Extract primary image
            images = []
            image_obj = item_data.get("image", {})
            if image_url := image_obj.get("imageUrl"):
                images.append(image_url)

            # Extract seller information
            seller_obj = item_data.get("seller", {})
            seller = seller_obj.get("username")

            # Extract item ID (strip the v1| prefix if present)
            vendor_item_id = item_data.get("itemId", "")
            if vendor_item_id.startswith("v1|"):
                # Format is "v1|123456789012|0"
                parts = vendor_item_id.split("|")
                if len(parts) >= 2:
                    vendor_item_id = parts[1]

            # Extract description
            description = item_data.get("shortDescription") or item_data.get("description")

            # Extract specs from localizedAspects or itemSpecifics
            aspects = item_data.get("localizedAspects", []) or item_data.get("itemSpecifics", [])
            cpu_model = self._extract_cpu_from_aspects(aspects)
            ram_gb = self._extract_ram_from_aspects(aspects)
            storage_gb = self._extract_storage_from_aspects(aspects)

            # Build normalized schema
            return NormalizedListingSchema(
                title=title,
                price=price,
                currency=currency,
                condition=condition,
                images=images,
                seller=seller,
                marketplace="ebay",
                vendor_item_id=vendor_item_id,
                description=description,
                cpu_model=cpu_model,
                ram_gb=ram_gb,
                storage_gb=storage_gb,
            )

        except Exception as e:
            if isinstance(e, AdapterException):
                raise
            raise AdapterException(
                AdapterError.INVALID_SCHEMA,
                f"Failed to map eBay response to schema: {e}",
                metadata={"item_data": item_data},
            ) from e

    def _normalize_condition(self, condition_raw: str) -> str:
        """
        Normalize eBay condition string to Deal Brain Condition enum.

        eBay Conditions:
        ---------------
        - "New" -> "new"
        - "New other (see details)" -> "new"
        - "Seller refurbished" -> "refurb"
        - "Manufacturer refurbished" -> "refurb"
        - "Used" -> "used"
        - "For parts or not working" -> "used"

        Args:
            condition_raw: Raw eBay condition string

        Returns:
            Normalized condition string matching Condition enum
        """
        condition_lower = condition_raw.lower()

        if "new" in condition_lower:
            return str(Condition.NEW.value)
        elif "refurb" in condition_lower:
            return str(Condition.REFURB.value)
        else:
            # Default to "used" for any other condition
            return str(Condition.USED.value)

    def _extract_cpu_from_aspects(self, aspects: list[dict[str, Any]]) -> str | None:
        """
        Extract CPU model from eBay item aspects.

        Looks for aspects with names like:
        - "Processor"
        - "Processor Type"
        - "CPU"

        Args:
            aspects: List of eBay localizedAspects or itemSpecifics

        Returns:
            CPU model string or None if not found

        Example:
            >>> aspects = [{"name": "Processor", "value": "Intel Core i7-12700K"}]
            >>> _extract_cpu_from_aspects(aspects)
            "Intel Core i7-12700K"
        """
        cpu_keywords = ["processor", "cpu", "processor type"]

        for aspect in aspects:
            name = aspect.get("name", "").lower()
            value = aspect.get("value", "")

            if any(keyword in name for keyword in cpu_keywords):
                return value.strip() if value else None

        return None

    def _extract_ram_from_aspects(self, aspects: list[dict[str, Any]]) -> int | None:
        """
        Extract RAM size in GB from eBay item aspects.

        Looks for aspects with names like:
        - "RAM Size"
        - "Memory"
        - "RAM"

        Parses values like:
        - "16 GB" -> 16
        - "32GB" -> 32
        - "8 GB DDR4" -> 8

        Args:
            aspects: List of eBay localizedAspects or itemSpecifics

        Returns:
            RAM size in GB as integer or None if not found

        Example:
            >>> aspects = [{"name": "RAM Size", "value": "16 GB"}]
            >>> _extract_ram_from_aspects(aspects)
            16
        """
        ram_keywords = ["ram", "memory", "ram size"]

        for aspect in aspects:
            name = aspect.get("name", "").lower()
            value = aspect.get("value", "")

            if any(keyword in name for keyword in ram_keywords):
                # Extract number from value (e.g., "16 GB" -> 16)
                match = re.search(r"(\d+)\s*GB", value, re.IGNORECASE)
                if match:
                    return int(match.group(1))

        return None

    def _extract_storage_from_aspects(self, aspects: list[dict[str, Any]]) -> int | None:
        """
        Extract storage size in GB from eBay item aspects.

        Looks for aspects with names like:
        - "SSD Capacity"
        - "Hard Drive Capacity"
        - "Storage"

        Parses values like:
        - "512 GB" -> 512
        - "1 TB" -> 1024
        - "2TB SSD" -> 2048

        Args:
            aspects: List of eBay localizedAspects or itemSpecifics

        Returns:
            Storage size in GB as integer or None if not found

        Example:
            >>> aspects = [{"name": "SSD Capacity", "value": "512 GB"}]
            >>> _extract_storage_from_aspects(aspects)
            512
        """
        storage_keywords = ["ssd", "storage", "hard drive", "hdd", "capacity"]

        for aspect in aspects:
            name = aspect.get("name", "").lower()
            value = aspect.get("value", "")

            if any(keyword in name for keyword in storage_keywords):
                # Check for TB first (convert to GB)
                tb_match = re.search(r"(\d+)\s*TB", value, re.IGNORECASE)
                if tb_match:
                    return int(tb_match.group(1)) * 1024

                # Then check for GB
                gb_match = re.search(r"(\d+)\s*GB", value, re.IGNORECASE)
                if gb_match:
                    return int(gb_match.group(1))

        return None


__all__ = ["EbayAdapter"]
