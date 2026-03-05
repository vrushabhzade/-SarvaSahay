"""
Redis client implementation for caching
Provides profile caching, scheme data caching, session management, and rate limiting
"""

import redis
import json
from typing import Optional, Any, Dict, List
from datetime import timedelta
import pickle
from shared.config.settings import get_settings

settings = get_settings()


class RedisCache:
    """Redis cache client with connection pooling and error handling"""
    
    def __init__(self):
        """Initialize Redis connection with connection pooling"""
        self.redis_client = redis.from_url(
            settings.redis.url,
            max_connections=settings.redis.max_connections,
            socket_timeout=settings.redis.socket_timeout,
            decode_responses=False,  # We'll handle encoding/decoding
        )
        
        # Separate client for string operations (with decode_responses=True)
        self.redis_string_client = redis.from_url(
            settings.redis.url,
            max_connections=settings.redis.max_connections,
            socket_timeout=settings.redis.socket_timeout,
            decode_responses=True,
        )
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except redis.RedisError as e:
            print(f"Redis get error for key {key}: {e}")
            return None
        except Exception as e:
            print(f"Error deserializing cached value for key {key}: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = pickle.dumps(value)
            if ttl:
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                return self.redis_client.set(key, serialized_value)
        except redis.RedisError as e:
            print(f"Redis set error for key {key}: {e}")
            return False
        except Exception as e:
            print(f"Error serializing value for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError as e:
            print(f"Redis delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError as e:
            print(f"Redis delete pattern error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError as e:
            print(f"Redis exists error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.expire(key, ttl))
        except redis.RedisError as e:
            print(f"Redis expire error for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get remaining TTL for key
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            return self.redis_client.ttl(key)
        except redis.RedisError as e:
            print(f"Redis ttl error for key {key}: {e}")
            return -2
    
    # Profile caching methods
    def cache_profile(self, user_id: str, profile_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Cache user profile data
        
        Args:
            user_id: User ID
            profile_data: Profile data dictionary
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        key = f"profile:{user_id}"
        return self.set(key, profile_data, ttl)
    
    def get_cached_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached user profile
        
        Args:
            user_id: User ID
            
        Returns:
            Profile data or None if not cached
        """
        key = f"profile:{user_id}"
        return self.get(key)
    
    def invalidate_profile(self, user_id: str) -> bool:
        """
        Invalidate cached user profile
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        key = f"profile:{user_id}"
        return self.delete(key)
    
    # Scheme caching methods
    def cache_scheme(self, scheme_id: str, scheme_data: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Cache government scheme data
        
        Args:
            scheme_id: Scheme ID
            scheme_data: Scheme data dictionary
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        key = f"scheme:{scheme_id}"
        return self.set(key, scheme_data, ttl)
    
    def get_cached_scheme(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached scheme data
        
        Args:
            scheme_id: Scheme ID
            
        Returns:
            Scheme data or None if not cached
        """
        key = f"scheme:{scheme_id}"
        return self.get(key)
    
    def cache_all_schemes(self, schemes: List[Dict[str, Any]], ttl: int = 86400) -> bool:
        """
        Cache all active schemes
        
        Args:
            schemes: List of scheme data dictionaries
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful, False otherwise
        """
        key = "schemes:all"
        return self.set(key, schemes, ttl)
    
    def get_all_cached_schemes(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all cached schemes
        
        Returns:
            List of scheme data or None if not cached
        """
        key = "schemes:all"
        return self.get(key)
    
    def invalidate_all_schemes(self) -> bool:
        """
        Invalidate all cached schemes
        
        Returns:
            True if successful, False otherwise
        """
        # Delete all scheme-related keys
        return self.delete_pattern("scheme:*") > 0 or self.delete("schemes:all")
    
    # Session management methods
    def create_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Create user session
        
        Args:
            session_id: Session ID
            session_data: Session data dictionary
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        return self.set(key, session_data, ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        key = f"session:{session_id}"
        return self.get(key)
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Update session data (preserves existing TTL)
        
        Args:
            session_id: Session ID
            session_data: Updated session data
            
        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        ttl = self.ttl(key)
        if ttl > 0:
            return self.set(key, session_data, ttl)
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        return self.delete(key)
    
    # Rate limiting methods
    def check_rate_limit(
        self, 
        identifier: str, 
        max_requests: int, 
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        key = f"ratelimit:{identifier}"
        try:
            current = self.redis_string_client.get(key)
            if current is None:
                # First request in window
                self.redis_string_client.setex(key, window_seconds, 1)
                return True, max_requests - 1
            
            current_count = int(current)
            if current_count >= max_requests:
                return False, 0
            
            # Increment counter
            new_count = self.redis_string_client.incr(key)
            return True, max_requests - new_count
        except redis.RedisError as e:
            print(f"Redis rate limit error for identifier {identifier}: {e}")
            # Fail open - allow request if Redis is down
            return True, max_requests
    
    def reset_rate_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for identifier
        
        Args:
            identifier: Unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        key = f"ratelimit:{identifier}"
        return self.delete(key)
    
    # Cache statistics
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0"),
                "total_keys": self.redis_client.dbsize(),
                "hit_rate": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1
                ),
            }
        except redis.RedisError as e:
            print(f"Redis stats error: {e}")
            return {}
    
    def ping(self) -> bool:
        """
        Check if Redis is available
        
        Returns:
            True if Redis is available, False otherwise
        """
        try:
            return self.redis_client.ping()
        except redis.RedisError:
            return False
    
    def flush_all(self) -> bool:
        """
        Flush all cached data (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.redis_client.flushdb()
        except redis.RedisError as e:
            print(f"Redis flush error: {e}")
            return False


# Global cache instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """
    Get Redis cache instance (singleton pattern)
    
    Returns:
        RedisCache instance
    """
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
