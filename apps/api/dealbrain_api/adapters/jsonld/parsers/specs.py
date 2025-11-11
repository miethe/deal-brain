"""Spec extraction utilities for CPU, RAM, storage, and brand."""

import re
from typing import Any

from bs4 import BeautifulSoup

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


class SpecParser:
    """
    Extracts hardware specifications from text and HTML tables.

    Supports:
    - CPU: "Intel Core i7-12700K", "AMD Ryzen 7 5800X"
    - RAM: "16GB RAM", "32 GB DDR4"
    - Storage: "512GB SSD", "1TB NVMe"
    - Brand: From byline or title
    """

    @staticmethod
    def extract_specs(text: str) -> dict[str, Any]:
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
        storage_match = STORAGE_PATTERN.search(text)
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

    @staticmethod
    def extract_specs_from_table(soup: BeautifulSoup) -> dict[str, str]:
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

    @staticmethod
    def extract_brand(soup: BeautifulSoup) -> str | None:
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


__all__ = ["SpecParser", "CPU_PATTERN", "RAM_PATTERN", "STORAGE_PATTERN"]
