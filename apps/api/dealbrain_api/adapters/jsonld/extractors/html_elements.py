"""HTML element extraction for sites without structured data or meta tags."""

import hashlib
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from dealbrain_core.enums import Condition
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)


class HtmlElementExtractor:
    """
    Extracts product data from HTML elements as final fallback.

    This extractor targets sites like Amazon that don't use meta tags or structured
    data, but have predictable HTML element patterns. It looks for:

    - Title: Common patterns like #productTitle, h1.product-title, etc.
    - Price: Common patterns like .a-price > .a-offscreen, .price, etc.
    - Images: First large img tag in product area
    - Brand: Manufacturer/brand from byline or title
    - Specs: Product details table or regex extraction
    """

    def __init__(
        self,
        price_parser: callable,
        spec_parser: callable,
        image_parser: callable,
        brand_parser: callable,
        list_price_parser: callable,
        table_spec_parser: callable,
    ):
        """
        Initialize HTML element extractor.

        Args:
            price_parser: Function to parse price strings
            spec_parser: Function to extract specs from text
            image_parser: Function to extract images from HTML
            brand_parser: Function to extract brand from HTML
            list_price_parser: Function to extract list price from HTML
            table_spec_parser: Function to extract specs from table
        """
        self._parse_price = price_parser
        self._extract_specs = spec_parser
        self._extract_images = image_parser
        self._extract_brand = brand_parser
        self._extract_list_price = list_price_parser
        self._extract_specs_from_table = table_spec_parser

    def extract_from_html_elements(self, html: str, url: str) -> NormalizedListingSchema | None:
        """
        Extract product data from HTML elements as final fallback.

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
            title = self._extract_title(soup, url, html)
            if not title:
                return None

            logger.info(f"  ✓ Title found: {title[:80]}...")

            # Extract price - try multiple common patterns
            price = self._extract_price(soup, title, url, html)
            if price:
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
                images = self._extract_images_fallback(soup)

            if images:
                logger.info(f"  ✓ Images found: {len(images)} image(s)")

            # Extract description from meta description as fallback
            description = self._extract_description(soup)

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
                list_price=list_price,
                currency="USD",
                condition=str(Condition.NEW.value),
                images=images,
                seller=None,
                marketplace="other",
                vendor_item_id=None,
                description=description,
                manufacturer=brand,
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

    def _extract_title(self, soup: BeautifulSoup, url: str, html: str) -> str | None:
        """
        Extract title from HTML using multiple strategies.

        Args:
            soup: BeautifulSoup parsed HTML
            url: Original URL
            html: Raw HTML content

        Returns:
            Title string or None if not found
        """
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

        return title

    def _extract_price(self, soup: BeautifulSoup, title: str, url: str, html: str) -> float | None:
        """
        Extract price from HTML using multiple strategies.

        Tries Amazon-specific selectors first, then generic patterns.

        Args:
            soup: BeautifulSoup parsed HTML
            title: Product title
            url: Original URL
            html: Raw HTML content

        Returns:
            Price as Decimal or None if not found
        """
        price = None
        price_str = None

        # Amazon-specific patterns (priority order based on 2025 research)
        # Priority 1a: aok-offscreen class (Amazon 2025 update)
        logger.debug("  [Price] Testing Priority 1a: span.aok-offscreen (first occurrence)")
        aok_offscreen_price = soup.select_one("span.aok-offscreen")
        if aok_offscreen_price:
            price_str = aok_offscreen_price.get_text(strip=True)
            logger.debug(f"  [Price]   Found element, text='{price_str}' (length={len(price_str)})")
            if price_str:
                price = self._parse_price(price_str)
                if price:
                    logger.info(f"  [Price]   ✓ Priority 1a SUCCESS: parsed price={price}")
                else:
                    logger.debug(f"  [Price]   Failed to parse price from '{price_str}'")
            else:
                logger.debug("  [Price]   Element text is empty, skipping to next priority")
        else:
            logger.debug("  [Price]   No span.aok-offscreen found")

        # Priority 1b: Desktop core price display with offscreen
        if not price:
            logger.debug(
                "  [Price] Testing Priority 1b: #corePriceDisplay_desktop_feature_div span.aok-offscreen"
            )
            offscreen_price = soup.select_one(
                "#corePriceDisplay_desktop_feature_div span.aok-offscreen"
            )
            if not offscreen_price:
                logger.debug("  [Price]   aok-offscreen not found, trying a-offscreen")
                offscreen_price = soup.select_one(
                    "#corePriceDisplay_desktop_feature_div span.a-offscreen"
                )
            if offscreen_price:
                price_str = offscreen_price.get_text(strip=True)
                logger.debug(
                    f"  [Price]   Found element, text='{price_str}' (length={len(price_str)})"
                )
                if price_str:
                    price = self._parse_price(price_str)
                    if price:
                        logger.info(f"  [Price]   ✓ Priority 1b SUCCESS: parsed price={price}")
                    else:
                        logger.debug(f"  [Price]   Failed to parse price from '{price_str}'")
                else:
                    logger.debug("  [Price]   Element text is empty, skipping to next priority")
            else:
                logger.debug("  [Price]   No element found for Priority 1b")

        # Priority 2a: tp_price_block (Amazon 2024-2025 pattern)
        if not price:
            logger.debug(
                "  [Price] Testing Priority 2a: #tp_price_block_total_price_ww span.a-offscreen"
            )
            tp_price = soup.select_one("#tp_price_block_total_price_ww span.a-offscreen")
            if tp_price:
                price_str = tp_price.get_text(strip=True)
                logger.debug(
                    f"  [Price]   Found element, text='{price_str}' (length={len(price_str)})"
                )
                if price_str:
                    price = self._parse_price(price_str)
                    if price:
                        logger.info(f"  [Price]   ✓ Priority 2a SUCCESS: parsed price={price}")
                    else:
                        logger.debug(f"  [Price]   Failed to parse price from '{price_str}'")
                else:
                    logger.debug("  [Price]   Element text is empty, skipping")
            else:
                logger.debug("  [Price]   No #tp_price_block_total_price_ww found")

        # Priority 2b: Simple a-price offscreen (most common)
        if not price:
            logger.debug("  [Price] Testing Priority 2b: span.a-price > span.a-offscreen")
            offscreen_price = soup.select_one("span.a-price > span.a-offscreen")
            if offscreen_price:
                price_str = offscreen_price.get_text(strip=True)
                logger.debug(
                    f"  [Price]   Found element, text='{price_str}' (length={len(price_str)})"
                )
                if price_str:
                    price = self._parse_price(price_str)
                    if price:
                        logger.info(f"  [Price]   ✓ Priority 2b SUCCESS: parsed price={price}")
                    else:
                        logger.debug(f"  [Price]   Failed to parse price from '{price_str}'")
                else:
                    logger.debug("  [Price]   Element text is empty, skipping")
            else:
                logger.debug("  [Price]   No element found for Priority 2b")

        # Continue with remaining priority levels...
        if not price:
            price = self._try_remaining_price_selectors(soup)

        # Price extraction summary
        if not price:
            logger.warning(f"  [Price] ❌ FAILED TO EXTRACT PRICE for '{title}'")
            self._log_price_extraction_failure(soup, url, html)
        else:
            logger.info(f"  ✓ Price found: {price}")

        return price

    def _try_remaining_price_selectors(self, soup: BeautifulSoup) -> float | None:
        """Try remaining price selector patterns (Priority 3+)."""
        price = None

        # Priority 3a: Generic a-price offscreen with intermediate wrapper
        logger.debug(
            "  [Price] Testing Priority 3a: span.a-price span.a-price-whole span.a-offscreen"
        )
        element = soup.select_one("span.a-price span.a-price-whole span.a-offscreen")
        if element:
            price_str = element.get_text(strip=True)
            if price_str:
                price = self._parse_price(price_str)
                if price:
                    logger.info(f"  [Price]   ✓ Priority 3a SUCCESS: parsed price={price}")
                    return price

        # Priority 3b: Modern priceToPay selector
        if not price:
            element = soup.select_one("span.priceToPay span.a-offscreen")
            if element:
                price_str = element.get_text(strip=True)
                if price_str:
                    price = self._parse_price(price_str)
                    if price:
                        return price

        # Priority 4-6: Legacy and generic patterns
        legacy_selectors = [
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
        ]

        for selector in legacy_selectors:
            element = soup.select_one(selector)
            if element:
                price_str = element.get_text(strip=True)
                price = self._parse_price(price_str)
                if price:
                    return price

        # Try aria-hidden pattern
        element = soup.select_one(".a-price span[aria-hidden='true']")
        if element:
            price_str = element.get_text(strip=True)
            price = self._parse_price(price_str)
            if price:
                return price

        # Generic patterns
        generic_selectors = [
            ("class", "price"),
            ("itemprop", "price"),
            ("class", "product-price"),
        ]

        for attr_type, attr_value in generic_selectors:
            if attr_type == "class":
                element = soup.find(class_=attr_value)
            else:
                element = soup.find(attrs={attr_type: attr_value})  # type: ignore[arg-type]

            if element:
                price_str = element.get_text(strip=True)
                price = self._parse_price(price_str)
                if price:
                    return price

        return None

    def _log_price_extraction_failure(self, soup: BeautifulSoup, url: str, html: str) -> None:
        """Log details about price extraction failure for debugging."""
        logger.warning(
            "  [Price] All selectors tried: Priority 1 (#corePriceDisplay .aok-offscreen/.a-offscreen), "
            "Priority 2 (span.a-price > span.a-offscreen), Priority 3a (span.a-price span.a-price-whole span.a-offscreen), "
            "Priority 3b (span.priceToPay span.a-offscreen), Priority 4 (#price_inside_buybox), "
            "Priority 5 (#priceblock_ourprice, #priceblock_dealprice), Priority 6 (.a-price span[aria-hidden]), "
            "Generic (.price, itemprop='price', .product-price)"
        )

        # Log what price-like elements exist
        a_price_spans = soup.select("span.a-price")
        if a_price_spans:
            logger.debug(f"    Found {len(a_price_spans)} span.a-price elements")

        # Find spans with 'price' in class name
        def has_price_in_class(class_attr: str | list[str] | None) -> bool:
            if class_attr is None:
                return False
            if isinstance(class_attr, str):
                return "price" in class_attr.lower()
            if isinstance(class_attr, list):
                return any("price" in c.lower() for c in class_attr if isinstance(c, str))
            return False

        price_like_spans = soup.find_all("span", class_=has_price_in_class, limit=5)
        if price_like_spans:
            logger.debug(f"    Found {len(price_like_spans)} spans with 'price' in class name")
            for span in price_like_spans[:3]:
                span_text = span.get_text(strip=True)[:50]
                class_attr = span.get("class")
                class_str = str(class_attr) if class_attr else "None"
                logger.debug(f"      - {class_str}: {span_text}")

        # Save HTML for debugging only if in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            self._save_html_for_debugging(html, url)

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        """Extract description from meta description tag."""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            content_attr = meta_desc.get("content", "")
            if isinstance(content_attr, str):
                return content_attr
            elif content_attr:
                return str(content_attr)
        return None

    def _extract_images_fallback(self, soup: BeautifulSoup) -> list[str]:
        """
        Fallback image extraction for non-Amazon sites.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of image URLs
        """
        images: list[str] = []

        img_tag = soup.select_one("img[data-old-hires], img[data-a-image-name], img.product-image")

        if not img_tag:
            # Fallback to first reasonable-sized img
            all_imgs = soup.find_all("img", src=True)
            for img in all_imgs:
                src_attr = img.get("src", "")
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

        return images

    def _save_html_for_debugging(self, html: str, url: str) -> None:
        """
        Save HTML to a temporary file for manual inspection during debugging.

        Only called when extraction fails and DEBUG logging is enabled.

        Args:
            html: HTML content to save
            url: URL the HTML was fetched from
        """
        # Only save if DEBUG logging enabled
        if not logger.isEnabledFor(logging.DEBUG):
            return

        try:
            # Create debug directory
            debug_dir = Path("/tmp/dealbrain_adapter_debug")  # noqa: S108
            debug_dir.mkdir(exist_ok=True)

            # Generate filename from URL hash
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


__all__ = ["HtmlElementExtractor"]
