"""Maps Schema.org Product data to NormalizedListingSchema."""

import logging
from decimal import Decimal
from typing import Any

from dealbrain_api.adapters.base import AdapterError, AdapterException
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)

EMPTY_PRICE: Decimal = Decimal("0.00")


class SchemaMapper:
    """
    Maps Schema.org Product schema to NormalizedListingSchema.

    Handles:
    - Field extraction and validation
    - Offer normalization (single vs. array)
    - Condition extraction from availability
    - Seller and brand extraction
    - Image URL extraction
    """

    def __init__(
        self,
        price_parser: callable,
        spec_parser: callable,
        image_parser: callable,
    ):
        """
        Initialize schema mapper.

        Args:
            price_parser: Function to parse price strings
            spec_parser: Function to extract specs from text
            image_parser: Function to extract images from product data
        """
        self._parse_price = price_parser
        self._extract_specs = spec_parser
        self._extract_images = image_parser

    def map_to_schema(self, product: dict[str, Any], url: str) -> NormalizedListingSchema:
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
            offers: list[dict[str, Any]] = []

            if offers_raw:
                # Normalize offers to list
                offers = self._normalize_offers(offers_raw)

                # Extract price from offers (take lowest if multiple)
                price, currency = self._extract_price_from_offers(offers)

            # Price is optional - log but continue if missing
            if price is None:
                logger.info(
                    f"Partial extraction from Schema.org: price not found for '{title}', "
                    "continuing with title only (price will be None)."
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
            quality = "partial" if price is None else "full"
            missing_fields = ["price"] if price is None else []

            # Track what was successfully extracted
            extraction_metadata: dict[str, str] = {}
            extracted_fields = {
                "title": title,
                "condition": condition,
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


__all__ = ["SchemaMapper", "EMPTY_PRICE"]
