"""Amazon product scraper for extracting structured data from product pages.

This module provides functionality to scrape Amazon product pages and extract
structured data including title, specs, manufacturer, and model information.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# User-Agent header to mimic browser requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class AmazonScraperError(Exception):
    """Raised when Amazon scraper fails to fetch or parse product data."""


async def scrape_amazon_product(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """Scrape Amazon product page for structured data.

    Parameters
    ----------
    url : str
        Amazon product URL to scrape
    timeout : float, optional
        Request timeout in seconds, by default 10.0

    Returns
    -------
    dict[str, Any]
        Dictionary containing extracted product data:
        - title: Product title
        - description: Product description (if available)
        - manufacturer: Manufacturer name (if available)
        - model: Model number (if available)
        - price: Price string (if available)
        - specs: Dictionary of specifications from product details table
        - bullet_points: List of product feature bullet points

    Raises
    ------
    AmazonScraperError
        If the request fails or the response is invalid

    Examples
    --------
    >>> data = await scrape_amazon_product("https://www.amazon.com/dp/B0EXAMPLE")
    >>> print(data['title'])
    'Example Mini PC with Intel i7'
    >>> print(data['specs'])
    {'Manufacturer': 'Example Inc.', 'Model Number': 'MINI-PC-001'}
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error scraping Amazon URL {url}: {e}")
        raise AmazonScraperError(f"Failed to fetch Amazon product page: HTTP {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.error(f"Request error scraping Amazon URL {url}: {e}")
        raise AmazonScraperError(f"Failed to fetch Amazon product page: {e}") from e

    soup = BeautifulSoup(response.content, "lxml")

    # Extract title
    title = _extract_title(soup)

    # Extract description
    description = _extract_description(soup)

    # Extract specifications table
    specs = _extract_specifications(soup)

    # Extract price
    price = _extract_price(soup)

    # Extract bullet points (feature highlights)
    bullet_points = _extract_bullet_points(soup)

    # Extract manufacturer and model from specs or alternative locations
    manufacturer = specs.get("Manufacturer") or specs.get("Brand") or ""
    model = specs.get("Model Number") or specs.get("Model") or specs.get("Item model number") or ""

    return {
        "title": title,
        "description": description,
        "manufacturer": manufacturer,
        "model": model,
        "price": price,
        "specs": specs,
        "bullet_points": bullet_points,
    }


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract product title from page.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML page

    Returns
    -------
    str
        Product title or empty string if not found
    """
    # Try multiple selectors for title
    title_selectors = [
        {"id": "productTitle"},
        {"id": "title"},
        {"class": "product-title"},
    ]

    for selector in title_selectors:
        element = soup.find(**selector)
        if element:
            return element.get_text().strip()

    logger.warning("Could not extract title from Amazon product page")
    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    """Extract product description from page.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML page

    Returns
    -------
    str
        Product description or empty string if not found
    """
    # Try multiple selectors for description
    description_selectors = [
        {"id": "productDescription"},
        {"id": "feature-bullets"},
        {"class": "a-section a-spacing-medium a-spacing-top-small"},
    ]

    for selector in description_selectors:
        element = soup.find(**selector)
        if element:
            # Get text and clean up whitespace
            text = element.get_text().strip()
            # Remove "Product Description" header if present
            text = text.replace("Product Description", "").strip()
            return text

    return ""


def _extract_specifications(soup: BeautifulSoup) -> dict[str, str]:
    """Extract specifications table from product details.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML page

    Returns
    -------
    dict[str, str]
        Dictionary of specification key-value pairs
    """
    specs: dict[str, str] = {}

    # Try multiple table IDs (Amazon uses different IDs for different layouts)
    table_ids = [
        "productDetails_techSpec_section_1",
        "productDetails_detailBullets_sections1",
        "product-specification-table",
    ]

    for table_id in table_ids:
        table = soup.find("table", id=table_id)
        if table:
            specs.update(_parse_spec_table(table))

    # Also try detail bullets format (common on mobile/newer layouts)
    detail_bullets = soup.find("ul", class_="detail-bullet-list")
    if detail_bullets:
        for item in detail_bullets.find_all("li"):
            text = item.get_text().strip()
            # Split on colon or first whitespace after key
            if ":" in text:
                key, value = text.split(":", 1)
                specs[key.strip()] = value.strip()

    # Try additional product details section
    tech_data = soup.find("div", id="prodDetails")
    if tech_data:
        table = tech_data.find("table")
        if table:
            specs.update(_parse_spec_table(table))

    return specs


def _parse_spec_table(table: Any) -> dict[str, str]:
    """Parse a specification table element into key-value pairs.

    Parameters
    ----------
    table : BeautifulSoup element
        Table element to parse

    Returns
    -------
    dict[str, str]
        Dictionary of specification key-value pairs
    """
    specs: dict[str, str] = {}

    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            key = cells[0].get_text().strip()
            value = cells[1].get_text().strip()
            if key and value:
                specs[key] = value

    return specs


def _extract_price(soup: BeautifulSoup) -> str:
    """Extract product price from page.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML page

    Returns
    -------
    str
        Price string or empty string if not found
    """
    # Try multiple price selectors
    price_selectors = [
        {"class": "a-price-whole"},
        {"id": "priceblock_ourprice"},
        {"id": "priceblock_dealprice"},
        {"class": "a-offscreen"},
    ]

    for selector in price_selectors:
        element = soup.find(**selector)
        if element:
            price_text = element.get_text().strip()
            # Clean up price text (remove extra whitespace, currency symbols)
            return price_text

    return ""


def _extract_bullet_points(soup: BeautifulSoup) -> list[str]:
    """Extract product feature bullet points.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed HTML page

    Returns
    -------
    list[str]
        List of feature bullet points
    """
    bullet_points: list[str] = []

    # Try feature bullets section
    feature_bullets = soup.find("div", id="feature-bullets")
    if feature_bullets:
        bullet_list = feature_bullets.find("ul")
        if bullet_list:
            for item in bullet_list.find_all("li"):
                text = item.get_text().strip()
                if text:
                    bullet_points.append(text)

    return bullet_points
