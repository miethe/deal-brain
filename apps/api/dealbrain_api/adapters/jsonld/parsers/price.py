"""Price parsing utilities for various formats."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from bs4 import BeautifulSoup


class PriceParser:
    """
    Parses price from various formats and sources.

    Handles:
    - String: "599.99", "$599.99", "USD 599.99"
    - Number: 599.99
    - With separators: "1,599.99"
    - HTML elements: offscreen spans, aria-hidden elements, etc.
    """

    @staticmethod
    def parse_price(price: Any) -> Decimal | None:
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

    @staticmethod
    def extract_price_from_offers(offers: list[dict[str, Any]]) -> tuple[Decimal | None, str]:
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
                parsed_price = PriceParser.parse_price(price_raw)
                if parsed_price:
                    prices.append(parsed_price)
                    # Extract currency from first valid offer
                    if len(prices) == 1:
                        currency = offer.get("priceCurrency", "USD")

        if prices:
            return min(prices), currency
        return None, currency

    @staticmethod
    def extract_list_price(soup: BeautifulSoup) -> Decimal | None:
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
                return PriceParser.parse_price(raw_price)

        return None


__all__ = ["PriceParser"]
