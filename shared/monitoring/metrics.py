"""
Metrics Collection Module
Implements Prometheus-based metrics for performance tracking
Requirements: 9.1, 9.5
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from typing import Dict, Any, Optional, Callable
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collection for SarvaSahay Platform
    
    Tracks:
    - Request timing and performance
    - Eligibility evaluation metrics
    - Document processing metrics
    - Application submission metrics
    - System resource usage
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collector with Prometheus registry"""
        self.registry = registry or CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'sarvasahay_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'sarvasahay_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        # Eligibility engine metrics (Requirement 9.1: <5 seconds)
        self.eligibility_evaluation_duration = Histogram(
            'sarvasahay_eligibility_evaluation_seconds',
            'Eligibility evaluation duration in seconds',
            ['profile_type'],
            buckets=(0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0),
            registry=self.registry
        )
        
        self.eligibility_evaluations_total = Counter(
            'sarvasahay_eligibility_evaluations_total',
            'Total number of eligibility evaluations',
            ['status'],
            registry=self.registry
        )
        
        self.schemes_matched = Histogram(
            'sarvasahay_schemes_matched',
            'Number of schemes matched per evaluation',
            buckets=(0, 1, 5, 10, 15, 20, 30, 50),
            registry=self.registry
        )
        
        # Document processing metrics
        self.document_processing_duration = Histogram(
            'sarvasahay_document_processing_seconds',
            'Document processing duration in seconds',
            ['document_type'],
            buckets=(1.0, 2.0, 5.0, 10.0, 20.0, 30.0),
            registry=self.registry
        )
        
        self.documents_processed_total = Counter(
            'sarvasahay_documents_processed_total',
            'Total number of documents processed',
            ['document_type', 'status'],
            registry=self.registry
        )
        
        self.ocr_accuracy = Gauge(
            'sarvasahay_ocr_accuracy',
            'OCR extraction accuracy percentage',
            ['document_type'],
            registry=self.registry
        )
        
        # Application submission metrics
        self.applications_submitted_total = Counter(
            'sarvasahay_applications_submitted_total',
            'Total number of applications submitted',
            ['scheme', 'status'],
            registry=self.registry
        )
        
        self.application_submission_duration = Histogram(
            'sarvasahay_application_submission_seconds',
            'Application submission duration in seconds',
            ['scheme'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0),
            registry=self.registry
        )
        
        # Government API metrics
        self.gov_api_requests_total = Counter(
            'sarvasahay_gov_api_requests_total',
            'Total government API requests',
            ['api_name', 'status'],
            registry=self.registry
        )
        
        self.gov_api_duration = Histogram(
            'sarvasahay_gov_api_duration_seconds',
            'Government API request duration',
            ['api_name'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        # System health metrics
        self.active_users = Gauge(
            'sarvasahay_active_users',
            'Number of currently active users',
            registry=self.registry
        )
        
        self.concurrent_requests = Gauge(
            'sarvasahay_concurrent_requests',
            'Number of concurrent requests being processed',
            registry=self.registry
        )
        
        # ML model metrics
        self.model_accuracy = Gauge(
            'sarvasahay_model_accuracy',
            'Current ML model accuracy',
            ['model_name'],
            registry=self.registry
        )
        
        self.model_inference_duration = Histogram(
            'sarvasahay_model_inference_seconds',
            'ML model inference duration',
            ['model_name'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0),
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'sarvasahay_cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'sarvasahay_cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'sarvasahay_errors_total',
            'Total number of errors',
            ['error_type', 'severity'],
            registry=self.registry
        )
        
        logger.info("MetricsCollector initialized with Prometheus registry")
    
    def track_request(self, method: str, endpoint: str, status: int, duration: float):
        """Track HTTP request metrics"""
        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Log slow requests (>5 seconds violates requirement 9.1)
        if duration > 5.0:
            logger.warning(
                f"Slow request detected: {method} {endpoint} took {duration:.2f}s",
                extra={'method': method, 'endpoint': endpoint, 'duration': duration}
            )
    
    def track_eligibility_evaluation(
        self, 
        duration: float, 
        schemes_matched: int, 
        profile_type: str = "standard",
        status: str = "success"
    ):
        """Track eligibility evaluation metrics"""
        self.eligibility_evaluation_duration.labels(profile_type=profile_type).observe(duration)
        self.eligibility_evaluations_total.labels(status=status).inc()
        self.schemes_matched.observe(schemes_matched)
        
        # Alert if evaluation exceeds 5-second requirement
        if duration > 5.0:
            logger.error(
                f"Eligibility evaluation exceeded 5s requirement: {duration:.2f}s",
                extra={'duration': duration, 'schemes_matched': schemes_matched}
            )
    
    def track_document_processing(
        self,
        document_type: str,
        duration: float,
        status: str = "success",
        accuracy: Optional[float] = None
    ):
        """Track document processing metrics"""
        self.document_processing_duration.labels(document_type=document_type).observe(duration)
        self.documents_processed_total.labels(document_type=document_type, status=status).inc()
        
        if accuracy is not None:
            self.ocr_accuracy.labels(document_type=document_type).set(accuracy * 100)
    
    def track_application_submission(
        self,
        scheme: str,
        duration: float,
        status: str = "success"
    ):
        """Track application submission metrics"""
        self.applications_submitted_total.labels(scheme=scheme, status=status).inc()
        self.application_submission_duration.labels(scheme=scheme).observe(duration)
    
    def track_gov_api_call(
        self,
        api_name: str,
        duration: float,
        status: str = "success"
    ):
        """Track government API call metrics"""
        self.gov_api_requests_total.labels(api_name=api_name, status=status).inc()
        self.gov_api_duration.labels(api_name=api_name).observe(duration)
    
    def track_model_inference(
        self,
        model_name: str,
        duration: float,
        accuracy: Optional[float] = None
    ):
        """Track ML model inference metrics"""
        self.model_inference_duration.labels(model_name=model_name).observe(duration)
        
        if accuracy is not None:
            self.model_accuracy.labels(model_name=model_name).set(accuracy)
    
    def track_cache_operation(self, cache_type: str, hit: bool):
        """Track cache hit/miss metrics"""
        if hit:
            self.cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses_total.labels(cache_type=cache_type).inc()
    
    def track_error(self, error_type: str, severity: str = "error"):
        """Track error occurrences"""
        self.errors_total.labels(error_type=error_type, severity=severity).inc()
    
    def set_active_users(self, count: int):
        """Set current active user count"""
        self.active_users.set(count)
    
    def increment_concurrent_requests(self):
        """Increment concurrent request counter"""
        self.concurrent_requests.inc()
    
    def decrement_concurrent_requests(self):
        """Decrement concurrent request counter"""
        self.concurrent_requests.dec()
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get human-readable metrics summary"""
        # Note: Prometheus metrics don't expose internal values directly
        # This is a simplified summary for display purposes
        return {
            "requests": {
                "note": "Use /metrics endpoint for detailed Prometheus metrics"
            },
            "eligibility": {
                "note": "Use /metrics endpoint for detailed Prometheus metrics"
            },
            "documents": {
                "note": "Use /metrics endpoint for detailed Prometheus metrics"
            },
            "applications": {
                "note": "Use /metrics endpoint for detailed Prometheus metrics"
            },
            "cache": {
                "note": "Use /metrics endpoint for detailed Prometheus metrics"
            },
            "errors": {
                "note": "Use /metrics endpoint for detailed Prometheus metrics"
            }
        }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# Decorator for tracking function execution time
def track_request_time(endpoint: str, method: str = "GET"):
    """Decorator to track request execution time"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            collector.increment_concurrent_requests()
            start_time = time.time()
            status = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                collector.track_error(type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                collector.track_request(method, endpoint, status, duration)
                collector.decrement_concurrent_requests()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            collector.increment_concurrent_requests()
            start_time = time.time()
            status = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                collector.track_error(type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                collector.track_request(method, endpoint, status, duration)
                collector.decrement_concurrent_requests()
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_eligibility_evaluation(func: Callable):
    """Decorator to track eligibility evaluation performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        collector = get_metrics_collector()
        start_time = time.time()
        status = "success"
        schemes_matched = 0
        
        try:
            result = func(*args, **kwargs)
            if isinstance(result, list):
                schemes_matched = len(result)
            return result
        except Exception as e:
            status = "error"
            collector.track_error(f"eligibility_{type(e).__name__}")
            raise
        finally:
            duration = time.time() - start_time
            collector.track_eligibility_evaluation(duration, schemes_matched, status=status)
    
    return wrapper


def track_document_processing(document_type: str):
    """Decorator to track document processing performance"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                collector.track_error(f"document_{type(e).__name__}")
                raise
            finally:
                duration = time.time() - start_time
                collector.track_document_processing(document_type, duration, status)
        
        return wrapper
    return decorator


def track_application_submission(scheme: str):
    """Decorator to track application submission performance"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                collector.track_error(f"application_{type(e).__name__}")
                raise
            finally:
                duration = time.time() - start_time
                collector.track_application_submission(scheme, duration, status)
        
        return wrapper
    return decorator
