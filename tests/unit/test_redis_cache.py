"""
Unit tests for Redis caching layer
Tests cache operations, rate limiting, and session management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from shared.cache.redis_client import RedisCache, get_redis_cache
from shared.cache.decorators import cached, cache_key
import time


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    with patch('shared.cache.redis_client.redis') as mock:
        mock_client = MagicMock()
        mock_string_client = MagicMock()
        mock.from_url.side_effect = [mock_client, mock_string_client]
        yield mock_client, mock_string_client


def test_cache_get_set(mock_redis):
    """Test basic get and set operations"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    # Mock successful set
    mock_client.setex.return_value = True
    result = cache.set("test_key", {"data": "value"}, ttl=300)
    assert result is True
    
    # Mock successful get
    import pickle
    mock_client.get.return_value = pickle.dumps({"data": "value"})
    result = cache.get("test_key")
    assert result == {"data": "value"}


def test_cache_get_nonexistent_key(mock_redis):
    """Test getting a non-existent key returns None"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    mock_client.get.return_value = None
    result = cache.get("nonexistent_key")
    assert result is None


def test_cache_delete(mock_redis):
    """Test deleting a key"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    mock_client.delete.return_value = 1
    result = cache.delete("test_key")
    assert result is True


def test_cache_exists(mock_redis):
    """Test checking if key exists"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    mock_client.exists.return_value = 1
    result = cache.exists("test_key")
    assert result is True
    
    mock_client.exists.return_value = 0
    result = cache.exists("nonexistent_key")
    assert result is False


def test_cache_profile(mock_redis):
    """Test profile caching operations"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    profile_data = {
        "user_id": "123",
        "name": "Test User",
        "age": 35,
        "state": "Maharashtra",
    }
    
    # Test caching profile
    mock_client.setex.return_value = True
    result = cache.cache_profile("123", profile_data, ttl=3600)
    assert result is True
    
    # Test retrieving cached profile
    import pickle
    mock_client.get.return_value = pickle.dumps(profile_data)
    result = cache.get_cached_profile("123")
    assert result == profile_data
    
    # Test invalidating profile
    mock_client.delete.return_value = 1
    result = cache.invalidate_profile("123")
    assert result is True


def test_cache_scheme(mock_redis):
    """Test scheme caching operations"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    scheme_data = {
        "scheme_id": "456",
        "name": "PM-KISAN",
        "benefit_amount": 6000,
    }
    
    # Test caching scheme
    mock_client.setex.return_value = True
    result = cache.cache_scheme("456", scheme_data, ttl=86400)
    assert result is True
    
    # Test retrieving cached scheme
    import pickle
    mock_client.get.return_value = pickle.dumps(scheme_data)
    result = cache.get_cached_scheme("456")
    assert result == scheme_data


def test_cache_all_schemes(mock_redis):
    """Test caching all schemes"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    schemes = [
        {"scheme_id": "1", "name": "Scheme 1"},
        {"scheme_id": "2", "name": "Scheme 2"},
    ]
    
    # Test caching all schemes
    mock_client.setex.return_value = True
    result = cache.cache_all_schemes(schemes, ttl=86400)
    assert result is True
    
    # Test retrieving all cached schemes
    import pickle
    mock_client.get.return_value = pickle.dumps(schemes)
    result = cache.get_all_cached_schemes()
    assert result == schemes
    assert len(result) == 2


def test_session_management(mock_redis):
    """Test session create, get, update, delete operations"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    session_data = {
        "user_id": "789",
        "login_time": "2026-03-02T10:00:00",
        "permissions": ["read", "write"],
    }
    
    # Test creating session
    mock_client.setex.return_value = True
    result = cache.create_session("session_123", session_data, ttl=3600)
    assert result is True
    
    # Test getting session
    import pickle
    mock_client.get.return_value = pickle.dumps(session_data)
    result = cache.get_session("session_123")
    assert result == session_data
    
    # Test updating session
    mock_client.ttl.return_value = 1800  # 30 minutes remaining
    mock_client.setex.return_value = True
    updated_data = {**session_data, "last_activity": "2026-03-02T10:30:00"}
    result = cache.update_session("session_123", updated_data)
    assert result is True
    
    # Test deleting session
    mock_client.delete.return_value = 1
    result = cache.delete_session("session_123")
    assert result is True


def test_rate_limiting(mock_redis):
    """Test rate limiting functionality"""
    _, mock_string_client = mock_redis
    cache = RedisCache()
    
    # First request - should be allowed
    mock_string_client.get.return_value = None
    mock_string_client.setex.return_value = True
    is_allowed, remaining = cache.check_rate_limit("user_123", max_requests=10, window_seconds=60)
    assert is_allowed is True
    assert remaining == 9
    
    # Subsequent request within limit
    mock_string_client.get.return_value = "5"
    mock_string_client.incr.return_value = 6
    is_allowed, remaining = cache.check_rate_limit("user_123", max_requests=10, window_seconds=60)
    assert is_allowed is True
    assert remaining == 4
    
    # Request exceeding limit
    mock_string_client.get.return_value = "10"
    is_allowed, remaining = cache.check_rate_limit("user_123", max_requests=10, window_seconds=60)
    assert is_allowed is False
    assert remaining == 0


def test_cache_stats(mock_redis):
    """Test getting cache statistics"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    mock_info = {
        "connected_clients": 5,
        "used_memory_human": "1.5M",
        "keyspace_hits": 100,
        "keyspace_misses": 10,
    }
    mock_client.info.return_value = mock_info
    mock_client.dbsize.return_value = 50
    
    stats = cache.get_cache_stats()
    assert stats["connected_clients"] == 5
    assert stats["used_memory"] == "1.5M"
    assert stats["total_keys"] == 50
    assert stats["hit_rate"] > 0.9  # 100/(100+10)


def test_cache_ping(mock_redis):
    """Test Redis availability check"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    mock_client.ping.return_value = True
    result = cache.ping()
    assert result is True


def test_cache_key_generation():
    """Test cache key generation from arguments"""
    # Test with positional arguments
    key1 = cache_key("arg1", "arg2", "arg3")
    key2 = cache_key("arg1", "arg2", "arg3")
    assert key1 == key2  # Same args should produce same key
    
    # Test with keyword arguments
    key3 = cache_key(user_id="123", action="view")
    key4 = cache_key(action="view", user_id="123")
    assert key3 == key4  # Order shouldn't matter for kwargs
    
    # Test with mixed arguments
    key5 = cache_key("arg1", user_id="123")
    assert isinstance(key5, str)
    assert len(key5) == 32  # MD5 hash length


def test_cached_decorator():
    """Test the cached decorator"""
    call_count = 0
    
    @cached(ttl=300, key_prefix="test")
    def expensive_function(x, y):
        nonlocal call_count
        call_count += 1
        return x + y
    
    with patch('shared.cache.decorators.get_redis_cache') as mock_cache:
        mock_cache_instance = MagicMock()
        mock_cache.return_value = mock_cache_instance
        
        # First call - cache miss
        mock_cache_instance.get.return_value = None
        mock_cache_instance.set.return_value = True
        result = expensive_function(2, 3)
        assert result == 5
        assert call_count == 1
        
        # Second call - cache hit
        mock_cache_instance.get.return_value = 5
        result = expensive_function(2, 3)
        assert result == 5
        assert call_count == 1  # Function not called again


def test_delete_pattern(mock_redis):
    """Test deleting keys by pattern"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    # Mock keys matching pattern
    mock_client.keys.return_value = [b"user:1", b"user:2", b"user:3"]
    mock_client.delete.return_value = 3
    
    result = cache.delete_pattern("user:*")
    assert result == 3


def test_invalidate_all_schemes(mock_redis):
    """Test invalidating all cached schemes"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    # Mock pattern deletion
    mock_client.keys.return_value = [b"scheme:1", b"scheme:2"]
    mock_client.delete.return_value = 2
    
    result = cache.invalidate_all_schemes()
    assert result is True


def test_cache_error_handling(mock_redis):
    """Test cache error handling"""
    mock_client, _ = mock_redis
    cache = RedisCache()
    
    # Test get with Redis error
    from redis.exceptions import RedisError
    mock_client.get.side_effect = RedisError("Connection error")
    result = cache.get("test_key")
    assert result is None  # Should return None on error
    
    # Test set with Redis error
    mock_client.setex.side_effect = RedisError("Connection error")
    result = cache.set("test_key", "value", ttl=300)
    assert result is False  # Should return False on error


def test_get_redis_cache_singleton():
    """Test that get_redis_cache returns singleton instance"""
    with patch('shared.cache.redis_client.redis'):
        cache1 = get_redis_cache()
        cache2 = get_redis_cache()
        assert cache1 is cache2  # Should be same instance
