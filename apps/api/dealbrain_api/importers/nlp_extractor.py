"""NLP-based component extraction from product titles and descriptions.

This module provides pattern-based extraction of hardware components
(CPU, RAM, Storage, GPU) from unstructured text using regex patterns.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Literal

import yaml

logger = logging.getLogger(__name__)

# Confidence level type
ConfidenceLevel = Literal["high", "medium", "low"]


class ExtractionResult:
    """Result of a component extraction attempt.

    Attributes
    ----------
    value : str
        The extracted value (e.g., "Intel Core i7-12700K")
    confidence : ConfidenceLevel
        Extraction confidence level
    pattern : str
        The regex pattern that matched
    match_groups : tuple
        The regex match groups for detailed parsing
    """

    def __init__(
        self,
        value: str,
        confidence: ConfidenceLevel,
        pattern: str,
        match_groups: tuple[Any, ...],
    ):
        self.value = value
        self.confidence = confidence
        self.pattern = pattern
        self.match_groups = match_groups

    def __repr__(self) -> str:
        return f"ExtractionResult(value={self.value!r}, confidence={self.confidence})"


class NLPExtractor:
    """Extract hardware components from text using pattern matching.

    This class loads extraction patterns from a YAML file and applies them
    to product titles and descriptions to extract component information.

    Parameters
    ----------
    patterns_file : Path | None
        Path to YAML file containing extraction patterns.
        If None, uses default patterns file in same directory.

    Examples
    --------
    >>> extractor = NLPExtractor()
    >>> cpu = extractor.extract_cpu("Intel Core i7-12700K Mini PC")
    >>> print(cpu.value, cpu.confidence)
    'i7-12700' 'high'
    """

    def __init__(self, patterns_file: Path | None = None):
        if patterns_file is None:
            # Default to patterns file in same directory
            patterns_file = Path(__file__).parent / "extraction_patterns.yaml"

        with open(patterns_file) as f:
            self.patterns = yaml.safe_load(f)

    def extract_cpu(self, text: str) -> ExtractionResult | None:
        """Extract CPU information from text.

        Parameters
        ----------
        text : str
            Product title or description text

        Returns
        -------
        ExtractionResult | None
            Extraction result with CPU name and confidence, or None if no match
        """
        return self._extract_component(text, "cpu_patterns")

    def extract_ram(self, text: str) -> dict[str, Any] | None:
        """Extract RAM information from text.

        Parameters
        ----------
        text : str
            Product title or description text

        Returns
        -------
        dict[str, Any] | None
            Dictionary containing:
            - capacity_gb: int - RAM capacity in GB
            - type: str - RAM type (DDR3, DDR4, DDR5)
            - speed: int | None - RAM speed in MHz (if available)
            - confidence: ConfidenceLevel
            Or None if no match
        """
        result = self._extract_component(text, "ram_patterns")
        if not result:
            return None

        # Parse the match groups to extract structured data
        match_groups = result.match_groups
        if not match_groups:
            return None

        # Extract capacity
        capacity_gb = int(match_groups[0]) if match_groups[0] else 0

        # Extract RAM type (DDR3, DDR4, DDR5)
        ram_type = match_groups[1] if len(match_groups) > 1 else ""

        # Extract speed if available (from patterns with speed)
        speed = None
        if len(match_groups) > 2 and match_groups[2]:
            try:
                speed = int(match_groups[2])
            except (ValueError, IndexError):
                pass

        return {
            "capacity_gb": capacity_gb,
            "type": ram_type,
            "speed": speed,
            "confidence": result.confidence,
        }

    def extract_storage(self, text: str) -> dict[str, Any] | None:
        """Extract storage information from text.

        Parameters
        ----------
        text : str
            Product title or description text

        Returns
        -------
        dict[str, Any] | None
            Dictionary containing:
            - capacity_gb: int - Storage capacity in GB
            - type: str - Storage type (SSD, HDD, NVMe SSD, etc.)
            - interface: str | None - Interface type (NVMe, SATA, etc.)
            - confidence: ConfidenceLevel
            Or None if no match
        """
        result = self._extract_component(text, "storage_patterns")
        if not result:
            return None

        match_groups = result.match_groups
        if not match_groups or len(match_groups) < 2:
            return None

        # Extract capacity and unit
        capacity = float(match_groups[0])
        unit = match_groups[1].upper()

        # Convert to GB
        capacity_gb = int(capacity * 1000) if unit == "TB" else int(capacity)

        # Determine storage type and interface from the matched text
        storage_type = "SSD"  # Default
        interface = None

        matched_text = result.value.upper()
        if "NVME" in matched_text:
            storage_type = "NVMe SSD"
            interface = "NVMe"
        elif "M.2" in matched_text:
            storage_type = "M.2 SSD"
            interface = "M.2"
        elif "HDD" in matched_text:
            storage_type = "HDD"
            interface = "SATA"
        elif "SATA" in matched_text:
            interface = "SATA"

        return {
            "capacity_gb": capacity_gb,
            "type": storage_type,
            "interface": interface,
            "confidence": result.confidence,
        }

    def extract_gpu(self, text: str) -> ExtractionResult | None:
        """Extract GPU information from text.

        Parameters
        ----------
        text : str
            Product title or description text

        Returns
        -------
        ExtractionResult | None
            Extraction result with GPU name and confidence, or None if no match
        """
        return self._extract_component(text, "gpu_patterns")

    def extract_form_factor(self, text: str) -> ExtractionResult | None:
        """Extract form factor information from text.

        Parameters
        ----------
        text : str
            Product title or description text

        Returns
        -------
        ExtractionResult | None
            Extraction result with form factor and confidence, or None if no match
        """
        return self._extract_component(text, "form_factor_patterns")

    def extract_all(self, text: str) -> dict[str, Any]:
        """Extract all component information from text.

        Parameters
        ----------
        text : str
            Product title or description text

        Returns
        -------
        dict[str, Any]
            Dictionary containing all extracted components:
            - cpu: ExtractionResult | None
            - ram: dict | None
            - storage: dict | None
            - gpu: ExtractionResult | None
            - form_factor: ExtractionResult | None
        """
        return {
            "cpu": self.extract_cpu(text),
            "ram": self.extract_ram(text),
            "storage": self.extract_storage(text),
            "gpu": self.extract_gpu(text),
            "form_factor": self.extract_form_factor(text),
        }

    def _extract_component(
        self, text: str, pattern_key: str
    ) -> ExtractionResult | None:
        """Extract a component using patterns from a specific pattern group.

        Parameters
        ----------
        text : str
            Text to extract from
        pattern_key : str
            Key in patterns dictionary (e.g., 'cpu_patterns')

        Returns
        -------
        ExtractionResult | None
            First matching extraction result, or None if no match
        """
        patterns = self.patterns.get(pattern_key, [])

        for pattern_def in patterns:
            pattern = pattern_def["pattern"]
            confidence = pattern_def["confidence"]

            # Try to find a match
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract the full matched text
                matched_text = match.group(0)

                # Extract match groups for detailed parsing
                match_groups = match.groups()

                return ExtractionResult(
                    value=matched_text,
                    confidence=confidence,
                    pattern=pattern,
                    match_groups=match_groups,
                )

        return None


def extract_from_amazon_data(amazon_data: dict[str, Any]) -> dict[str, Any]:
    """Extract components from Amazon scraper data.

    This is a convenience function that extracts components from both
    the title and bullet points of Amazon product data.

    Parameters
    ----------
    amazon_data : dict[str, Any]
        Data returned from amazon_scraper.scrape_amazon_product()

    Returns
    -------
    dict[str, Any]
        Dictionary containing all extracted components with the highest
        confidence matches from title and bullet points
    """
    extractor = NLPExtractor()

    # Combine title and bullet points for extraction
    text_sources = [amazon_data.get("title", "")]
    text_sources.extend(amazon_data.get("bullet_points", []))

    # Also include description if available
    if amazon_data.get("description"):
        text_sources.append(amazon_data["description"])

    # Extract from each text source and keep highest confidence
    results: dict[str, Any] = {
        "cpu": None,
        "ram": None,
        "storage": None,
        "gpu": None,
        "form_factor": None,
    }

    for text in text_sources:
        if not text:
            continue

        extracted = extractor.extract_all(text)

        # Update results with higher confidence matches
        for key, value in extracted.items():
            if value is None:
                continue

            current = results[key]
            if current is None:
                results[key] = value
            else:
                # Compare confidence levels
                current_conf = (
                    current.confidence
                    if isinstance(current, ExtractionResult)
                    else current.get("confidence", "low")
                )
                new_conf = (
                    value.confidence
                    if isinstance(value, ExtractionResult)
                    else value.get("confidence", "low")
                )

                # Priority: high > medium > low
                conf_priority = {"high": 3, "medium": 2, "low": 1}
                if conf_priority.get(new_conf, 0) > conf_priority.get(
                    current_conf, 0
                ):
                    results[key] = value

    return results
