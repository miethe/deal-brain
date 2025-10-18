"""Base adapter interface for URL ingestion."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)


class AdapterError(str, Enum):
    """
    Error types for adapter operations.

    These standardized error codes allow the ingestion service to handle
    failures consistently across different adapters and implement appropriate
    retry strategies.

    Attributes:
        TIMEOUT: Request exceeded configured timeout
        INVALID_SCHEMA: Response data failed validation
        ADAPTER_DISABLED: Adapter is disabled in settings
        RATE_LIMITED: Rate limit exceeded, retry later
        ITEM_NOT_FOUND: Resource not found (404 or equivalent)
        NETWORK_ERROR: Network connectivity issue
        PARSE_ERROR: Failed to parse response data
    """

    TIMEOUT = "timeout"
    INVALID_SCHEMA = "invalid_schema"
    ADAPTER_DISABLED = "adapter_disabled"
    RATE_LIMITED = "rate_limited"
    ITEM_NOT_FOUND = "item_not_found"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"


class AdapterException(Exception):
    """
    Base exception for adapter errors.

    Attributes:
        error_type: AdapterError enum value
        message: Human-readable error message
        metadata: Additional context (optional)
    """

    def __init__(
        self,
        error_type: AdapterError,
        message: str,
        metadata: dict[str, Any] | None = None,
    ):
        self.error_type = error_type
        self.message = message
        self.metadata = metadata or {}
        super().__init__(f"[{error_type.value}] {message}")


class RateLimitConfig:
    """
    Rate limiting configuration for an adapter.

    Attributes:
        requests_per_minute: Maximum requests per minute
        current_count: Current request count in the time window
        window_start: Start time of current rate limit window
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.current_count = 0
        self.window_start = asyncio.get_event_loop().time()

    async def check_and_wait(self) -> None:
        """
        Check rate limit and wait if necessary.

        Raises:
            AdapterException: If rate limit is exceeded and cannot wait
        """
        now = asyncio.get_event_loop().time()
        elapsed = now - self.window_start

        # Reset window if a minute has passed
        if elapsed >= 60:
            self.current_count = 0
            self.window_start = now
            return

        # Check if we're at the limit
        if self.current_count >= self.requests_per_minute:
            wait_time = 60 - elapsed
            logger.warning(
                f"Rate limit reached ({self.requests_per_minute}/min). "
                f"Waiting {wait_time:.1f}s"
            )
            await asyncio.sleep(wait_time)
            self.current_count = 0
            self.window_start = asyncio.get_event_loop().time()

        self.current_count += 1


class RetryConfig:
    """
    Retry configuration for adapter requests.

    Attributes:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier (seconds)
        retryable_errors: Error types that should trigger a retry
    """

    def __init__(
        self,
        max_retries: int = 2,
        backoff_factor: float = 1.0,
        retryable_errors: set[AdapterError] | None = None,
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retryable_errors = retryable_errors or {
            AdapterError.TIMEOUT,
            AdapterError.NETWORK_ERROR,
            AdapterError.RATE_LIMITED,
        }

    async def execute_with_retry(
        self,
        operation: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an async operation with retry logic.

        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result from successful operation execution

        Raises:
            AdapterException: If all retries are exhausted
        """
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except AdapterException as e:
                last_error = e
                if e.error_type not in self.retryable_errors:
                    raise
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2**attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e.message}. "
                        f"Retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed: {e.message}"
                    )
                    raise

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise AdapterException(
            AdapterError.NETWORK_ERROR,
            "Operation failed with no error details",
        )


class BaseAdapter(ABC):
    """
    Abstract base class for all URL ingestion adapters.

    All adapters (eBay API, JSON-LD, generic scraper) must inherit from this
    class and implement the extract() method. The base class provides common
    functionality like rate limiting, retry logic, and timeout handling.

    Adapter Pattern:
    ----------------
    1. Each adapter handles a specific data source (eBay API, JSON-LD, etc.)
    2. All adapters produce the same output: NormalizedListingSchema
    3. The ingestion service tries adapters in priority order
    4. First successful extraction wins

    How to Implement a New Adapter:
    --------------------------------
    1. Inherit from BaseAdapter
    2. Set adapter metadata (name, supported_domains, priority)
    3. Implement async extract(url: str) -> NormalizedListingSchema
    4. Use self.retry_config.execute_with_retry() for HTTP requests
    5. Raise AdapterException with appropriate error_type on failure

    Example:
    --------
    ```python
    class EbayApiAdapter(BaseAdapter):
        def __init__(self, api_key: str, timeout_s: int = 6):
            super().__init__(
                name="ebay_api",
                supported_domains=["ebay.com", "ebay.co.uk"],
                priority=1,  # Highest priority
                timeout_s=timeout_s,
                max_retries=2,
            )
            self.api_key = api_key

        async def extract(self, url: str) -> NormalizedListingSchema:
            # Extract item ID from URL
            item_id = self._parse_item_id(url)

            # Fetch from API with retry
            data = await self.retry_config.execute_with_retry(
                self._fetch_item, item_id
            )

            # Transform to normalized schema
            return self._transform(data)
    ```

    Attributes:
        name: Adapter identifier (e.g., "ebay_api", "jsonld")
        supported_domains: List of domains this adapter can handle
        priority: Adapter priority (lower = higher priority)
        timeout_s: Request timeout in seconds
        rate_limit_config: Rate limiting configuration
        retry_config: Retry strategy configuration
    """

    def __init__(
        self,
        name: str,
        supported_domains: list[str],
        priority: int = 10,
        timeout_s: int = 8,
        max_retries: int = 2,
        requests_per_minute: int = 60,
    ):
        """
        Initialize base adapter.

        Args:
            name: Adapter identifier (e.g., "ebay_api")
            supported_domains: List of domains (e.g., ["ebay.com"])
            priority: Adapter priority (lower = higher priority)
            timeout_s: Request timeout in seconds
            max_retries: Maximum retry attempts
            requests_per_minute: Rate limit threshold
        """
        self.name = name
        self.supported_domains = supported_domains
        self.priority = priority
        self.timeout_s = timeout_s
        self.rate_limit_config = RateLimitConfig(requests_per_minute)
        self.retry_config = RetryConfig(max_retries=max_retries)

    @abstractmethod
    async def extract(self, url: str) -> NormalizedListingSchema:
        """
        Extract listing data from URL and return normalized schema.

        This is the main method that each adapter must implement. It should:
        1. Parse the URL to extract necessary identifiers
        2. Fetch data from the source (API, webpage, etc.)
        3. Transform the raw data into NormalizedListingSchema
        4. Validate the schema before returning

        Args:
            url: URL to extract listing data from

        Returns:
            NormalizedListingSchema with normalized listing data

        Raises:
            AdapterException: If extraction fails for any reason
        """
        pass

    def supports_url(self, url: str) -> bool:
        """
        Check if this adapter supports the given URL.

        Args:
            url: URL to check

        Returns:
            True if URL domain matches supported_domains
        """
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.supported_domains)

    async def _check_rate_limit(self) -> None:
        """Check rate limit before making a request."""
        await self.rate_limit_config.check_and_wait()

    def _validate_response(self, data: dict[str, Any]) -> None:
        """
        Validate raw response data before transformation.

        Args:
            data: Raw response data dictionary

        Raises:
            AdapterException: If validation fails
        """
        required_fields = ["title", "price"]
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            raise AdapterException(
                AdapterError.INVALID_SCHEMA,
                f"Missing required fields: {', '.join(missing)}",
                metadata={"missing_fields": missing},
            )


__all__ = [
    "AdapterError",
    "AdapterException",
    "RateLimitConfig",
    "RetryConfig",
    "BaseAdapter",
]
