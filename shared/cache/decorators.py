"""
Cache decorators for easy caching of function results
"""

from functools import wraps
from typing import Callable, Optional, Any
import hashlib
import json
from shared.cache.redis_client import get_redis_cache


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a deterministic string from arguments
    key_data = {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }
    key_string = json.dumps(key_data, sort_keys=True)
    # Hash for shorter keys
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = 3600,
    key_prefix: Optional[str] = None,
    skip_cache: Optional[Callable] = None
):
    """
    Decorator to cache function results in Redis
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Optional prefix for cache key
        skip_cache: Optional function to determine if caching should be skipped
        
    Example:
        @cached(ttl=300, key_prefix="user")
        def get_user_profile(user_id: str):
            return fetch_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check if we should skip cache
            if skip_cache and skip_cache(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Generate cache key
            func_name = func.__name__
            arg_key = cache_key(*args, **kwargs)
            if key_prefix:
                full_key = f"{key_prefix}:{func_name}:{arg_key}"
            else:
                full_key = f"{func_name}:{arg_key}"
            
            # Try to get from cache
            cache = get_redis_cache()
            cached_result = cache.get(full_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(full_key, result, ttl)
            return result
        
        # Add cache invalidation method
        def invalidate(*args, **kwargs):
            """Invalidate cache for specific arguments"""
            func_name = func.__name__
            arg_key = cache_key(*args, **kwargs)
            if key_prefix:
                full_key = f"{key_prefix}:{func_name}:{arg_key}"
            else:
                full_key = f"{func_name}:{arg_key}"
            cache = get_redis_cache()
            return cache.delete(full_key)
        
        wrapper.invalidate = invalidate
        return wrapper
    
    return decorator


def cached_property(ttl: int = 3600):
    """
    Decorator to cache class property results
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        
    Example:
        class User:
            @cached_property(ttl=300)
            def expensive_computation(self):
                return compute_something()
    """
    def decorator(func: Callable) -> property:
        @wraps(func)
        def wrapper(self) -> Any:
            # Generate cache key using class name and instance id
            class_name = self.__class__.__name__
            instance_id = id(self)
            func_name = func.__name__
            full_key = f"{class_name}:{instance_id}:{func_name}"
            
            # Try to get from cache
            cache = get_redis_cache()
            cached_result = cache.get(full_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(self)
            cache.set(full_key, result, ttl)
            return result
        
        return property(wrapper)
    
    return decorator
