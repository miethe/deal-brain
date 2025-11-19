"""Redis caching service with graceful fallback.

This module provides a Redis-based caching layer with:
- Automatic serialization/deserialization with Pydantic models
- Graceful fallback when Redis is unavailable
- Configurable TTL for cache entries
- Error logging and monitoring
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import RedisError

from ..settings import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class CachingService:
    """Redis caching service with graceful degradation.

    Provides caching functionality for API responses with automatic
    serialization/deserialization and error handling. If Redis is
    unavailable, operations fail gracefully without raising exceptions.

    Args:
        redis_client: Optional Redis client (auto-initialized if not provided)
        settings: Optional application settings (auto-loaded if not provided)
    """

    def __init__(
        self,
        redis_client: Redis | None = None,
        settings: Settings | None = None
    ):
        """Initialize caching service.

        Args:
            redis_client: Optional Redis client instance
            settings: Optional application settings
        """
        self.settings = settings or get_settings()
        self._redis_client = redis_client
        self._redis_available = True  # Assume available until proven otherwise

    async def _get_redis_client(self) -> Redis | None:
        """Get or initialize Redis client.

        Returns:
            Redis client instance if available, None if initialization fails
        """
        if self._redis_client is None and self._redis_available:
            try:
                self._redis_client = await Redis.from_url(
                    self.settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established")
            except (RedisError, Exception) as e:
                logger.warning(f"Redis initialization failed: {e}")
                self._redis_available = False
                self._redis_client = None

        return self._redis_client

    async def get(
        self,
        key: str,
        model_class: type[T]
    ) -> T | None:
        """Get cached value and deserialize to Pydantic model.

        Args:
            key: Cache key
            model_class: Pydantic model class to deserialize into

        Returns:
            Deserialized model instance if found, None otherwise
        """
        try:
            client = await self._get_redis_client()
            if not client:
                return None

            cached_value = await client.get(key)
            if not cached_value:
                return None

            # Deserialize JSON to Pydantic model
            data = json.loads(cached_value)
            return model_class.model_validate(data)

        except (RedisError, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None

    async def get_raw(self, key: str) -> str | None:
        """Get cached raw string value.

        Args:
            key: Cache key

        Returns:
            Cached string value if found, None otherwise
        """
        try:
            client = await self._get_redis_client()
            if not client:
                return None

            return await client.get(key)

        except (RedisError, Exception) as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: BaseModel | dict[str, Any] | str,
        ttl_seconds: int = 3600
    ) -> bool:
        """Set cached value with automatic serialization.

        Args:
            key: Cache key
            value: Value to cache (Pydantic model, dict, or string)
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_redis_client()
            if not client:
                return False

            # Serialize value
            if isinstance(value, BaseModel):
                serialized_value = value.model_dump_json()
            elif isinstance(value, dict):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            # Set with expiry
            await client.setex(key, ttl_seconds, serialized_value)
            logger.debug(f"Cached key '{key}' with TTL {ttl_seconds}s")
            return True

        except (RedisError, Exception) as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached value.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            client = await self._get_redis_client()
            if not client:
                return False

            deleted = await client.delete(key)
            logger.debug(f"Deleted cache key '{key}': {deleted > 0}")
            return deleted > 0

        except (RedisError, Exception) as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "listing:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = await self._get_redis_client()
            if not client:
                return 0

            # Find matching keys
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)

            # Delete in batch
            if keys:
                deleted = await client.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern '{pattern}'")
                return deleted

            return 0

        except (RedisError, Exception) as e:
            logger.warning(f"Cache delete pattern error for '{pattern}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self._get_redis_client()
            if not client:
                return False

            return await client.exists(key) > 0

        except (RedisError, Exception) as e:
            logger.warning(f"Cache exists error for key '{key}': {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection.

        Should be called during application shutdown.
        """
        if self._redis_client:
            try:
                await self._redis_client.aclose()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


__all__ = ["CachingService"]
