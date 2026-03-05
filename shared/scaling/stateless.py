"""
Stateless Service Design Module
Implements patterns for stateless, horizontally scalable services
Requirements: 9.2, 9.3
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import hashlib
import json

logger = logging.getLogger(__name__)


class StatelessService(ABC):
    """
    Base class for stateless services
    
    Ensures services can be horizontally scaled without state dependencies:
    - No local state storage
    - All state in external stores (Redis, Database)
    - Idempotent operations
    - Session management via external cache
    """
    
    def __init__(self, service_name: str):
        """
        Initialize stateless service
        
        Args:
            service_name: Unique name for this service
        """
        self.service_name = service_name
        logger.info(f"Stateless service initialized: {service_name}")
    
    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request in a stateless manner
        
        Args:
            request_data: Request data dictionary
        
        Returns:
            Response data dictionary
        """
        pass
    
    def generate_request_id(self, request_data: Dict[str, Any]) -> str:
        """
        Generate deterministic request ID for idempotency
        
        Args:
            request_data: Request data
        
        Returns:
            Unique request ID
        """
        # Create deterministic hash from request data
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()
    
    def is_idempotent_operation(self, operation: str) -> bool:
        """
        Check if operation is idempotent
        
        Args:
            operation: Operation name
        
        Returns:
            True if operation can be safely retried
        """
        # GET operations are always idempotent
        idempotent_operations = ['GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE']
        return operation.upper() in idempotent_operations


class SessionManager:
    """
    External session management for stateless services
    
    Stores session data in Redis for horizontal scaling
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize session manager
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis_client = redis_client
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        logger.info("SessionManager initialized")
    
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """
        Create new session
        
        Args:
            user_id: User identifier
            session_data: Session data to store
        
        Returns:
            Session ID
        """
        session_id = hashlib.sha256(f"{user_id}:{id(session_data)}".encode()).hexdigest()
        
        if self.redis_client:
            # Store in Redis for distributed access
            try:
                self.redis_client.setex(
                    f"session:{session_id}",
                    3600,  # 1 hour TTL
                    json.dumps(session_data)
                )
            except Exception as e:
                logger.error(f"Error storing session in Redis: {e}")
                # Fallback to local cache
                self.local_cache[session_id] = session_data
        else:
            # Use local cache if Redis not available
            self.local_cache[session_id] = session_data
        
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None if not found
        """
        if self.redis_client:
            try:
                data = self.redis_client.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Error retrieving session from Redis: {e}")
        
        # Fallback to local cache
        return self.local_cache.get(session_id)
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            session_data: Updated session data
        
        Returns:
            True if successful
        """
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"session:{session_id}",
                    3600,
                    json.dumps(session_data)
                )
                return True
            except Exception as e:
                logger.error(f"Error updating session in Redis: {e}")
        
        # Fallback to local cache
        self.local_cache[session_id] = session_data
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if successful
        """
        if self.redis_client:
            try:
                self.redis_client.delete(f"session:{session_id}")
            except Exception as e:
                logger.error(f"Error deleting session from Redis: {e}")
        
        # Remove from local cache
        if session_id in self.local_cache:
            del self.local_cache[session_id]
        
        logger.info(f"Session deleted: {session_id}")
        return True
    
    def extend_session(self, session_id: str, ttl: int = 3600) -> bool:
        """
        Extend session TTL
        
        Args:
            session_id: Session identifier
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        if self.redis_client:
            try:
                self.redis_client.expire(f"session:{session_id}", ttl)
                return True
            except Exception as e:
                logger.error(f"Error extending session TTL: {e}")
                return False
        
        return True


class RequestDeduplicator:
    """
    Request deduplication for idempotent operations
    
    Prevents duplicate processing of the same request across multiple instances
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize request deduplicator
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis_client = redis_client
        self.processed_requests: Dict[str, Any] = {}
        logger.info("RequestDeduplicator initialized")
    
    def is_duplicate(self, request_id: str) -> bool:
        """
        Check if request has already been processed
        
        Args:
            request_id: Unique request identifier
        
        Returns:
            True if request is duplicate
        """
        if self.redis_client:
            try:
                return self.redis_client.exists(f"request:{request_id}") > 0
            except Exception as e:
                logger.error(f"Error checking duplicate in Redis: {e}")
        
        return request_id in self.processed_requests
    
    def mark_processed(self, request_id: str, result: Any, ttl: int = 300):
        """
        Mark request as processed
        
        Args:
            request_id: Unique request identifier
            result: Processing result
            ttl: Time to live in seconds (default: 5 minutes)
        """
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"request:{request_id}",
                    ttl,
                    json.dumps(result)
                )
            except Exception as e:
                logger.error(f"Error marking request as processed: {e}")
        
        self.processed_requests[request_id] = result
    
    def get_cached_result(self, request_id: str) -> Optional[Any]:
        """
        Get cached result for duplicate request
        
        Args:
            request_id: Unique request identifier
        
        Returns:
            Cached result or None
        """
        if self.redis_client:
            try:
                data = self.redis_client.get(f"request:{request_id}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Error retrieving cached result: {e}")
        
        return self.processed_requests.get(request_id)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(redis_client=None) -> SessionManager:
    """Get or create global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(redis_client)
    return _session_manager
