"""JSON-LD/Microdata adapter for generic retailer websites."""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

import extruct
import httpx
from bs4 import BeautifulSoup
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

    Extraction Strategy (Three-Tier Fallback):
    ------------------------------------------
    1. Schema.org structured data (JSON-LD, Microdata, RDFa) - Primary method
    2. Meta tags (OpenGraph, Twitter Card) - First fallback
    3. HTML elements (direct element parsing) - Final fallback

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

    HTML Element Fallback:
    ---------------------
    For sites like Amazon that don't use structured data or meta tags:
    - Title: #productTitle, .product-title, itemprop="name", or first h1
    - Price: span.a-price > span.a-offscreen (Amazon), .price, itemprop="price"
    - Images: data-old-hires, data-a-image-source, or first non-1x1 img
    - Description: meta[name="description"] tag

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
    - NO_STRUCTURED_DATA: No Product schema, meta tags, or HTML elements found
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
            # Fallback 1: Try extracting from meta tags (OpenGraph, Twitter Card)
            logger.info(f"No Schema.org Product found, trying meta tag fallback for {url}")
            result = self._extract_from_meta_tags(html, url)

            if result:
                logger.info(f"Successfully extracted listing from meta tags: {result.title}")
                return result

            # Fallback 2: Try extracting from HTML elements (Amazon-style)
            logger.info(f"No meta tags found, trying HTML element fallback for {url}")
            result = self._extract_from_html_elements(html, url)

            if result:
                logger.info(f"Successfully extracted listing from HTML elements: {result.title}")
                return result

            # All three methods failed
            raise AdapterException(
                AdapterError.NO_STRUCTURED_DATA,
                "No Schema.org Product data, extractable meta tags, or HTML elements found in page",
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

    def _extract_from_meta_tags(self, html: str, url: str) -> NormalizedListingSchema | None:
        """
        Extract product data from OpenGraph/Twitter Card meta tags as fallback.

        When Schema.org structured data is not available, this method attempts to
        extract listing information from standard meta tags that many sites include:
        - OpenGraph (og:*) - Used by Facebook and widely adopted
        - Twitter Card (twitter:*) - Used by Twitter
        - Generic meta tags (name="description", itemprop="price", etc.)

        Priority order:
        1. OpenGraph tags (highest priority)
        2. Twitter Card tags
        3. Generic meta tags

        Required fields for successful extraction:
        - Title (from og:title, twitter:title, or title tag)
        - Price (from og:price:amount, itemprop="price", or price-containing meta)

        Optional fields:
        - Currency (from og:price:currency, defaults to USD)
        - Images (from og:image or twitter:image)
        - Description (from og:description, twitter:description, or meta description)

        Args:
            html: HTML content to parse
            url: Original URL (for error messages and logging)

        Returns:
            NormalizedListingSchema with extracted data, or None if insufficient data
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            meta_tags = soup.find_all("meta")

            # Build meta data dictionary
            meta_data: dict[str, str] = {}
            for tag in meta_tags:
                # OpenGraph tags (property attribute)
                if tag.get("property"):
                    meta_data[tag["property"]] = tag.get("content", "")
                # Twitter/generic tags (name attribute)
                if tag.get("name"):
                    meta_data[tag["name"]] = tag.get("content", "")
                # Microdata tags (itemprop attribute)
                if tag.get("itemprop"):
                    meta_data[f"itemprop:{tag['itemprop']}"] = tag.get("content", "")

            # Debug logging: show what meta tags were found
            logger.debug(f"Meta tag extraction debug for {url}:")
            logger.debug(f"  Total meta tags found: {len(meta_tags)}")
            logger.debug(f"  Meta data keys: {list(meta_data.keys())}")

            # Log a sample of meta content for debugging
            if meta_data:
                sample_keys = list(meta_data.keys())[:10]
                for key in sample_keys:
                    value = meta_data[key][:100] if len(meta_data[key]) > 100 else meta_data[key]
                    logger.debug(f"  {key}: {value}")
            else:
                logger.warning(f"No meta tags found in HTML for {url}")

            # Extract title (required)
            title = (
                meta_data.get("og:title")
                or meta_data.get("twitter:title")
                or meta_data.get("title")
            )

            # Fallback to <title> tag if no meta title found
            if not title:
                title_tag = soup.find("title")
                if title_tag and title_tag.string:
                    title = title_tag.string.strip()

            logger.debug(f"Title extraction attempt: title={title}")

            if not title:
                logger.debug(f"Meta tag extraction failed: no title found for {url}")
                return None

            # Extract price (required)
            price_str = (
                meta_data.get("og:price:amount")
                or meta_data.get("itemprop:price")
                or meta_data.get("price")
            )

            # Try to find price in various meta tags if not found
            if not price_str:
                for key, value in meta_data.items():
                    if "price" in key.lower() and value:
                        price_str = value
                        break

            if not price_str:
                logger.debug(f"Meta tag extraction failed: no price found for {url}")
                return None

            # Parse price
            price = self._parse_price(price_str)

            logger.debug(f"Price extraction attempt: price_str={price_str}, parsed_price={price}")

            if not price:
                logger.debug(
                    f"Meta tag extraction failed: could not parse price '{price_str}' for {url}"
                )
                return None

            # Extract currency (optional, defaults to USD)
            currency = meta_data.get("og:price:currency") or meta_data.get("currency") or "USD"

            # Extract images (optional)
            images: list[str] = []
            image_url = (
                meta_data.get("og:image")
                or meta_data.get("twitter:image")
                or meta_data.get("itemprop:image")
            )
            if image_url:
                images = [image_url]

            # Extract description (optional)
            description = (
                meta_data.get("og:description")
                or meta_data.get("twitter:description")
                or meta_data.get("description")
            )

            # Parse specs from title + description
            specs_text = f"{title} {description or ''}"
            specs = self._extract_specs(specs_text)

            # Extract seller (optional)
            seller = (
                meta_data.get("og:site_name")
                or meta_data.get("twitter:site")
                or meta_data.get("author")
            )

            # Build normalized schema
            logger.info(
                f"Meta tag extraction successful: title='{title}', "
                f"price={price}, currency={currency}"
            )

            return NormalizedListingSchema(
                title=title,
                price=price,
                currency=currency,
                condition=Condition.NEW.value,  # Default, meta tags rarely specify condition
                images=images,
                seller=seller,
                marketplace="other",  # Generic marketplace
                vendor_item_id=None,  # Not available from meta tags
                description=description,
                cpu_model=specs.get("cpu_model"),
                ram_gb=specs.get("ram_gb"),
                storage_gb=specs.get("storage_gb"),
            )

        except Exception as e:
            logger.warning(
                f"Meta tag extraction failed with exception for {url}: {e}", exc_info=True
            )
            # Log extraction failure summary
            logger.info(
                f"Meta tag extraction failed for {url}: "
                f"title={'present' if 'title' in locals() else 'missing'}, "
                f"price={'present' if 'price' in locals() and price else 'missing'}"
            )
            return None

    def _extract_from_html_elements(self, html: str, url: str) -> NormalizedListingSchema | None:
        """
        Extract product data from HTML elements as final fallback.

        This method targets sites like Amazon that don't use meta tags or structured
        data, but have predictable HTML element patterns. It looks for:

        - Title: Common patterns like #productTitle, h1.product-title, etc.
        - Price: Common patterns like .a-price > .a-offscreen, .price, etc.
        - Images: First large img tag in product area

        Args:
            html: HTML content to parse
            url: Original URL (for error messages and logging)

        Returns:
            NormalizedListingSchema with extracted data, or None if insufficient data
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract title - try multiple common patterns
            title = None

            # Amazon: #productTitle
            element = soup.find(id="productTitle")
            if element:
                title = element.get_text(strip=True)

            # Generic: .product-title
            if not title:
                element = soup.find(class_="product-title")
                if element:
                    title = element.get_text(strip=True)

            # Schema.org microdata: itemprop="name"
            if not title:
                element = soup.find(attrs={"itemprop": "name"})  # type: ignore[arg-type]
                if element:
                    title = element.get_text(strip=True)

            # Fallback to first h1 if no title found
            if not title:
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

            if not title:
                logger.debug(f"HTML element extraction failed: no title found for {url}")
                return None

            # Extract price - try multiple common patterns
            price = None
            price_str = None

            # Amazon pattern: span.a-price > span.a-offscreen
            offscreen_price = soup.select_one("span.a-price span.a-offscreen")
            if offscreen_price:
                price_str = offscreen_price.get_text(strip=True)
                price = self._parse_price(price_str)

            # Generic patterns if Amazon pattern fails
            if not price:
                # Try .price class
                element = soup.find(class_="price")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Try itemprop="price"
            if not price:
                element = soup.find(attrs={"itemprop": "price"})  # type: ignore[arg-type]
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Try .product-price class
            if not price:
                element = soup.find(class_="product-price")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            if not price:
                logger.debug(
                    f"HTML element extraction failed: no price found for {url}, "
                    f"tried offscreen_price, .price, itemprop='price', and .product-price patterns"
                )
                return None

            # Extract images - look for product images
            images = []
            img_tag = soup.select_one(
                "img[data-old-hires], img[data-a-image-name], img.product-image"
            )

            if not img_tag:
                # Fallback to first reasonable-sized img
                all_imgs = soup.find_all("img", src=True)
                for img in all_imgs:
                    src = img.get("src", "")
                    # Skip tiny images (icons, spacers)
                    if "1x1" not in src and "pixel" not in src.lower():
                        img_tag = img
                        break

            if img_tag:
                img_src = (
                    img_tag.get("data-old-hires")
                    or img_tag.get("data-a-image-source")
                    or img_tag.get("src")
                )
                if img_src and isinstance(img_src, str):
                    images = [img_src]

            # Extract description from meta description as fallback
            description = None
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")

            # Extract specs from title + description
            specs = self._extract_specs((title or "") + " " + (description or ""))

            logger.info(
                f"Successfully extracted listing from HTML elements: "
                f"title={title[:50]}..., price={price}"
            )

            # Build normalized schema
            return NormalizedListingSchema(
                title=title,
                price=price,
                currency="USD",  # Default, could be enhanced to detect from page
                condition=str(Condition.NEW.value),  # Default
                images=images,
                seller=None,  # Not easily extractable from HTML
                marketplace="other",
                vendor_item_id=None,
                description=description,
                cpu_model=specs.get("cpu_model"),
                ram_gb=specs.get("ram_gb"),
                storage_gb=specs.get("storage_gb"),
            )

        except Exception as e:
            logger.warning(f"HTML element extraction exception for {url}: {e}")
            return None


__all__ = ["JsonLdAdapter"]
