"""
Redis caching utilities for performance optimization.

Provides caching decorators and utilities for expensive operations like
rule evaluation and database queries.
"""

import functools
import json
import hashlib
from typing import Any, Callable, Optional
from datetime import timedelta

from redis import asyncio as aioredis
from loguru import logger

from .settings import get_settings


class CacheManager:
    """Manages Redis cache connections and operations."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self.settings = get_settings()

    async def get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.settings.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            redis = await self.get_redis()
            return await redis.get(key)
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[timedelta] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            redis = await self.get_redis()
            if ttl:
                await redis.setex(key, int(ttl.total_seconds()), value)
            else:
                await redis.set(key, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            redis = await self.get_redis()
            await redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            redis = await self.get_redis()
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create deterministic key from args
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(key_parts)

    # Hash long keys
    if len(key_str) > 200:
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        return key_hash

    return key_str


def cached(
    prefix: str,
    ttl: Optional[timedelta] = timedelta(minutes=15),
    key_func: Optional[Callable] = None,
):
    """
    Decorator for caching async function results in Redis.

    Args:
        prefix: Cache key prefix (e.g., "ruleset", "rule_eval")
        ttl: Time-to-live for cached values
        key_func: Optional function to generate cache key from args

    Example:
        @cached(prefix="ruleset", ttl=timedelta(minutes=30))
        async def get_ruleset(session, ruleset_id: int):
            ...
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_suffix = key_func(*args, **kwargs)
            else:
                # Skip first arg (usually 'session')
                cache_suffix = cache_key(*args[1:], **kwargs)

            full_key = f"{prefix}:{cache_suffix}"

            # Try to get from cache
            cached_value = await cache_manager.get(full_key)
            if cached_value is not None:
                try:
                    return json.loads(cached_value)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in cache for key {full_key}")

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result (skip if None)
            if result is not None:
                try:
                    serialized = json.dumps(result, default=str)
                    await cache_manager.set(full_key, serialized, ttl=ttl)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Cannot serialize result for caching: {e}")

            return result

        return wrapper

    return decorator


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching pattern.

    Example:
        await invalidate_cache_pattern("ruleset:*")
        await invalidate_cache_pattern("rule_eval:123:*")
    """
    return await cache_manager.delete_pattern(pattern)


async def invalidate_ruleset_cache(ruleset_id: int):
    """Invalidate all cache entries for a ruleset."""
    await invalidate_cache_pattern(f"ruleset:{ruleset_id}*")
    await invalidate_cache_pattern(f"rule_eval:{ruleset_id}:*")


async def invalidate_rule_cache(rule_id: int):
    """Invalidate all cache entries for a rule."""
    await invalidate_cache_pattern(f"rule:{rule_id}*")
    await invalidate_cache_pattern(f"rule_preview:{rule_id}*")
