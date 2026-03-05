"""
Comprehensive Error Handling and Fallback Mechanisms
Provides graceful degradation, circuit breakers, retry logic, and user-friendly error messages
"""

from typing import Dict, Any, Optional, Callable, List, Type
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps
import time
import logging
from dataclasses import dataclass, field


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    USER_INPUT = "user_input"
    SYSTEM_INTEGRATION = "system_integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATA_VALIDATION = "data_validation"
    NETWORK = "network"
    RESOURCE = "resource"


@dataclass
class ErrorContext:
    """Context information for errors"""
    error_code: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    user_message: str
    technical_details: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    fallback_available: bool = False
    fallback_method: Optional[str] = None
    retry_possible: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SarvaSahayError(Exception):
    """Base exception for SarvaSahay platform"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM_INTEGRATION,
        user_message: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        fallback_available: bool = False,
        fallback_method: Optional[str] = None
    ):
        super().__init__(message)
        self.context = ErrorContext(
            error_code=error_code,
            message=message,
            severity=severity,
            category=category,
            user_message=user_message or message,
            technical_details=message,
            suggested_actions=suggested_actions or [],
            fallback_available=fallback_available,
            fallback_method=fallback_method
        )


class DocumentProcessingError(SarvaSahayError):
    """Document processing related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DOC_ERROR",
            category=ErrorCategory.DATA_VALIDATION,
            **kwargs
        )


class APIIntegrationError(SarvaSahayError):
    """Government API integration errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="API_ERROR",
            category=ErrorCategory.SYSTEM_INTEGRATION,
            **kwargs
        )


class TrackingError(SarvaSahayError):
    """Application tracking errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="TRACK_ERROR",
            category=ErrorCategory.SYSTEM_INTEGRATION,
            **kwargs
        )


@dataclass
class CircuitBreakerState:
    """Circuit breaker state management"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open
    success_count: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Prevents cascading failures by failing fast when service is unavailable
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        self.state = CircuitBreakerState()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception if circuit is open
        """
        # Check circuit state
        if self.state.state == "open":
            # Check if timeout has passed
            if self.state.last_failure_time:
                elapsed = (datetime.utcnow() - self.state.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    self.state.state = "half_open"
                    self.state.success_count = 0
                    logger.info("Circuit breaker entering half-open state")
                else:
                    raise APIIntegrationError(
                        message=f"Circuit breaker is open. Service unavailable.",
                        severity=ErrorSeverity.HIGH,
                        user_message="The service is temporarily unavailable. Please try again later.",
                        suggested_actions=[
                            "Wait a few minutes and try again",
                            "Use alternative submission method if available"
                        ],
                        fallback_available=True
                    )
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Record success
            if self.state.state == "half_open":
                self.state.success_count += 1
                if self.state.success_count >= self.success_threshold:
                    self.state.state = "closed"
                    self.state.failure_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
            
            return result
        
        except Exception as e:
            # Record failure
            self.state.failure_count += 1
            self.state.last_failure_time = datetime.utcnow()
            
            if self.state.failure_count >= self.failure_threshold:
                self.state.state = "open"
                logger.error(f"Circuit breaker opened after {self.state.failure_count} failures")
            
            raise e
    
    def reset(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitBreakerState()
        logger.info("Circuit breaker manually reset")


class RetryStrategy:
    """
    Retry strategy with exponential backoff
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def execute(
        self,
        func: Callable,
        *args,
        retry_on: Optional[List[Type[Exception]]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            retry_on: List of exception types to retry on
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        retry_on = retry_on or [Exception]
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this exception
                should_retry = any(isinstance(e, exc_type) for exc_type in retry_on)
                
                if not should_retry or attempt == self.max_attempts - 1:
                    raise e
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.initial_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                # Add jitter to prevent thundering herd
                if self.jitter:
                    import random
                    delay *= (0.5 + random.random())
                
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                time.sleep(delay)
        
        raise last_exception


def with_circuit_breaker(
    failure_threshold: int = 5,
    timeout_seconds: int = 60
):
    """
    Decorator to add circuit breaker protection to functions
    
    Args:
        failure_threshold: Number of failures before opening circuit
        timeout_seconds: Seconds to wait before attempting recovery
    """
    circuit_breaker = CircuitBreaker(failure_threshold, timeout_seconds)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)
        
        wrapper.circuit_breaker = circuit_breaker
        return wrapper
    
    return decorator


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None
):
    """
    Decorator to add retry logic to functions
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries
        retry_on: List of exception types to retry on
    """
    retry_strategy = RetryStrategy(max_attempts=max_attempts, initial_delay=initial_delay)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_strategy.execute(func, *args, retry_on=retry_on, **kwargs)
        
        return wrapper
    
    return decorator


class FallbackManager:
    """
    Manages fallback mechanisms for service failures
    """
    
    def __init__(self):
        self.fallback_handlers: Dict[str, Callable] = {}
    
    def register_fallback(self, service_name: str, handler: Callable):
        """
        Register fallback handler for a service
        
        Args:
            service_name: Name of the service
            handler: Fallback handler function
        """
        self.fallback_handlers[service_name] = handler
        logger.info(f"Registered fallback handler for {service_name}")
    
    def execute_with_fallback(
        self,
        service_name: str,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute function with fallback on failure
        
        Args:
            service_name: Name of the service
            primary_func: Primary function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Result from primary or fallback function
        """
        try:
            result = primary_func(*args, **kwargs)
            return {
                "success": True,
                "source": "primary",
                "data": result
            }
        
        except Exception as e:
            logger.error(f"Primary function failed for {service_name}: {str(e)}")
            
            # Try fallback if available
            if service_name in self.fallback_handlers:
                try:
                    fallback_result = self.fallback_handlers[service_name](*args, **kwargs)
                    logger.info(f"Fallback successful for {service_name}")
                    return {
                        "success": True,
                        "source": "fallback",
                        "data": fallback_result,
                        "primary_error": str(e)
                    }
                
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {service_name}: {str(fallback_error)}")
            
            # Both primary and fallback failed
            return {
                "success": False,
                "source": "none",
                "error": str(e),
                "fallback_available": service_name in self.fallback_handlers
            }


class ErrorMessageGenerator:
    """
    Generates user-friendly error messages in multiple languages
    """
    
    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.messages = self._load_messages()
    
    def _load_messages(self) -> Dict[str, Dict[str, str]]:
        """Load error messages for different languages"""
        return {
            "en": {
                "doc_poor_quality": "The document image quality is poor. Please retake the photo in better lighting.",
                "doc_unreadable": "The document is unreadable. Please ensure the document is clear and all text is visible.",
                "api_unavailable": "The government service is temporarily unavailable. Please try again later.",
                "api_timeout": "The request timed out. Please check your internet connection and try again.",
                "validation_failed": "The information provided could not be validated. Please check and try again.",
                "network_error": "Network connection error. Please check your internet connection.",
                "service_degraded": "The service is experiencing issues. Some features may be unavailable.",
                "submission_failed": "Application submission failed. You can submit manually at the government office.",
                "tracking_unavailable": "Application tracking is temporarily unavailable. Your application is still being processed.",
                "payment_check_failed": "Unable to check payment status. Please try again later or contact support."
            },
            "hi": {
                "doc_poor_quality": "दस्तावेज़ की छवि की गुणवत्ता खराब है। कृपया बेहतर रोशनी में फोटो फिर से लें।",
                "doc_unreadable": "दस्तावेज़ पढ़ने योग्य नहीं है। कृपया सुनिश्चित करें कि दस्तावेज़ स्पष्ट है।",
                "api_unavailable": "सरकारी सेवा अस्थायी रूप से अनुपलब्ध है। कृपया बाद में पुनः प्रयास करें।",
                "api_timeout": "अनुरोध समय समाप्त हो गया। कृपया अपना इंटरनेट कनेक्शन जांचें।",
                "validation_failed": "प्रदान की गई जानकारी मान्य नहीं हो सकी। कृपया जांचें और पुनः प्रयास करें।",
                "network_error": "नेटवर्क कनेक्शन त्रुटि। कृपया अपना इंटरनेट कनेक्शन जांचें।",
                "service_degraded": "सेवा में समस्याएं हैं। कुछ सुविधाएं अनुपलब्ध हो सकती हैं।",
                "submission_failed": "आवेदन जमा करना विफल रहा। आप सरकारी कार्यालय में मैन्युअल रूप से जमा कर सकते हैं।",
                "tracking_unavailable": "आवेदन ट्रैकिंग अस्थायी रूप से अनुपलब्ध है। आपका आवेदन अभी भी संसाधित हो रहा है।",
                "payment_check_failed": "भुगतान स्थिति जांचने में असमर्थ। कृपया बाद में पुनः प्रयास करें।"
            },
            "mr": {
                "doc_poor_quality": "दस्तऐवजाची प्रतिमा गुणवत्ता खराब आहे. कृपया चांगल्या प्रकाशात फोटो पुन्हा घ्या.",
                "doc_unreadable": "दस्तऐवज वाचण्यायोग्य नाही. कृपया दस्तऐवज स्पष्ट असल्याची खात्री करा.",
                "api_unavailable": "सरकारी सेवा तात्पुरती अनुपलब्ध आहे. कृपया नंतर पुन्हा प्रयत्न करा.",
                "api_timeout": "विनंती कालबाह्य झाली. कृपया आपले इंटरनेट कनेक्शन तपासा.",
                "validation_failed": "प्रदान केलेली माहिती प्रमाणित करता आली नाही. कृपया तपासा आणि पुन्हा प्रयत्न करा.",
                "network_error": "नेटवर्क कनेक्शन त्रुटी. कृपया आपले इंटरनेट कनेक्शन तपासा.",
                "service_degraded": "सेवेत समस्या आहेत. काही वैशिष्ट्ये अनुपलब्ध असू शकतात.",
                "submission_failed": "अर्ज सबमिट करणे अयशस्वी झाले. आपण सरकारी कार्यालयात मॅन्युअली सबमिट करू शकता.",
                "tracking_unavailable": "अर्ज ट्रॅकिंग तात्पुरते अनुपलब्ध आहे. आपला अर्ज अद्याप प्रक्रिया केला जात आहे.",
                "payment_check_failed": "पेमेंट स्थिती तपासण्यात अक्षम. कृपया नंतर पुन्हा प्रयत्न करा."
            }
        }
    
    def get_message(
        self,
        message_key: str,
        language: Optional[str] = None,
        **format_args
    ) -> str:
        """
        Get user-friendly error message
        
        Args:
            message_key: Message key
            language: Language code (en, hi, mr)
            **format_args: Format arguments for message
            
        Returns:
            Localized error message
        """
        lang = language or self.default_language
        
        if lang not in self.messages:
            lang = self.default_language
        
        message = self.messages[lang].get(
            message_key,
            self.messages[self.default_language].get(message_key, "An error occurred")
        )
        
        if format_args:
            try:
                message = message.format(**format_args)
            except KeyError:
                pass
        
        return message


# Global instances
fallback_manager = FallbackManager()
error_message_generator = ErrorMessageGenerator()


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Handle error and generate user-friendly response
    
    Args:
        error: Exception that occurred
        context: Additional context information
        language: User's preferred language
        
    Returns:
        Error response with user-friendly message and suggested actions
    """
    context = context or {}
    
    # Check if it's a SarvaSahay error with context
    if isinstance(error, SarvaSahayError):
        return {
            "success": False,
            "error": {
                "code": error.context.error_code,
                "message": error.context.user_message,
                "severity": error.context.severity,
                "category": error.context.category,
                "suggestedActions": error.context.suggested_actions,
                "fallbackAvailable": error.context.fallback_available,
                "fallbackMethod": error.context.fallback_method,
                "retryPossible": error.context.retry_possible,
                "timestamp": error.context.timestamp.isoformat()
            },
            "context": context
        }
    
    # Handle generic errors
    error_type = type(error).__name__
    error_message = str(error)
    
    # Map to user-friendly message
    message_key = "service_degraded"
    if "network" in error_message.lower() or "connection" in error_message.lower():
        message_key = "network_error"
    elif "timeout" in error_message.lower():
        message_key = "api_timeout"
    elif "validation" in error_message.lower():
        message_key = "validation_failed"
    
    user_message = error_message_generator.get_message(message_key, language)
    
    return {
        "success": False,
        "error": {
            "code": "GENERIC_ERROR",
            "message": user_message,
            "severity": ErrorSeverity.MEDIUM,
            "category": ErrorCategory.SYSTEM_INTEGRATION,
            "suggestedActions": [
                "Please try again in a few minutes",
                "Contact support if the problem persists"
            ],
            "technicalDetails": f"{error_type}: {error_message}",
            "timestamp": datetime.utcnow().isoformat()
        },
        "context": context
    }
