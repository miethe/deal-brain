"""JSON-LD/Microdata adapter for generic retailer websites."""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

import extruct
import httpx
from dealbrain_api.adapters.base import AdapterError, AdapterException, BaseAdapter
from dealbrain_api.settings import get_settings
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)


# Regex patterns for spec extraction
CPU_PATTERN = re.compile(
    r"(?:Intel|AMD)?\s*(?:Core)?\s*(i[3579]|Ryzen\s*[3579])\s*-?\s*(\d{4,5}[A-Z]*)",
    re.IGNORECASE,
)

RAM_PATTERN = re.compile(
    r"(\d+)\s*GB\s*(?:RAM|DDR[34]|Memory)?",
    re.IGNORECASE,
)

# Storage pattern requires specific storage keywords to avoid matching RAM
STORAGE_PATTERN = re.compile(
    r"(\d+)\s*(GB|TB)\s*(?:SSD|NVMe|HDD|M\.2|SATA|Storage|Drive)",
    re.IGNORECASE,
)


class JsonLdAdapter(BaseAdapter):
    """
    Generic JSON-LD/Microdata adapter using Schema.org Product extraction.

    This adapter serves as a universal fallback for any retailer website that
    implements structured data using JSON-LD, Microdata, or RDFa. It uses the
    extruct library to extract Schema.org Product data and maps it to
    NormalizedListingSchema.

    Structured Data Support:
    -----------------------
    Extraction priority order:
    1. JSON-LD (most common, easiest to parse)
    2. Microdata (embedded in HTML with itemscope/itemtype)
    3. RDFa (least common, most complex)

    Schema.org Product Mapping:
    ---------------------------
    This adapter looks for Schema.org Product type and extracts:
    - name -> title
    - offers.price / offers[0].price -> price
    - offers.priceCurrency -> currency
    - offers.availability -> condition (InStock = new, Refurbished = refurb)
    - image / images[0] -> images
    - offers.seller.name or brand.name -> seller
    - description -> description (parsed for CPU/RAM/storage)

    Spec Extraction:
    ---------------
    Since most retailers don't include CPU/RAM/storage in structured data,
    this adapter uses regex patterns to extract them from the description:
    - CPU: "Intel Core i7-12700K", "AMD Ryzen 7 5800X"
    - RAM: "16GB RAM", "32 GB DDR4"
    - Storage: "512GB SSD", "1TB NVMe", "2 TB"

    Price Parsing:
    -------------
    Handles various price formats:
    - String: "599.99", "$599.99", "USD 599.99"
    - Number: 599.99
    - With separators: "1,599.99"

    Nested Offers:
    -------------
    Some sites have multiple offers (different sellers, conditions):
    - Takes the lowest price by default
    - Extracts seller from first offer

    Error Handling:
    --------------
    - NO_STRUCTURED_DATA: No Product schema found in page
    - INVALID_SCHEMA: Product schema missing required fields (name, price)
    - PARSE_ERROR: Unable to parse price or specs
    - NETWORK_ERROR: HTTP fetch failed
    - TIMEOUT: Request timeout

    Priority:
    --------
    Priority 5 (lower than domain-specific adapters like eBay)
    Supports all domains via wildcard ["*"]
    """

    # Class attributes for router metadata access
    _adapter_name = "jsonld"
    _adapter_domains = ["*"]
    _adapter_priority = 5

    def __init__(self) -> None:
        """
        Initialize JSON-LD adapter.

        Loads configuration from settings including timeout and retries.
        Uses wildcard domain matching to support any URL.
        """
        settings = get_settings()

        # Initialize base adapter with JSON-LD-specific configuration
        super().__init__(
            name="jsonld",
            supported_domains=["*"],  # Wildcard - supports all domains
            priority=5,  # Lower priority than domain-specific adapters
            timeout_s=settings.ingestion.jsonld.timeout_s,
            max_retries=settings.ingestion.jsonld.retries,
            requests_per_minute=30,  # Conservative rate limit for generic scraping
        )

        logger.info(
            f"Initialized JsonLdAdapter with timeout={self.timeout_s}s, "
            f"retries={self.retry_config.max_retries}"
        )

    async def extract(self, url: str) -> NormalizedListingSchema:
        """
        Extract listing data from any URL using JSON-LD/Microdata.

        Workflow:
        1. Fetch HTML from URL
        2. Extract structured data using extruct
        3. Find Product schema (JSON-LD → Microdata → RDFa)
        4. Map to NormalizedListingSchema
        5. Parse specs from description

        Args:
            url: URL to extract listing data from

        Returns:
            NormalizedListingSchema with normalized listing data

        Raises:
            AdapterException: If extraction fails at any step
        """
        logger.info(f"Extracting listing data from URL using JSON-LD: {url}")

        # Step 1: Fetch HTML
        html = await self._fetch_html(url)

        # Step 2: Extract structured data
        structured_data = extruct.extract(html, base_url=url)

        # Step 3: Find Product schema
        product_data = self._find_product_schema(structured_data)

        if not product_data:
            raise AdapterException(
                AdapterError.NO_STRUCTURED_DATA,
                "No Schema.org Product data found in page",
                metadata={"url": url},
            )

        # Step 4: Map to normalized schema
        normalized = self._map_to_schema(product_data, url)

        logger.info(f"Successfully extracted listing: {normalized.title}")
        return normalized

    def supports_url(self, url: str) -> bool:
        """
        Check if this adapter supports the given URL.

        Since this is a wildcard adapter, it supports all URLs.
        However, it should be used as a fallback after domain-specific
        adapters have been tried.

        Args:
            url: URL to check

        Returns:
            Always True (supports all domains)
        """
        return True

    async def _fetch_html(self, url: str) -> str:
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
                return response.text

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

    def _find_product_schema(self, data: dict[str, Any]) -> dict[str, Any] | None:
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

    def _map_to_schema(self, product: dict[str, Any], url: str) -> NormalizedListingSchema:
        """
        Map Schema.org Product to NormalizedListingSchema.

        Extracts fields from Product schema and parses specs from description.

        Product Schema Structure:
        ------------------------
        JSON-LD format:
        {
            "@type": "Product",
            "name": "Product Name",
            "description": "Description with specs...",
            "image": "https://example.com/image.jpg" or ["url1", "url2"],
            "brand": {"@type": "Brand", "name": "Brand Name"},
            "offers": {
                "@type": "Offer",
                "price": "599.99" or 599.99,
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
                "seller": {"@type": "Organization", "name": "Seller"}
            }
        }

        Microdata format (from extruct):
        {
            "type": "http://schema.org/Product",
            "properties": {
                "name": "Product Name",
                "offers": {...}
            }
        }

        Args:
            product: Product schema dict
            url: Original URL (for error messages)

        Returns:
            NormalizedListingSchema with mapped data

        Raises:
            AdapterException: If required fields are missing
        """
        try:
            # Handle Microdata format (extruct wraps fields in "properties")
            if "properties" in product:
                product = product["properties"]

            # Extract title
            title = product.get("name") or product.get("title")
            if not title:
                raise AdapterException(
                    AdapterError.INVALID_SCHEMA,
                    "Product schema missing required field: name",
                    metadata={"product": product},
                )

            # Extract offers (may be dict or list)
            offers_raw = product.get("offers") or product.get("offer")
            if not offers_raw:
                raise AdapterException(
                    AdapterError.INVALID_SCHEMA,
                    "Product schema missing required field: offers",
                    metadata={"product": product},
                )

            # Normalize offers to list
            offers = self._normalize_offers(offers_raw)

            # Extract price from offers (take lowest if multiple)
            price, currency = self._extract_price_from_offers(offers)

            if price is None:
                raise AdapterException(
                    AdapterError.INVALID_SCHEMA,
                    "No valid price found in offers",
                    metadata={"offers": offers},
                )

            # Extract condition from availability
            condition = self._extract_condition_from_offers(offers)

            # Extract seller
            seller = self._extract_seller(product, offers)

            # Extract images
            images = self._extract_images(product)

            # Extract description
            description = product.get("description")

            # Parse specs from description
            specs = self._extract_specs(description or title)

            # Build normalized schema
            return NormalizedListingSchema(
                title=title,
                price=price,
                currency=currency,
                condition=condition,
                images=images,
                seller=seller,
                marketplace="other",  # Generic marketplace
                vendor_item_id=None,  # Not available from generic sites
                description=description,
                cpu_model=specs.get("cpu_model"),
                ram_gb=specs.get("ram_gb"),
                storage_gb=specs.get("storage_gb"),
            )

        except Exception as e:
            if isinstance(e, AdapterException):
                raise
            raise AdapterException(
                AdapterError.PARSE_ERROR,
                f"Failed to map Product schema: {e}",
                metadata={"product": product, "url": url},
            ) from e

    def _normalize_offers(self, offers_raw: Any) -> list[dict[str, Any]]:
        """
        Normalize offers to list format.

        Handles both JSON-LD and Microdata formats:
        - JSON-LD: {price: "599.99"} or [{price: "599.99"}]
        - Microdata: {properties: {price: "599.99"}}

        Args:
            offers_raw: Single offer dict or list of offers

        Returns:
            List of offer dicts (with Microdata properties unwrapped)
        """
        if isinstance(offers_raw, dict):
            # Handle Microdata format
            if "properties" in offers_raw:
                return [offers_raw["properties"]]
            return [offers_raw]
        elif isinstance(offers_raw, list):
            # Unwrap Microdata properties for each offer
            result = []
            for offer in offers_raw:
                if isinstance(offer, dict) and "properties" in offer:
                    result.append(offer["properties"])
                else:
                    result.append(offer)
            return result
        else:
            return []

    def _extract_price_from_offers(
        self, offers: list[dict[str, Any]]
    ) -> tuple[Decimal | None, str]:
        """
        Extract lowest price from offers.

        Args:
            offers: List of Offer schema dicts

        Returns:
            Tuple of (price as Decimal, currency code)
        """
        prices = []
        currency = "USD"  # Default

        for offer in offers:
            price_raw = offer.get("price")
            if price_raw is not None:
                parsed_price = self._parse_price(price_raw)
                if parsed_price:
                    prices.append(parsed_price)
                    # Extract currency from first valid offer
                    if len(prices) == 1:
                        currency = offer.get("priceCurrency", "USD")

        if prices:
            return min(prices), currency
        return None, currency

    def _parse_price(self, price: Any) -> Decimal | None:
        """
        Parse price from various formats.

        Handles:
        - String: "599.99", "$599.99", "USD 599.99"
        - Number: 599.99
        - With separators: "1,599.99"

        Args:
            price: Price value (string or number)

        Returns:
            Price as Decimal or None if invalid
        """
        if price is None:
            return None

        try:
            # If already a number, convert directly
            if isinstance(price, (int, float)):
                return Decimal(str(price))

            # If string, clean and parse
            if isinstance(price, str):
                # Remove currency symbols, spaces, and common prefixes
                cleaned = price.strip()
                cleaned = re.sub(r"^[A-Z]{3}\s*", "", cleaned)  # Remove "USD "
                cleaned = re.sub(r"[\$£€¥]", "", cleaned)  # Remove currency symbols
                cleaned = re.sub(r",", "", cleaned)  # Remove thousands separators
                cleaned = cleaned.strip()

                # Extract first decimal number
                match = re.search(r"(\d+\.?\d*)", cleaned)
                if match:
                    return Decimal(match.group(1))

            return None

        except (ValueError, InvalidOperation):
            return None

    def _extract_condition_from_offers(self, offers: list[dict[str, Any]]) -> str:
        """
        Extract condition from offer availability.

        Schema.org availability values:
        - InStock / PreOrder / PreSale -> assume NEW
        - Refurbished -> REFURB
        - LimitedAvailability / OnlineOnly -> check description, default NEW

        Args:
            offers: List of Offer schema dicts

        Returns:
            Condition string (new|refurb|used)
        """
        for offer in offers:
            availability = offer.get("availability", "")
            if isinstance(availability, str):
                availability_lower = availability.lower()
                if "refurb" in availability_lower:
                    return str(Condition.REFURB.value)

            # Check itemCondition field (less common)
            item_condition = offer.get("itemCondition", "")
            if isinstance(item_condition, str):
                condition_lower = item_condition.lower()
                if "new" in condition_lower:
                    return str(Condition.NEW.value)
                elif "refurb" in condition_lower:
                    return str(Condition.REFURB.value)
                elif "used" in condition_lower:
                    return str(Condition.USED.value)

        # Default to NEW if not specified
        return str(Condition.NEW.value)

    def _extract_seller(self, product: dict[str, Any], offers: list[dict[str, Any]]) -> str | None:
        """
        Extract seller name from product or offers.

        Priority:
        1. offers[0].seller.name
        2. product.brand.name
        3. product.manufacturer.name

        Handles both JSON-LD and Microdata formats (with properties wrapper).

        Args:
            product: Product schema dict
            offers: List of Offer schema dicts

        Returns:
            Seller name or None
        """
        # Try first offer seller
        if offers:
            seller_obj = offers[0].get("seller", {})
            if isinstance(seller_obj, dict):
                # Handle Microdata format
                if "properties" in seller_obj:
                    seller_obj = seller_obj["properties"]
                seller_name = seller_obj.get("name")
                if seller_name:
                    return str(seller_name)

        # Try brand
        brand_obj = product.get("brand", {})
        if isinstance(brand_obj, dict):
            # Handle Microdata format
            if "properties" in brand_obj:
                brand_obj = brand_obj["properties"]
            brand_name = brand_obj.get("name")
            if brand_name:
                return str(brand_name)

        # Try manufacturer
        manufacturer_obj = product.get("manufacturer", {})
        if isinstance(manufacturer_obj, dict):
            # Handle Microdata format
            if "properties" in manufacturer_obj:
                manufacturer_obj = manufacturer_obj["properties"]
            manufacturer_name = manufacturer_obj.get("name")
            if manufacturer_name:
                return str(manufacturer_name)

        return None

    def _extract_images(self, product: dict[str, Any]) -> list[str]:
        """
        Extract image URLs from product.

        Product may have:
        - image: "url" (single string)
        - image: ["url1", "url2"] (list)
        - images: ["url1", "url2"] (list)

        Args:
            product: Product schema dict

        Returns:
            List of image URLs (primary image only)
        """
        image_data = product.get("image") or product.get("images", [])

        if isinstance(image_data, str):
            return [image_data] if image_data else []
        elif isinstance(image_data, list):
            # Return first valid URL only
            for item in image_data:
                if isinstance(item, str):
                    return [item]
                elif isinstance(item, dict) and "url" in item:
                    return [item["url"]]
            return []
        elif isinstance(image_data, dict) and "url" in image_data:
            return [image_data["url"]]

        return []

    def _extract_specs(self, text: str) -> dict[str, Any]:
        """
        Extract CPU/RAM/storage from text using regex.

        Parses text (description or title) for component specs:
        - CPU: "Intel Core i7-12700K", "AMD Ryzen 7 5800X"
        - RAM: "16GB RAM", "32 GB DDR4"
        - Storage: "512GB SSD", "1TB NVMe"

        Args:
            text: Description or title text

        Returns:
            Dict with cpu_model, ram_gb, storage_gb keys
        """
        specs: dict[str, Any] = {}

        if not text:
            return specs

        # Extract CPU
        cpu_match = CPU_PATTERN.search(text)
        if cpu_match:
            # Get full match to include "Intel" or "AMD" prefix
            specs["cpu_model"] = cpu_match.group(0).strip()

        # Extract Storage first (before RAM to avoid matching RAM as storage)
        # Look for storage-specific keywords
        storage_pattern = re.compile(
            r"(\d+)\s*(GB|TB)\s*(?:SSD|NVMe|HDD|M\.2|SATA|Storage|Drive)",
            re.IGNORECASE,
        )
        storage_match = storage_pattern.search(text)
        if storage_match:
            size = int(storage_match.group(1))
            unit = storage_match.group(2).upper()

            if unit == "TB":
                specs["storage_gb"] = size * 1024
            else:  # GB
                specs["storage_gb"] = size

        # Extract RAM (after storage to avoid conflicts)
        ram_match = RAM_PATTERN.search(text)
        if ram_match:
            specs["ram_gb"] = int(ram_match.group(1))

        return specs


__all__ = ["JsonLdAdapter"]
