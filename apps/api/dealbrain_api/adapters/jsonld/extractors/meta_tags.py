"""Meta tag extraction for OpenGraph and Twitter Card data."""

import logging

from bs4 import BeautifulSoup
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)


class MetaTagExtractor:
    """
    Extracts product data from OpenGraph and Twitter Card meta tags.

    When Schema.org structured data is not available, this extractor attempts to
    extract listing information from standard meta tags that many sites include:
    - OpenGraph (og:*) - Used by Facebook and widely adopted
    - Twitter Card (twitter:*) - Used by Twitter
    - Generic meta tags (name="description", itemprop="price", etc.)

    Priority order:
    1. OpenGraph tags (highest priority)
    2. Twitter Card tags
    3. Generic meta tags
    """

    def __init__(self, price_parser: callable, spec_parser: callable):
        """
        Initialize meta tag extractor.

        Args:
            price_parser: Function to parse price strings
            spec_parser: Function to extract specs from text
        """
        self._parse_price = price_parser
        self._extract_specs = spec_parser

    def extract_from_meta_tags(self, html: str, url: str) -> NormalizedListingSchema | None:
        """
        Extract product data from OpenGraph/Twitter Card meta tags as fallback.

        Required fields for successful extraction:
        - Title (from og:title, twitter:title, or title tag)

        Optional fields:
        - Price (from og:price:amount, itemprop="price", or price-containing meta)
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
                    prop_str = prop if isinstance(prop, str) else str(prop)
                    content = tag.get("content", "")
                    content_str = content if isinstance(content, str) else str(content)
                    meta_data[prop_str] = content_str
                # Twitter/generic tags (name attribute)
                name = tag.get("name")
                if name:
                    name_str = name if isinstance(name, str) else str(name)
                    content = tag.get("content", "")
                    content_str = content if isinstance(content, str) else str(content)
                    meta_data[name_str] = content_str
                # Microdata tags (itemprop attribute)
                itemprop = tag.get("itemprop")
                if itemprop:
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
            generic_site_names = ["amazon.com", "amazon", "ebay", "ebay.com", "product page"]
            title_lower = title.lower() if title else ""
            is_generic = (
                not title
                or title_lower in generic_site_names
                or "product page" in title_lower
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
                marketplace="other",
                vendor_item_id=None,
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


__all__ = ["MetaTagExtractor"]
