"""Currency and condition conversion utilities for ingestion.

This module provides pure conversion functions for normalizing prices and conditions
from various marketplaces into standardized formats.
"""

from decimal import Decimal

# Currency conversion rates (fixed for Phase 2)
# TODO: Phase 3+ will use live rates API
CURRENCY_RATES = {
    "USD": Decimal("1.0"),
    "EUR": Decimal("1.08"),  # 1 EUR = 1.08 USD
    "GBP": Decimal("1.27"),  # 1 GBP = 1.27 USD
    "CAD": Decimal("0.74"),  # 1 CAD = 0.74 USD
}

# Condition normalization mapping
CONDITION_MAPPING = {
    "new": "new",
    "brand new": "new",
    "refurb": "refurb",  # Already normalized value
    "seller refurbished": "refurb",
    "manufacturer refurbished": "refurb",
    "refurbished": "refurb",
    "used": "used",
    "pre-owned": "used",
    "open box": "used",
    "for parts": "used",
}


def convert_to_usd(
    price: Decimal | None,
    currency: str | None,
) -> Decimal | None:
    """Convert price to USD using fixed exchange rates.

    Args:
        price: Original price amount (may be None for partial extractions)
        currency: ISO currency code (USD|EUR|GBP|CAD)

    Returns:
        Price converted to USD (2 decimal places), or None if price is None

    Example:
        >>> convert_to_usd(Decimal("500"), "EUR")
        Decimal('540.00')
        >>> convert_to_usd(Decimal("599.99"), "USD")
        Decimal('599.99')
        >>> convert_to_usd(Decimal("599.99"), "JPY")
        Decimal('599.99')  # Unknown currency defaults to USD
        >>> convert_to_usd(None, "USD")
        None  # Partial extraction without price
    """
    # Handle None price (partial extraction)
    if price is None:
        return None

    if not currency or currency not in CURRENCY_RATES:
        # Default to USD if unknown currency
        return price.quantize(Decimal("0.01"))

    rate = CURRENCY_RATES[currency]
    converted = price * rate
    return converted.quantize(Decimal("0.01"))


def normalize_condition(condition: str | None) -> str:
    """Normalize condition string to standard enum value.

    Maps various condition strings to standardized Condition enum values
    (new|refurb|used). Defaults to 'used' if unknown.

    Args:
        condition: Raw condition string from adapter

    Returns:
        Normalized condition enum value

    Example:
        >>> normalize_condition("Brand New")
        'new'
        >>> normalize_condition("Seller refurbished")
        'refurb'
        >>> normalize_condition("unknown")
        'used'  # Default to 'used' if unknown
    """
    if not condition:
        return "used"  # Default to 'used'

    condition_lower = condition.lower().strip()
    return CONDITION_MAPPING.get(condition_lower, "used")


__all__ = [
    "CURRENCY_RATES",
    "CONDITION_MAPPING",
    "convert_to_usd",
    "normalize_condition",
]
