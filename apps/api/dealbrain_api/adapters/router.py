"""Adapter router for selecting the appropriate adapter for a given URL."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from dealbrain_api.adapters.base import AdapterError, AdapterException, BaseAdapter
from dealbrain_api.adapters.ebay import EbayAdapter
from dealbrain_api.adapters.jsonld import JsonLdAdapter
from dealbrain_api.settings import get_settings
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)

# Registry of all available adapters
AVAILABLE_ADAPTERS: list[type[BaseAdapter]] = [
    EbayAdapter,
    JsonLdAdapter,
]


class AdapterRouter:
    """
    Routes URLs to appropriate adapter based on domain and priority.

    This router serves as the entry point for the ingestion system. It:
    1. Auto-discovers available adapters from AVAILABLE_ADAPTERS registry
    2. Matches URLs to adapters based on domain patterns
    3. Selects highest priority adapter when multiple match
    4. Validates adapter is enabled in settings before use

    Selection Algorithm:
    -------------------
    1. Parse domain from URL (e.g., "ebay.com" from "https://www.ebay.com/itm/123")
    2. Find all adapters whose supported_domains match the URL domain
    3. Sort matches by priority (lower number = higher priority)
    4. Select first match (highest priority)
    5. Check if adapter is enabled in settings
    6. Return initialized adapter instance

    Domain Matching Rules:
    ---------------------
    - Wildcard "*" matches all domains (used by JsonLdAdapter)
    - Exact match: "ebay.com" matches "ebay.com", "www.ebay.com", "m.ebay.com"
    - TLD preserved: "ebay.com" does NOT match "ebay.co.uk"
    - Subdomain normalization: "www." and "m." prefixes stripped for matching

    Priority System:
    ---------------
    - Lower number = higher priority
    - EbayAdapter: priority 1 (highest)
    - JsonLdAdapter: priority 5 (fallback)
    - If two adapters have same priority, first in registry wins

    Example Usage:
    -------------
    ```python
    router = AdapterRouter()

    # Select adapter for eBay URL
    adapter = router.select_adapter("https://www.ebay.com/itm/123456789012")
    # Returns EbayAdapter instance (priority 1)

    # Select adapter for generic URL
    adapter = router.select_adapter("https://www.bestbuy.com/product/123")
    # Returns JsonLdAdapter instance (wildcard, priority 5)

    # Convenience method: select and extract in one call
    listing = await router.extract("https://www.ebay.com/itm/123456789012")
    ```

    Error Handling:
    --------------
    - NO_ADAPTER_FOUND: No adapter matches URL (rare with wildcard JsonLdAdapter)
    - ADAPTER_DISABLED: Matched adapter is disabled in settings
    - PARSE_ERROR: Invalid URL format
    """

    def __init__(self) -> None:
        """
        Initialize adapter router.

        Loads available adapters from registry and prepares for routing.
        """
        self.adapters = AVAILABLE_ADAPTERS
        logger.info(f"Initialized AdapterRouter with {len(self.adapters)} adapters")

    def select_adapter(self, url: str) -> BaseAdapter:
        """
        Select the best adapter for the given URL.

        This is the main routing method that implements the selection algorithm:
        1. Extract domain from URL
        2. Find all matching adapters
        3. Sort by priority
        4. Validate enabled status
        5. Return initialized adapter

        Args:
            url: The URL to extract data from

        Returns:
            Initialized adapter instance ready to call extract()

        Raises:
            AdapterException: If no adapter found, adapter disabled, or invalid URL
        """
        logger.debug(f"Selecting adapter for URL: {url}")

        # Step 1: Parse URL to get domain
        try:
            domain = self._extract_domain(url)
            logger.debug(f"Extracted domain: {domain}")
        except Exception as e:
            raise AdapterException(
                AdapterError.PARSE_ERROR,
                f"Invalid URL format: {url}",
                metadata={"url": url, "error": str(e)},
            ) from e

        # Step 2: Find all matching adapters
        matching = self._find_matching_adapters(url, domain)

        if not matching:
            raise AdapterException(
                AdapterError.NO_ADAPTER_FOUND,
                f"No adapter found for URL: {url}",
                metadata={"url": url, "domain": domain},
            )

        # Step 3: Sort by priority (lowest number = highest priority)
        matching.sort(key=lambda a: self._get_adapter_priority(a))

        adapter_class = matching[0]
        adapter_name = self._get_adapter_name(adapter_class)
        adapter_priority = self._get_adapter_priority(adapter_class)

        logger.debug(
            f"Found {len(matching)} matching adapters, "
            f"selected: {adapter_name} (priority {adapter_priority})"
        )

        # Step 4: Check if adapter is enabled in settings
        if not self._is_adapter_class_enabled(adapter_class):
            raise AdapterException(
                AdapterError.ADAPTER_DISABLED,
                f"{adapter_name} adapter is disabled in settings",
                metadata={"adapter": adapter_name, "url": url},
            )

        # Step 5: Return initialized adapter instance
        adapter_instance = adapter_class()
        logger.info(f"Selected {adapter_instance.name} adapter for URL: {url}")
        return adapter_instance

    async def extract(self, url: str) -> NormalizedListingSchema:
        """
        Convenience method: select adapter and extract in one call.

        This method combines adapter selection and extraction into a single
        operation. It's the recommended way to use the router for simple cases.

        Args:
            url: The URL to extract data from

        Returns:
            Normalized listing data

        Raises:
            AdapterException: If adapter selection or extraction fails
        """
        adapter = self.select_adapter(url)
        return await adapter.extract(url)

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Parses the URL and returns the normalized domain (without www/m prefix).

        Examples:
            >>> _extract_domain("https://www.ebay.com/itm/123")
            "ebay.com"
            >>> _extract_domain("https://m.ebay.com/itm/123")
            "ebay.com"
            >>> _extract_domain("https://ebay.co.uk/itm/123")
            "ebay.co.uk"

        Args:
            url: URL to parse

        Returns:
            Normalized domain (e.g., "ebay.com")

        Raises:
            ValueError: If URL is invalid or missing domain
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if not domain:
            raise ValueError(f"No domain found in URL: {url}")

        # Normalize domain: strip www. and m. prefixes
        if domain.startswith("www."):
            domain = domain[4:]
        elif domain.startswith("m."):
            domain = domain[2:]

        return domain

    def _find_matching_adapters(self, url: str, domain: str) -> list[type[BaseAdapter]]:
        """
        Find all adapters that support this URL/domain.

        Checks each adapter's supported_domains list and returns all that match.

        Args:
            url: Original URL (for logging)
            domain: Normalized domain from URL

        Returns:
            List of adapter classes (not instances) that support this domain
        """
        matching: list[type[BaseAdapter]] = []

        for adapter_class in self.adapters:
            # Get adapter metadata without instantiating
            # We use a try/except to handle adapters that may fail during init
            # (e.g., missing API keys) but still need to be registered
            adapter_domains = self._get_adapter_domains(adapter_class)

            if self._domain_matches(domain, adapter_domains):
                matching.append(adapter_class)
                adapter_name = self._get_adapter_name(adapter_class)
                adapter_priority = self._get_adapter_priority(adapter_class)
                logger.debug(
                    f"Adapter {adapter_name} matches domain {domain} "
                    f"(priority {adapter_priority})"
                )

        return matching

    def _is_adapter_enabled(self, adapter_instance: BaseAdapter) -> bool:
        """
        Check if adapter is enabled in settings.

        Looks up the adapter's enabled status in settings.ingestion.[adapter_name].enabled

        Args:
            adapter_instance: Adapter instance to check

        Returns:
            True if adapter is enabled, False otherwise
        """
        settings = get_settings()

        # Map adapter name to settings attribute
        adapter_name = adapter_instance.name
        adapter_config = getattr(settings.ingestion, adapter_name, None)

        if adapter_config is None:
            logger.warning(
                f"No configuration found for adapter {adapter_name}, "
                f"assuming enabled by default"
            )
            return True

        enabled = adapter_config.enabled
        logger.debug(f"Adapter {adapter_name} enabled status: {enabled}")
        return enabled

    def _is_adapter_class_enabled(self, adapter_class: type[BaseAdapter]) -> bool:
        """
        Check if adapter class is enabled in settings.

        Uses adapter name to look up enabled status without instantiating.

        Args:
            adapter_class: Adapter class to check

        Returns:
            True if adapter is enabled, False otherwise
        """
        settings = get_settings()
        adapter_name = self._get_adapter_name(adapter_class)
        adapter_config = getattr(settings.ingestion, adapter_name, None)

        if adapter_config is None:
            logger.warning(
                f"No configuration found for adapter {adapter_name}, "
                f"assuming enabled by default"
            )
            return True

        enabled = adapter_config.enabled
        logger.debug(f"Adapter {adapter_name} enabled status: {enabled}")
        return enabled

    def _get_adapter_name(self, adapter_class: type[BaseAdapter]) -> str:
        """
        Get adapter name from class.

        Instantiates adapter temporarily to get name.
        Falls back to class name if instantiation fails.

        Args:
            adapter_class: Adapter class

        Returns:
            Adapter name string
        """
        # Try to get from class attribute if exists
        if hasattr(adapter_class, "_adapter_name"):
            return adapter_class._adapter_name

        # Otherwise, derive from class name
        # EbayAdapter -> "ebay", JsonLdAdapter -> "jsonld"
        class_name = adapter_class.__name__
        if class_name.endswith("Adapter"):
            return class_name[: -len("Adapter")].lower()
        return class_name.lower()

    def _get_adapter_priority(self, adapter_class: type[BaseAdapter]) -> int:
        """
        Get adapter priority from class.

        Args:
            adapter_class: Adapter class

        Returns:
            Priority integer (lower = higher priority)
        """
        # Try to get from class attribute if exists
        if hasattr(adapter_class, "_adapter_priority"):
            return adapter_class._adapter_priority

        # Default priority for adapters
        return 10

    def _get_adapter_domains(self, adapter_class: type[BaseAdapter]) -> list[str]:
        """
        Get adapter supported domains from class.

        Args:
            adapter_class: Adapter class

        Returns:
            List of supported domains
        """
        # Try to get from class attribute if exists
        if hasattr(adapter_class, "_adapter_domains"):
            return adapter_class._adapter_domains

        # Default: no domains supported
        return []

    def _domain_matches(self, url_domain: str, adapter_domains: list[str]) -> bool:
        """
        Check if URL domain matches any of adapter's domains.

        Implements matching rules:
        - Wildcard "*" matches any domain
        - Exact match: "ebay.com" matches "ebay.com"
        - Subdomain already normalized by _extract_domain()

        Args:
            url_domain: Normalized domain from URL (e.g., "ebay.com")
            adapter_domains: List of domains from adapter (e.g., ["ebay.com", "www.ebay.com"])

        Returns:
            True if URL domain matches any adapter domain
        """
        # Check for wildcard match
        if "*" in adapter_domains:
            return True

        # Normalize adapter domains and check for exact match
        for adapter_domain in adapter_domains:
            normalized_adapter_domain = adapter_domain.lower()

            # Strip www/m prefix from adapter domain for comparison
            if normalized_adapter_domain.startswith("www."):
                normalized_adapter_domain = normalized_adapter_domain[4:]
            elif normalized_adapter_domain.startswith("m."):
                normalized_adapter_domain = normalized_adapter_domain[2:]

            if url_domain == normalized_adapter_domain:
                return True

        return False


__all__ = ["AdapterRouter", "AVAILABLE_ADAPTERS"]
