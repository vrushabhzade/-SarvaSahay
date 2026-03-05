"""
Redis caching module for SarvaSahay Platform
Provides caching for profiles, schemes, and session management
"""

from shared.cache.redis_client import RedisCache, get_redis_cache
from shared.cache.decorators import cached, cache_key

__all__ = [
    "RedisCache",
    "get_redis_cache",
    "cached",
    "cache_key",
]
