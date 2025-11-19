"""Fuzzy matching service for matching extracted component names to catalog entries.

This module provides fuzzy matching capabilities to match extracted CPU and GPU
names from product descriptions to existing catalog entries, handling common
variations in naming conventions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from rapidfuzz import fuzz, process

if TYPE_CHECKING:
    from ..models.catalog import Cpu, Gpu

logger = logging.getLogger(__name__)


class CatalogMatcher:
    """Fuzzy matcher for CPU and GPU catalog entries.

    This class uses the rapidfuzz library to perform fuzzy string matching
    between extracted component names and catalog entries, handling common
    variations in naming conventions.

    Parameters
    ----------
    similarity_threshold : int
        Minimum similarity score (0-100) for a match to be considered valid.
        Default is 70.

    Examples
    --------
    >>> matcher = CatalogMatcher(similarity_threshold=75)
    >>> cpu = matcher.match_cpu("i7-12700K", cpu_catalog)
    >>> print(cpu.name if cpu else "No match")
    'Intel Core i7-12700K'
    """

    def __init__(self, similarity_threshold: int = 70):
        if not 0 <= similarity_threshold <= 100:
            raise ValueError("similarity_threshold must be between 0 and 100")
        self.similarity_threshold = similarity_threshold

    def match_cpu(
        self, extracted_name: str, cpus: list[Cpu]
    ) -> tuple[Cpu | None, int]:
        """Match extracted CPU name to catalog entry.

        Parameters
        ----------
        extracted_name : str
            Extracted CPU name from product description
        cpus : list[Cpu]
            List of CPU catalog entries to match against

        Returns
        -------
        tuple[Cpu | None, int]
            Tuple of (matched CPU or None, similarity score)
            Returns (None, 0) if no match above threshold is found

        Examples
        --------
        >>> matcher = CatalogMatcher()
        >>> cpu, score = matcher.match_cpu("i7 12700K", cpu_list)
        >>> print(f"Matched: {cpu.name} (score: {score})")
        """
        if not extracted_name or not cpus:
            return None, 0

        # Build list of CPU names and aliases for matching
        choices: dict[str, Cpu] = {}

        for cpu in cpus:
            # Add main CPU name
            choices[cpu.name] = cpu

            # Add aliases from attributes_json if available
            if cpu.attributes_json and "aliases" in cpu.attributes_json:
                aliases = cpu.attributes_json["aliases"]
                if isinstance(aliases, list):
                    for alias in aliases:
                        if isinstance(alias, str):
                            choices[alias] = cpu

        # Perform fuzzy matching
        result = process.extractOne(
            extracted_name,
            choices.keys(),
            scorer=fuzz.ratio,
            score_cutoff=self.similarity_threshold,
        )

        if result is None:
            logger.debug(
                f"No CPU match found for '{extracted_name}' "
                f"(threshold: {self.similarity_threshold})"
            )
            return None, 0

        matched_name, score, _ = result
        matched_cpu = choices[matched_name]

        logger.info(
            f"Matched CPU '{extracted_name}' to '{matched_cpu.name}' "
            f"(score: {score})"
        )

        return matched_cpu, int(score)

    def match_gpu(
        self, extracted_name: str, gpus: list[Gpu]
    ) -> tuple[Gpu | None, int]:
        """Match extracted GPU name to catalog entry.

        Parameters
        ----------
        extracted_name : str
            Extracted GPU name from product description
        gpus : list[Gpu]
            List of GPU catalog entries to match against

        Returns
        -------
        tuple[Gpu | None, int]
            Tuple of (matched GPU or None, similarity score)
            Returns (None, 0) if no match above threshold is found

        Examples
        --------
        >>> matcher = CatalogMatcher()
        >>> gpu, score = matcher.match_gpu("RTX 3060", gpu_list)
        >>> print(f"Matched: {gpu.name} (score: {score})")
        """
        if not extracted_name or not gpus:
            return None, 0

        # Build list of GPU names and aliases for matching
        choices: dict[str, Gpu] = {}

        for gpu in gpus:
            # Add main GPU name
            choices[gpu.name] = gpu

            # Add aliases from attributes_json if available
            if gpu.attributes_json and "aliases" in gpu.attributes_json:
                aliases = gpu.attributes_json["aliases"]
                if isinstance(aliases, list):
                    for alias in aliases:
                        if isinstance(alias, str):
                            choices[alias] = gpu

        # Perform fuzzy matching
        result = process.extractOne(
            extracted_name,
            choices.keys(),
            scorer=fuzz.ratio,
            score_cutoff=self.similarity_threshold,
        )

        if result is None:
            logger.debug(
                f"No GPU match found for '{extracted_name}' "
                f"(threshold: {self.similarity_threshold})"
            )
            return None, 0

        matched_name, score, _ = result
        matched_gpu = choices[matched_name]

        logger.info(
            f"Matched GPU '{extracted_name}' to '{matched_gpu.name}' "
            f"(score: {score})"
        )

        return matched_gpu, int(score)

    def match_cpu_with_confidence(
        self, extracted_name: str, cpus: list[Cpu]
    ) -> dict[str, Any]:
        """Match CPU and return result with confidence level.

        Parameters
        ----------
        extracted_name : str
            Extracted CPU name from product description
        cpus : list[Cpu]
            List of CPU catalog entries to match against

        Returns
        -------
        dict[str, Any]
            Dictionary containing:
            - cpu: Cpu | None - Matched CPU entry
            - score: int - Similarity score (0-100)
            - confidence: str - Confidence level (high/medium/low)
            - requires_review: bool - Whether manual review is recommended
        """
        cpu, score = self.match_cpu(extracted_name, cpus)

        # Determine confidence level based on score
        if score >= 90:
            confidence = "high"
            requires_review = False
        elif score >= 75:
            confidence = "medium"
            requires_review = True
        else:
            confidence = "low"
            requires_review = True

        return {
            "cpu": cpu,
            "score": score,
            "confidence": confidence,
            "requires_review": requires_review,
        }

    def match_gpu_with_confidence(
        self, extracted_name: str, gpus: list[Gpu]
    ) -> dict[str, Any]:
        """Match GPU and return result with confidence level.

        Parameters
        ----------
        extracted_name : str
            Extracted GPU name from product description
        gpus : list[Gpu]
            List of GPU catalog entries to match against

        Returns
        -------
        dict[str, Any]
            Dictionary containing:
            - gpu: Gpu | None - Matched GPU entry
            - score: int - Similarity score (0-100)
            - confidence: str - Confidence level (high/medium/low)
            - requires_review: bool - Whether manual review is recommended
        """
        gpu, score = self.match_gpu(extracted_name, gpus)

        # Determine confidence level based on score
        if score >= 90:
            confidence = "high"
            requires_review = False
        elif score >= 75:
            confidence = "medium"
            requires_review = True
        else:
            confidence = "low"
            requires_review = True

        return {
            "gpu": gpu,
            "score": score,
            "confidence": confidence,
            "requires_review": requires_review,
        }


def normalize_component_name(name: str) -> str:
    """Normalize component name for better matching.

    This function applies common normalization rules to component names
    to improve fuzzy matching accuracy.

    Parameters
    ----------
    name : str
        Component name to normalize

    Returns
    -------
    str
        Normalized component name

    Examples
    --------
    >>> normalize_component_name("Intel® Core™ i7-12700K")
    'Intel Core i7-12700K'
    """
    # Remove trademark symbols
    normalized = name.replace("®", "").replace("™", "")

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    # Convert to lowercase for case-insensitive matching
    normalized = normalized.lower()

    # Remove common prefixes/suffixes that don't affect identification
    replacements = {
        "processor": "",
        "graphics": "",
        "card": "",
        "desktop": "",
    }

    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    # Normalize whitespace again after replacements
    normalized = " ".join(normalized.split())

    return normalized.strip()


async def match_extracted_components(
    extracted_data: dict[str, Any],
    cpus: list[Cpu],
    gpus: list[Gpu],
    similarity_threshold: int = 70,
) -> dict[str, Any]:
    """Match all extracted components to catalog entries.

    This is a convenience function that matches CPU and GPU components
    from extracted data to catalog entries.

    Parameters
    ----------
    extracted_data : dict[str, Any]
        Extracted component data from nlp_extractor.extract_from_amazon_data()
    cpus : list[Cpu]
        List of CPU catalog entries
    gpus : list[Gpu]
        List of GPU catalog entries
    similarity_threshold : int
        Minimum similarity score for matching (default: 70)

    Returns
    -------
    dict[str, Any]
        Dictionary containing matched components with confidence levels:
        - cpu_match: dict | None - CPU match result
        - gpu_match: dict | None - GPU match result
        - requires_review: bool - Whether any component needs review
    """
    matcher = CatalogMatcher(similarity_threshold=similarity_threshold)

    results: dict[str, Any] = {
        "cpu_match": None,
        "gpu_match": None,
        "requires_review": False,
    }

    # Match CPU
    cpu_extraction = extracted_data.get("cpu")
    if cpu_extraction and hasattr(cpu_extraction, "value"):
        cpu_name = normalize_component_name(cpu_extraction.value)
        cpu_match = matcher.match_cpu_with_confidence(cpu_name, cpus)
        results["cpu_match"] = cpu_match
        if cpu_match["requires_review"]:
            results["requires_review"] = True

    # Match GPU
    gpu_extraction = extracted_data.get("gpu")
    if gpu_extraction and hasattr(gpu_extraction, "value"):
        gpu_name = normalize_component_name(gpu_extraction.value)
        gpu_match = matcher.match_gpu_with_confidence(gpu_name, gpus)
        results["gpu_match"] = gpu_match
        if gpu_match["requires_review"]:
            results["requires_review"] = True

    return results
