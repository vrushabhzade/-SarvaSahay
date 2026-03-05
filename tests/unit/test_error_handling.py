"""
Unit Tests for Error Handling and Fallback Mechanisms
Tests graceful degradation, circuit breakers, retry logic, and user-friendly error messages
"""

import pytest
import time
from datetime import datetime, timedelta
from shared.utils.error_handling import (
    ErrorSeverity,
    ErrorCategory,
    SarvaSahayError,
    DocumentProcessingError,
    APIIntegrationError,
    TrackingError,
    CircuitBreaker,
    RetryStrategy,
    FallbackManager,
    ErrorMessageGenerator,
    with_circuit_breaker,
    with_retry,
    handle_error
)


class TestErrorClasses:
    """Test custom error classes"""
    
    def test_sarvasahay_error_creation(self):
        """Test creating SarvaSahay error with context"""
        error = SarvaSahayError(
            message="Test error",
            error_code="TEST_001",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM_INTEGRATION,
            user_message="User-friendly message",
            suggested_actions=["Action 1", "Action 2"]
        )
        
        assert error.context.error_code == "TEST_001"
        assert error.context.severity == ErrorSeverity.HIGH
        assert error.context.category == ErrorCategory.SYSTEM_INTEGRATION
        assert error.context.user_message == "User-friendly message"
        assert len(error.context.suggested_actions) == 2
    
    def test_document_processing_error(self):
        """Test document processing error"""
        error = DocumentProcessingError(
            message="OCR failed",
            severity=ErrorSeverity.MEDIUM
        )
        
        assert error.context.error_code == "DOC_ERROR"
        assert error.context.category == ErrorCategory.DATA_VALIDATION
    
    def test_api_integration_error(self):
        """Test API integration error"""
        error = APIIntegrationError(
            message="API unavailable",
            severity=ErrorSeverity.HIGH
        )
        
        assert error.context.error_code == "API_ERROR"
        assert error.context.category == ErrorCategory.SYSTEM_INTEGRATION
    
    def test_tracking_error(self):
        """Test tracking error"""
        error = TrackingError(
            message="Tracking failed",
            severity=ErrorSeverity.MEDIUM
        )
        
        assert error.context.error_code == "TRACK_ERROR"
        assert error.context.category == ErrorCategory.SYSTEM_INTEGRATION


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows calls"""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=5)
        
        def successful_func():
            return "success"
        
        result = cb.call(successful_func)
        assert result == "success"
        assert cb.state.state == "closed"
        assert cb.state.failure_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=5)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state.state == "open"
        assert cb.state.failure_count == 3
        
        # Next call should fail fast
        with pytest.raises(APIIntegrationError) as exc_info:
            cb.call(failing_func)
        
        assert "Circuit breaker is open" in str(exc_info.value)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1, success_threshold=2)
        
        def failing_func():
            raise Exception("Test failure")
        
        def successful_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state.state == "open"
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Should enter half-open state and allow calls
        result = cb.call(successful_func)
        assert result == "success"
        assert cb.state.state == "half_open"
        
        # Another success should close the circuit
        result = cb.call(successful_func)
        assert result == "success"
        assert cb.state.state == "closed"
    
    def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset"""
        cb = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        assert cb.state.state == "open"
        
        # Reset
        cb.reset()
        assert cb.state.state == "closed"
        assert cb.state.failure_count == 0


class TestRetryStrategy:
    """Test retry strategy with exponential backoff"""
    
    def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt"""
        retry = RetryStrategy(max_attempts=3)
        
        def successful_func():
            return "success"
        
        result = retry.execute(successful_func)
        assert result == "success"
    
    def test_retry_success_after_failures(self):
        """Test successful execution after retries"""
        retry = RetryStrategy(max_attempts=3, initial_delay=0.1)
        
        attempt_count = {"count": 0}
        
        def flaky_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = retry.execute(flaky_func)
        assert result == "success"
        assert attempt_count["count"] == 3
    
    def test_retry_exhausts_attempts(self):
        """Test retry exhausts all attempts and raises last exception"""
        retry = RetryStrategy(max_attempts=3, initial_delay=0.1)
        
        def always_failing_func():
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError) as exc_info:
            retry.execute(always_failing_func)
        
        assert "Permanent failure" in str(exc_info.value)
    
    def test_retry_respects_exception_filter(self):
        """Test retry only retries specified exceptions"""
        retry = RetryStrategy(max_attempts=3, initial_delay=0.1)
        
        def func_with_value_error():
            raise ValueError("Should not retry")
        
        # Should not retry ValueError
        with pytest.raises(ValueError):
            retry.execute(func_with_value_error, retry_on=[ConnectionError])


class TestWithCircuitBreakerDecorator:
    """Test circuit breaker decorator"""
    
    def test_decorator_protects_function(self):
        """Test decorator adds circuit breaker protection"""
        
        @with_circuit_breaker(failure_threshold=2, timeout_seconds=5)
        def protected_func(should_fail=False):
            if should_fail:
                raise Exception("Test failure")
            return "success"
        
        # Should work normally
        result = protected_func(should_fail=False)
        assert result == "success"
        
        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                protected_func(should_fail=True)
        
        # Circuit should be open
        with pytest.raises(APIIntegrationError):
            protected_func(should_fail=False)


class TestWithRetryDecorator:
    """Test retry decorator"""
    
    def test_decorator_adds_retry_logic(self):
        """Test decorator adds retry logic to function"""
        
        attempt_count = {"count": 0}
        
        @with_retry(max_attempts=3, initial_delay=0.1)
        def flaky_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert attempt_count["count"] == 2


class TestFallbackManager:
    """Test fallback manager"""
    
    def test_register_and_execute_fallback(self):
        """Test registering and executing fallback handlers"""
        manager = FallbackManager()
        
        def primary_func():
            raise Exception("Primary failed")
        
        def fallback_func():
            return "fallback_result"
        
        manager.register_fallback("test_service", fallback_func)
        
        result = manager.execute_with_fallback("test_service", primary_func)
        
        assert result["success"] is True
        assert result["source"] == "fallback"
        assert result["data"] == "fallback_result"
    
    def test_primary_success_no_fallback(self):
        """Test primary function success doesn't trigger fallback"""
        manager = FallbackManager()
        
        def primary_func():
            return "primary_result"
        
        def fallback_func():
            return "fallback_result"
        
        manager.register_fallback("test_service", fallback_func)
        
        result = manager.execute_with_fallback("test_service", primary_func)
        
        assert result["success"] is True
        assert result["source"] == "primary"
        assert result["data"] == "primary_result"
    
    def test_no_fallback_registered(self):
        """Test behavior when no fallback is registered"""
        manager = FallbackManager()
        
        def primary_func():
            raise Exception("Primary failed")
        
        result = manager.execute_with_fallback("test_service", primary_func)
        
        assert result["success"] is False
        assert result["source"] == "none"
        assert "error" in result


class TestErrorMessageGenerator:
    """Test error message generator"""
    
    def test_get_english_message(self):
        """Test getting English error message"""
        generator = ErrorMessageGenerator(default_language="en")
        
        message = generator.get_message("doc_poor_quality", language="en")
        assert "quality is poor" in message.lower()
    
    def test_get_hindi_message(self):
        """Test getting Hindi error message"""
        generator = ErrorMessageGenerator(default_language="en")
        
        message = generator.get_message("doc_poor_quality", language="hi")
        assert "गुणवत्ता" in message
    
    def test_get_marathi_message(self):
        """Test getting Marathi error message"""
        generator = ErrorMessageGenerator(default_language="en")
        
        message = generator.get_message("doc_poor_quality", language="mr")
        assert "गुणवत्ता" in message
    
    def test_fallback_to_default_language(self):
        """Test fallback to default language for unknown language"""
        generator = ErrorMessageGenerator(default_language="en")
        
        message = generator.get_message("doc_poor_quality", language="unknown")
        assert "quality is poor" in message.lower()
    
    def test_fallback_for_unknown_key(self):
        """Test fallback for unknown message key"""
        generator = ErrorMessageGenerator(default_language="en")
        
        message = generator.get_message("unknown_key", language="en")
        assert "error occurred" in message.lower()


class TestHandleError:
    """Test error handling function"""
    
    def test_handle_sarvasahay_error(self):
        """Test handling SarvaSahay error"""
        error = DocumentProcessingError(
            message="Test error",
            severity=ErrorSeverity.HIGH,
            user_message="User message",
            suggested_actions=["Action 1"]
        )
        
        result = handle_error(error, {"key": "value"}, "en")
        
        assert result["success"] is False
        assert result["error"]["code"] == "DOC_ERROR"
        assert result["error"]["message"] == "User message"
        assert result["error"]["severity"] == ErrorSeverity.HIGH
        assert len(result["error"]["suggestedActions"]) == 1
        assert result["context"]["key"] == "value"
    
    def test_handle_generic_error(self):
        """Test handling generic exception"""
        error = ValueError("Generic error")
        
        result = handle_error(error, {}, "en")
        
        assert result["success"] is False
        assert result["error"]["code"] == "GENERIC_ERROR"
        assert "ValueError" in result["error"]["technicalDetails"]
    
    def test_handle_network_error(self):
        """Test handling network-related error"""
        error = Exception("Network connection failed")
        
        result = handle_error(error, {}, "en")
        
        assert result["success"] is False
        assert "network" in result["error"]["message"].lower() or "connection" in result["error"]["message"].lower()


class TestErrorSeverityAndCategory:
    """Test error severity and category enums"""
    
    def test_error_severity_levels(self):
        """Test error severity levels"""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"
    
    def test_error_categories(self):
        """Test error categories"""
        assert ErrorCategory.USER_INPUT == "user_input"
        assert ErrorCategory.SYSTEM_INTEGRATION == "system_integration"
        assert ErrorCategory.PERFORMANCE == "performance"
        assert ErrorCategory.SECURITY == "security"
        assert ErrorCategory.DATA_VALIDATION == "data_validation"
        assert ErrorCategory.NETWORK == "network"
        assert ErrorCategory.RESOURCE == "resource"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
