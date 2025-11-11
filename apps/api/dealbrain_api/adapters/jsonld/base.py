"""Main JSON-LD adapter class with orchestration logic."""

import logging

from dealbrain_api.adapters.base import AdapterError, AdapterException, BaseAdapter
from dealbrain_api.settings import get_settings
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

from .extractors import HtmlElementExtractor, MetaTagExtractor, StructuredDataExtractor
from .normalizers import SchemaMapper
from .parsers import ImageParser, PriceParser, SpecParser

logger = logging.getLogger(__name__)


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

        # Initialize extractors with dependencies
        self._structured_data_extractor = StructuredDataExtractor(
            timeout_s=self.timeout_s,
            rate_limiter_check=self._check_rate_limit,
        )

        self._meta_tag_extractor = MetaTagExtractor(
            price_parser=PriceParser.parse_price,
            spec_parser=SpecParser.extract_specs,
        )

        self._html_element_extractor = HtmlElementExtractor(
            price_parser=PriceParser.parse_price,
            spec_parser=SpecParser.extract_specs,
            image_parser=ImageParser.extract_images_from_html,
            brand_parser=SpecParser.extract_brand,
            list_price_parser=PriceParser.extract_list_price,
            table_spec_parser=SpecParser.extract_specs_from_table,
        )

        # Initialize schema mapper
        self._schema_mapper = SchemaMapper(
            price_parser=PriceParser.parse_price,
            spec_parser=SpecParser.extract_specs,
            image_parser=ImageParser.extract_images_from_product,
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

        # Step 1: Fetch HTML (use wrapper for test compatibility)
        html = await self._fetch_html(url)

        # Step 2: Extract structured data
        structured_data = self._structured_data_extractor.extract_structured_data(html, url)

        # Step 3: Find Product schema (use wrapper for test compatibility)
        product_data = self._find_product_schema(structured_data)

        if not product_data:
            # Fallback 1: Try extracting from meta tags (OpenGraph, Twitter Card) (use wrapper for test compatibility)
            logger.info(f"📋 No Schema.org Product found, trying meta tag fallback for {url}")
            result = self._extract_from_meta_tags(html, url)

            if result:
                logger.info(f"✅ Successfully extracted listing from meta tags: {result.title}")
                return result

            # Fallback 2: Try extracting from HTML elements (Amazon-style) (use wrapper for test compatibility)
            logger.info(f"🔍 No meta tags found, trying HTML element fallback for {url}")
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

        # Step 4: Map to normalized schema (use wrapper for test compatibility)
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

    # ==================================================================================
    # Backward Compatibility Wrappers for Tests
    # ==================================================================================
    # The following methods provide backward compatibility with existing tests that
    # expect these methods to exist on the adapter instance. They delegate to the
    # appropriate sub-components.

    async def _fetch_html(self, url: str) -> str:
        """Compatibility wrapper for _fetch_html (delegates to extractor)."""
        return await self._structured_data_extractor.fetch_html(url)

    def _find_product_schema(self, data: dict) -> dict | None:
        """Compatibility wrapper for _find_product_schema (delegates to extractor)."""
        return self._structured_data_extractor.find_product_schema(data)

    def _is_product_schema(self, item: dict) -> bool:
        """Compatibility wrapper for _is_product_schema (delegates to extractor)."""
        return self._structured_data_extractor._is_product_schema(item)

    def _map_to_schema(self, product: dict, url: str):
        """Compatibility wrapper for _map_to_schema (delegates to mapper)."""
        return self._schema_mapper.map_to_schema(product, url)

    def _normalize_offers(self, offers_raw):
        """Compatibility wrapper for _normalize_offers (delegates to mapper)."""
        return self._schema_mapper._normalize_offers(offers_raw)

    def _extract_price_from_offers(self, offers: list):
        """Compatibility wrapper for _extract_price_from_offers (delegates to mapper)."""
        return self._schema_mapper._extract_price_from_offers(offers)

    def _parse_price(self, price):
        """Compatibility wrapper for _parse_price (delegates to parser)."""
        return PriceParser.parse_price(price)

    def _extract_condition_from_offers(self, offers: list) -> str:
        """Compatibility wrapper for _extract_condition_from_offers (delegates to mapper)."""
        return self._schema_mapper._extract_condition_from_offers(offers)

    def _extract_seller(self, product: dict, offers: list):
        """Compatibility wrapper for _extract_seller (delegates to mapper)."""
        return self._schema_mapper._extract_seller(product, offers)

    def _extract_images(self, product_or_soup) -> list[str]:
        """Compatibility wrapper for _extract_images (delegates to parser based on input type)."""
        # Check if input is BeautifulSoup (HTML extraction) or dict (Product schema)
        from bs4 import BeautifulSoup

        if isinstance(product_or_soup, BeautifulSoup):
            return ImageParser.extract_images_from_html(product_or_soup)
        else:
            return ImageParser.extract_images_from_product(product_or_soup)

    def _extract_specs(self, text: str) -> dict:
        """Compatibility wrapper for _extract_specs (delegates to parser)."""
        return SpecParser.extract_specs(text)

    def _extract_from_meta_tags(self, html: str, url: str):
        """Compatibility wrapper for _extract_from_meta_tags (delegates to extractor)."""
        return self._meta_tag_extractor.extract_from_meta_tags(html, url)

    def _extract_from_html_elements(self, html: str, url: str):
        """Compatibility wrapper for _extract_from_html_elements (delegates to extractor)."""
        return self._html_element_extractor.extract_from_html_elements(html, url)

    def _extract_brand(self, soup):
        """Compatibility wrapper for _extract_brand (delegates to parser)."""
        return SpecParser.extract_brand(soup)

    def _extract_list_price(self, soup):
        """Compatibility wrapper for _extract_list_price (delegates to parser)."""
        return PriceParser.extract_list_price(soup)

    def _extract_specs_from_table(self, soup):
        """Compatibility wrapper for _extract_specs_from_table (delegates to parser)."""
        return SpecParser.extract_specs_from_table(soup)


__all__ = ["JsonLdAdapter"]
