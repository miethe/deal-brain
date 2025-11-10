"""JSON-LD/Microdata adapter for generic retailer websites."""

from __future__ import annotations

import hashlib
import logging
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
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

EMPTY_PRICE: Decimal = Decimal("0.00")


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

            # All three methods failed - no extractable data found
            raise AdapterException(
                AdapterError.NO_STRUCTURED_DATA,
                "No product data could be extracted from page (no title, price, or other "
                "identifying information found)",
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

            # Initialize price and currency with defaults
            price: Decimal | None = None
            currency = "USD"
            offers: list[dict[str, Any]] = []  # Initialize offers variable

            if offers_raw:
                # Normalize offers to list
                offers = self._normalize_offers(offers_raw)

                # Extract price from offers (take lowest if multiple)
                price, currency = self._extract_price_from_offers(offers)

            # Price is optional - log but continue if missing
            if price is None:
                price = EMPTY_PRICE
                logger.info(
                    f"Partial extraction from Schema.org: price not found for '{title}', "
                    "continuing with title only with price set to $0.00."
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

            # Determine data quality and build extraction metadata
            quality = "partial" if (price is None or price == EMPTY_PRICE) else "full"
            missing_fields = ["price"] if (price is None or price == EMPTY_PRICE) else []

            # Track what was successfully extracted
            extraction_metadata: dict[str, str] = {}
            extracted_fields = {
                "title": title,
                "condition": condition,
                "marketplace": "other",
                "currency": currency,
            }
            if price is not None and price != EMPTY_PRICE:
                extracted_fields["price"] = str(price)
            if images:
                extracted_fields["images"] = ",".join(images)
            if seller:
                extracted_fields["seller"] = seller
            if description:
                extracted_fields["description"] = description
            if specs.get("cpu_model"):
                extracted_fields["cpu_model"] = specs["cpu_model"]
            if specs.get("ram_gb"):
                extracted_fields["ram_gb"] = str(specs["ram_gb"])
            if specs.get("storage_gb"):
                extracted_fields["storage_gb"] = str(specs["storage_gb"])

            # Mark all extracted fields
            for field_name in extracted_fields:
                extraction_metadata[field_name] = "extracted"

            # Mark price as extraction_failed if missing
            if price is None or price == EMPTY_PRICE:
                extraction_metadata["price"] = "extraction_failed"

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
                quality=quality,
                extraction_metadata=extraction_metadata,
                missing_fields=missing_fields,
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

    def _extract_list_price(self, soup: BeautifulSoup) -> Decimal | None:
        """
        Extract list price (original MSRP) from Amazon product page.

        Amazon shows "List Price" or "Was" price separately from deal price.
        This enables pricing context for deal scoring.

        Selectors:
        - span.basisPrice span.aok-offscreen (modern)
        - span.basisPrice span.a-offscreen (legacy)

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List price as Decimal or None if not found
        """
        # Try modern selector first
        basis_price = soup.select_one("span.basisPrice span.aok-offscreen")
        if not basis_price:
            # Fallback to legacy selector
            basis_price = soup.select_one("span.basisPrice span.a-offscreen")

        if basis_price:
            raw_price = basis_price.get_text(strip=True)
            if raw_price:
                # Use existing _parse_price method for consistent handling
                return self._parse_price(raw_price)

        return None

    def _extract_brand(self, soup: BeautifulSoup) -> str | None:
        """
        Extract brand/manufacturer from Amazon product page.

        Extraction strategies (in order):
        1. #bylineInfo link with pattern "Visit the [Brand] Store"
        2. Product title prefix (first word, min 2 chars)

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Brand name string (max 64 chars) or None
        """
        # Strategy 1: Extract from bylineInfo link
        byline = soup.select_one("#bylineInfo")
        if byline:
            text = byline.get_text(strip=True)
            # Pattern: "Visit the [Brand] Store" → extract [Brand]
            match = re.search(r"Visit the (.+?) Store", text)
            if match:
                brand = match.group(1).strip()
                # Truncate to schema max length (64 chars)
                return brand[:64] if len(brand) > 64 else brand

        # Strategy 2: Extract from product title (first word)
        title = soup.select_one("#productTitle")
        if title:
            title_text = title.get_text(strip=True)
            words = title_text.split()
            if words and len(words[0]) > 1:  # Avoid single letters
                brand = words[0]
                return brand[:64] if len(brand) > 64 else brand

        return None

    def _extract_specs_from_table(self, soup: BeautifulSoup) -> dict[str, str]:
        """
        Extract structured specs from Amazon product details table.

        Amazon provides prodDetTable with key-value rows. This is more
        reliable than regex parsing from description text.

        Extracted specs are filtered to relevant components:
        - CPU/Processor
        - RAM/Memory
        - Storage
        - GPU/Graphics

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Dict of normalized spec keys to values (e.g., {"processor": "AMD Ryzen 7"})
        """
        specs: dict[str, str] = {}

        # Find the product details table
        spec_table = soup.select_one("table.prodDetTable")
        if not spec_table:
            return specs

        # Parse each row as key-value pair
        rows = spec_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).rstrip(":")
                value = cells[1].get_text(strip=True)

                # Normalize key names (lowercase, replace spaces with underscores)
                key_normalized = key.lower().replace(" ", "_")

                # Extract only relevant specs
                relevant_terms = ["cpu", "processor", "ram", "memory", "storage", "gpu", "graphics"]
                if any(term in key_normalized for term in relevant_terms):
                    specs[key_normalized] = value

        return specs

    def _extract_images(self, soup: BeautifulSoup) -> list[str]:
        """
        Extract high-resolution product images from Amazon product gallery.

        Extraction methods (in order):
        1. img[data-old-hires] attribute - High-res direct URLs
        2. img[data-a-dynamic-image] attribute - JSON-encoded URL map

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of up to 5 image URLs (all starting with "http")
        """
        images: list[str] = []

        # Primary method: data-old-hires attribute (high-res)
        image_elements = soup.select("img[data-old-hires]")
        if not image_elements:
            # Fallback: data-a-dynamic-image attribute
            image_elements = soup.select("img[data-a-dynamic-image]")

        for img in image_elements:
            # Extract from data-old-hires attribute
            if img.has_attr("data-old-hires"):
                url = img.get("data-old-hires", "")
                url_str = url if isinstance(url, str) else str(url) if url else ""
                if url_str and url_str.startswith("http"):
                    images.append(url_str)
            # Extract from data-a-dynamic-image attribute (JSON encoded)
            elif img.has_attr("data-a-dynamic-image"):
                try:
                    import json

                    dynamic_attr = img.get("data-a-dynamic-image", "{}")
                    dynamic_str = (
                        dynamic_attr
                        if isinstance(dynamic_attr, str)
                        else str(dynamic_attr)
                        if dynamic_attr
                        else "{}"
                    )
                    dynamic_data = json.loads(dynamic_str)
                    # Keys are image URLs, values are dimensions
                    for img_url in dynamic_data.keys():
                        if img_url.startswith("http"):
                            images.append(img_url)
                            break  # Take first/largest image
                except (json.JSONDecodeError, AttributeError):
                    pass

            # Limit to 5 images
            if len(images) >= 5:
                break

        return images[:5]

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
                prop = tag.get("property")
                if prop:
                    # Convert BeautifulSoup attribute value to string
                    prop_str = prop if isinstance(prop, str) else str(prop)
                    content = tag.get("content", "")
                    content_str = content if isinstance(content, str) else str(content)
                    meta_data[prop_str] = content_str
                # Twitter/generic tags (name attribute)
                name = tag.get("name")
                if name:
                    # Convert BeautifulSoup attribute value to string
                    name_str = name if isinstance(name, str) else str(name)
                    content = tag.get("content", "")
                    content_str = content if isinstance(content, str) else str(content)
                    meta_data[name_str] = content_str
                # Microdata tags (itemprop attribute)
                itemprop = tag.get("itemprop")
                if itemprop:
                    # Convert BeautifulSoup attribute value to string
                    itemprop_str = itemprop if isinstance(itemprop, str) else str(itemprop)
                    content = tag.get("content", "")
                    content_str = content if isinstance(content, str) else str(content)
                    meta_data[f"itemprop:{itemprop_str}"] = content_str

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
            # Prioritize OpenGraph and Twitter Card titles over generic meta title
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

            # Validate title is meaningful (not just site name)
            # Reject generic site names but allow short legitimate product titles
            generic_site_names = ["amazon.com", "amazon", "ebay", "ebay.com", "product page"]
            title_lower = title.lower() if title else ""
            is_generic = (
                not title
                or title_lower in generic_site_names
                or "product page" in title_lower  # Catch "Amazon.com Product Page" etc
            )
            if is_generic:
                logger.debug(
                    f"Meta tag extraction failed: title generic or missing ('{title}') for {url}"
                )
                return None

            # Extract price (optional)
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

            # Parse price (may be None)
            price = None
            if price_str:
                price = self._parse_price(price_str)
                logger.debug(f"Price extraction attempt: price_str={price_str}, parsed_price={price}")

            # Price is optional - log but continue if missing
            if not price:
                logger.info(
                    f"Partial extraction from meta tags: price not found for '{title}', "
                    "continuing with title only"
                )

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

            # Determine data quality and build extraction metadata
            quality = "partial" if price is None else "full"
            missing_fields = ["price"] if price is None else []

            # Track what was successfully extracted
            extraction_metadata: dict[str, str] = {}
            extracted_fields = {
                "title": title,
                "condition": Condition.NEW.value,
                "marketplace": "other",
                "currency": currency,
            }
            if price is not None:
                extracted_fields["price"] = str(price)
            if images:
                extracted_fields["images"] = ",".join(images)
            if seller:
                extracted_fields["seller"] = seller
            if description:
                extracted_fields["description"] = description
            if specs.get("cpu_model"):
                extracted_fields["cpu_model"] = specs["cpu_model"]
            if specs.get("ram_gb"):
                extracted_fields["ram_gb"] = str(specs["ram_gb"])
            if specs.get("storage_gb"):
                extracted_fields["storage_gb"] = str(specs["storage_gb"])

            # Mark all extracted fields
            for field_name in extracted_fields:
                extraction_metadata[field_name] = "extracted"

            # Mark price as extraction_failed if missing
            if price is None:
                extraction_metadata["price"] = "extraction_failed"

            # Build normalized schema
            logger.info(
                f"Meta tag extraction successful: title='{title}', "
                f"price={price}, currency={currency}, quality={quality}"
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
                quality=quality,
                extraction_metadata=extraction_metadata,
                missing_fields=missing_fields,
            )

        except Exception as e:
            logger.warning(
                f"Meta tag extraction failed with exception for {url}: {e}", exc_info=True
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

            # Diagnostic logging: HTML structure analysis
            logger.info(f"HTML element extraction diagnostics for {url}:")
            logger.info(f"  HTML length: {len(html)} characters")

            # Check for common bot-blocking indicators
            title_text = soup.find("title")
            title_str = title_text.get_text(strip=True) if title_text else "No title"
            logger.info(f"  Page title: {title_str[:100]}")

            # Check for CAPTCHA indicators
            captcha_indicators = [
                "captcha",
                "robot",
                "automated",
                "verify you are human",
                "unusual traffic",
                "security check",
            ]
            page_text_sample = html[:5000].lower()  # First 5KB
            found_indicators = [ind for ind in captcha_indicators if ind in page_text_sample]
            if found_indicators:
                logger.warning(
                    f"  ⚠️  Potential bot blocking detected! Found indicators: "
                    f"{found_indicators}"
                )

            # Count key elements
            all_spans = soup.find_all("span")
            all_divs = soup.find_all("div")
            all_imgs = soup.find_all("img")
            logger.info(
                f"  Element counts: {len(all_spans)} spans, {len(all_divs)} divs, "
                f"{len(all_imgs)} imgs"
            )

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
                logger.warning("  ❌ Title extraction failed")
                logger.debug(
                    "    Tried selectors: #productTitle, .product-title, " "itemprop='name', h1"
                )

                # Log what title-like elements exist
                h1_tags = soup.find_all("h1", limit=3)
                if h1_tags:
                    h1_texts = [h1.get_text(strip=True)[:50] for h1 in h1_tags]
                    logger.debug(f"    Found {len(h1_tags)} h1 tags: {h1_texts}")
                else:
                    logger.debug("    No h1 tags found")

                self._save_html_for_debugging(html, url)
                return None
            else:
                logger.info(f"  ✓ Title found: {title[:80]}...")

            # Extract price - try multiple common patterns
            price = None
            price_str = None

            # Amazon-specific patterns (priority order based on 2025 research)
            # Priority 1: Desktop core price display with offscreen (updated 2025)
            # Try modern aok-offscreen class first, then legacy a-offscreen
            offscreen_price = soup.select_one(
                "#corePriceDisplay_desktop_feature_div span.aok-offscreen"
            )
            if not offscreen_price:
                offscreen_price = soup.select_one(
                    "#corePriceDisplay_desktop_feature_div span.a-offscreen"
                )
            if offscreen_price:
                price_str = offscreen_price.get_text(strip=True)
                # Validate non-empty to avoid parsing empty elements
                if price_str:
                    price = self._parse_price(price_str)

            # Priority 2: Simple a-price offscreen (direct child, most common)
            if not price:
                offscreen_price = soup.select_one("span.a-price > span.a-offscreen")
                if offscreen_price:
                    price_str = offscreen_price.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Priority 3: Generic a-price offscreen with intermediate wrapper
            if not price:
                offscreen_price = soup.select_one("span.a-price span.a-price-whole span.a-offscreen")
                if offscreen_price:
                    price_str = offscreen_price.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Priority 3: Modern priceToPay selector
            if not price:
                element = soup.select_one("span.priceToPay span.a-offscreen")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Priority 4: Buy box price
            if not price:
                element = soup.select_one("#price_inside_buybox")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Priority 5: Legacy Amazon selectors
            if not price:
                element = soup.select_one("#priceblock_ourprice")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            if not price:
                element = soup.select_one("#priceblock_dealprice")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Priority 6: Visible price with aria-hidden (Amazon modern pattern)
            if not price:
                element = soup.select_one(".a-price span[aria-hidden='true']")
                if element:
                    price_str = element.get_text(strip=True)
                    price = self._parse_price(price_str)

            # Generic patterns as fallbacks
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

            # Price is optional - log but continue if missing
            if not price:
                logger.info(
                    f"Partial extraction from HTML elements: price not found for '{title}', "
                    "continuing with title only"
                )
                logger.debug(
                    "    Tried selectors: #corePriceDisplay_desktop_feature_div .aok-offscreen/.a-offscreen, "
                    ".a-price > .a-offscreen, .priceToPay .a-offscreen, #price_inside_buybox, "
                    "#priceblock_ourprice, #priceblock_dealprice, .a-price span[aria-hidden], "
                    ".price, itemprop='price', .product-price"
                )

                # Log what price-like elements exist for debugging
                a_price_spans = soup.select("span.a-price")
                if a_price_spans:
                    logger.debug(f"    Found {len(a_price_spans)} span.a-price elements")

                # Find spans with 'price' in class name - need to handle BeautifulSoup attribute types
                def has_price_in_class(class_attr: str | list[str] | None) -> bool:
                    """Check if 'price' appears in any class name."""
                    if class_attr is None:
                        return False
                    if isinstance(class_attr, str):
                        return "price" in class_attr.lower()
                    if isinstance(class_attr, list):
                        return any("price" in c.lower() for c in class_attr if isinstance(c, str))
                    return False

                price_like_spans = soup.find_all("span", class_=has_price_in_class, limit=5)
                if price_like_spans:
                    logger.debug(
                        f"    Found {len(price_like_spans)} spans with 'price' in " "class name"
                    )
                    for span in price_like_spans[:3]:
                        span_text = span.get_text(strip=True)[:50]
                        # Convert BeautifulSoup attribute value to string for logging
                        class_attr = span.get("class")
                        class_str = str(class_attr) if class_attr else "None"
                        logger.debug(f"      - {class_str}: {span_text}")

                # Save HTML for debugging only if in debug mode
                if logger.isEnabledFor(logging.DEBUG):
                    self._save_html_for_debugging(html, url)
            else:
                logger.info(f"  ✓ Price found: {price}")

            # Extract list price (original MSRP) - Amazon-specific
            list_price = self._extract_list_price(soup)
            if list_price:
                logger.info(f"  ✓ List price found: {list_price}")

            # Extract brand/manufacturer - Amazon-specific
            brand = self._extract_brand(soup)
            if brand:
                logger.info(f"  ✓ Brand found: {brand}")

            # Extract images using enhanced extractor
            images = self._extract_images(soup)
            if not images:
                # Fallback to legacy method for non-Amazon sites
                img_tag = soup.select_one(
                    "img[data-old-hires], img[data-a-image-name], img.product-image"
                )

                if not img_tag:
                    # Fallback to first reasonable-sized img
                    all_imgs = soup.find_all("img", src=True)
                    for img in all_imgs:
                        src_attr = img.get("src", "")
                        # Convert BeautifulSoup attribute value to string
                        src = src_attr if isinstance(src_attr, str) else str(src_attr) if src_attr else ""
                        # Skip tiny images (icons, spacers)
                        if src and "1x1" not in src and "pixel" not in src.lower():
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

            if images:
                logger.info(f"  ✓ Images found: {len(images)} image(s)")

            # Extract description from meta description as fallback
            description: str | None = None
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                content_attr = meta_desc.get("content", "")
                # Convert BeautifulSoup attribute value to string
                if isinstance(content_attr, str):
                    description = content_attr
                elif content_attr:
                    description = str(content_attr)

            # Extract specs from product details table (Amazon-specific, more reliable)
            table_specs = self._extract_specs_from_table(soup)

            # Fallback to regex extraction from title + description if table is empty
            desc_str = description if description else ""
            regex_specs = self._extract_specs((title or "") + " " + desc_str)

            # Merge specs: prefer table extraction, fallback to regex
            specs = {**regex_specs, **table_specs}  # table_specs overwrites regex_specs

            if table_specs:
                logger.info(f"  ✓ Specs from table: {list(table_specs.keys())}")
            if regex_specs and not table_specs:
                logger.info(f"  ✓ Specs from regex: {list(regex_specs.keys())}")

            # Determine data quality and build extraction metadata
            quality = "partial" if price is None else "full"
            missing_fields = ["price"] if price is None else []

            # Track what was successfully extracted
            extraction_metadata: dict[str, str] = {}
            extracted_fields = {
                "title": title,
                "condition": str(Condition.NEW.value),
                "marketplace": "other",
                "currency": "USD",
            }
            if price is not None:
                extracted_fields["price"] = str(price)
            if list_price is not None:
                extracted_fields["list_price"] = str(list_price)
            if brand:
                extracted_fields["manufacturer"] = brand
            if images:
                extracted_fields["images"] = ",".join(images)
            if description:
                extracted_fields["description"] = description
            if specs.get("cpu_model"):
                extracted_fields["cpu_model"] = specs["cpu_model"]
            if specs.get("ram_gb"):
                extracted_fields["ram_gb"] = str(specs["ram_gb"])
            if specs.get("storage_gb"):
                extracted_fields["storage_gb"] = str(specs["storage_gb"])

            # Mark all extracted fields
            for field_name in extracted_fields:
                extraction_metadata[field_name] = "extracted"

            # Store raw table specs in extraction_metadata for reference
            if table_specs:
                import json
                extraction_metadata["specs_raw"] = json.dumps(table_specs)

            # Mark price as extraction_failed if missing
            if price is None:
                extraction_metadata["price"] = "extraction_failed"

            logger.info(
                f"Successfully extracted listing from HTML elements: "
                f"title={title[:50]}..., price={price}, quality={quality}"
            )

            # Build normalized schema
            return NormalizedListingSchema(
                title=title,
                price=price,
                list_price=list_price,  # New field for original MSRP
                currency="USD",  # Default, could be enhanced to detect from page
                condition=str(Condition.NEW.value),  # Default
                images=images,
                seller=None,  # Not easily extractable from HTML
                marketplace="other",
                vendor_item_id=None,
                description=description,
                manufacturer=brand,  # New field for brand/manufacturer
                cpu_model=specs.get("cpu_model"),
                ram_gb=specs.get("ram_gb"),
                storage_gb=specs.get("storage_gb"),
                quality=quality,
                extraction_metadata=extraction_metadata,
                missing_fields=missing_fields,
            )

        except Exception as e:
            logger.warning(f"HTML element extraction exception for {url}: {e}")
            return None

    def _save_html_for_debugging(self, html: str, url: str) -> None:
        """
        Save HTML to a temporary file for manual inspection during debugging.

        Only called when extraction fails and DEBUG logging is enabled.
        Helps diagnose bot blocking and HTML structure issues.

        Args:
            html: HTML content to save
            url: URL the HTML was fetched from
        """
        # Only save if DEBUG logging enabled
        if not logger.isEnabledFor(logging.DEBUG):
            return

        try:
            # Create debug directory
            # S108: Using /tmp is acceptable for debug-only diagnostic files
            debug_dir = Path("/tmp/dealbrain_adapter_debug")  # noqa: S108
            debug_dir.mkdir(exist_ok=True)

            # Generate filename from URL hash
            # S324: MD5 is acceptable for non-security filename generation
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]  # noqa: S324
            filename = f"amazon_{url_hash}.html"
            filepath = debug_dir / filename

            # Save HTML
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            logger.debug(f"  📁 Saved HTML to {filepath} for manual inspection")
            logger.debug(f"     Open in browser: file://{filepath}")

        except Exception as e:
            logger.debug(f"  Failed to save HTML for debugging: {e}")


__all__ = ["JsonLdAdapter"]
