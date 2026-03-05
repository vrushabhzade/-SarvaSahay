"""
Enhanced Tracking Service with Comprehensive Error Handling
Implements graceful degradation and fallback mechanisms for application tracking
"""

from typing import Dict, Any, Optional, List
from services.tracking_service import TrackingService, TrackingConfig
from services.government_api_client import GovernmentAPIIntegration
from shared.models.application import Application
from shared.utils.error_handling import (
    TrackingError,
    ErrorSeverity,
    with_retry,
    handle_error,
    error_message_generator,
    fallback_manager
)
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EnhancedTrackingService(TrackingService):
    """
    Enhanced tracking service with error handling and fallback mechanisms
    """
    
    def __init__(
        self,
        gov_api: GovernmentAPIIntegration,
        config: Optional[TrackingConfig] = None
    ):
        super().__init__(gov_api, config)
        self._register_fallbacks()
        self.cached_statuses = {}
        self.cache_ttl_seconds = 3600  # 1 hour cache
    
    def _register_fallbacks(self):
        """Register fallback handlers for tracking failures"""
        fallback_manager.register_fallback(
            "tracking_poll",
            self._fallback_cached_tracking
        )
        fallback_manager.register_fallback(
            "payment_tracking",
            self._fallback_estimated_payment
        )
    
    def poll_application_safe(
        self,
        application_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Poll application with comprehensive error handling
        
        Args:
            application_id: Application identifier
            language: User's preferred language
            
        Returns:
            Poll result with fallback handling
        """
        try:
            # Check if application is registered
            if application_id not in self.trackers:
                raise TrackingError(
                    message=f"Application not registered for tracking: {application_id}",
                    severity=ErrorSeverity.MEDIUM,
                    user_message="This application is not being tracked. Please register it first.",
                    suggested_actions=[
                        "Register the application for tracking",
                        "Verify the application ID is correct"
                    ]
                )
            
            # Attempt to poll with retry
            result = self._poll_with_fallback(application_id)
            
            # Check if polling failed
            if not result.get("success"):
                # Use cached status if available
                cached_status = self._get_cached_status(application_id)
                if cached_status:
                    result = {
                        "success": True,
                        "source": "cached",
                        "applicationId": application_id,
                        "statusResult": cached_status,
                        "warning": {
                            "message": error_message_generator.get_message("tracking_unavailable", language),
                            "severity": "low",
                            "suggestedActions": [
                                "Real-time tracking is temporarily unavailable",
                                "Showing last known status",
                                "Try again later for updated status"
                            ]
                        },
                        "cachedAt": cached_status.get("lastUpdated")
                    }
                else:
                    # No cached data available
                    raise TrackingError(
                        message="Unable to fetch application status",
                        severity=ErrorSeverity.MEDIUM,
                        user_message=error_message_generator.get_message("tracking_unavailable", language),
                        suggested_actions=[
                            "Try again in a few minutes",
                            "Your application is still being processed",
                            "Contact the government office for manual status check"
                        ],
                        fallback_available=True,
                        fallback_method="manual_check"
                    )
            else:
                # Cache successful result
                self._cache_status(application_id, result)
            
            return result
        
        except TrackingError as e:
            logger.error(f"Tracking error: {str(e)}")
            return handle_error(e, {"applicationId": application_id}, language)
        
        except Exception as e:
            logger.error(f"Unexpected error in tracking: {str(e)}")
            error_response = handle_error(e, {"applicationId": application_id}, language)
            
            # Try to provide cached status
            cached_status = self._get_cached_status(application_id)
            if cached_status:
                error_response["cachedStatus"] = cached_status
                error_response["message"] = "Showing last known status due to tracking error"
            
            return error_response
    
    @with_retry(max_attempts=2, initial_delay=1.0)
    def _poll_with_fallback(self, application_id: str) -> Dict[str, Any]:
        """
        Poll with retry logic
        
        Args:
            application_id: Application identifier
            
        Returns:
            Poll result
        """
        return self.poll_application(application_id)
    
    def _cache_status(self, application_id: str, status_data: Dict[str, Any]):
        """
        Cache application status
        
        Args:
            application_id: Application identifier
            status_data: Status data to cache
        """
        self.cached_statuses[application_id] = {
            "data": status_data,
            "cachedAt": datetime.utcnow(),
            "expiresAt": datetime.utcnow() + timedelta(seconds=self.cache_ttl_seconds)
        }
    
    def _get_cached_status(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached status if available and not expired
        
        Args:
            application_id: Application identifier
            
        Returns:
            Cached status or None
        """
        cached = self.cached_statuses.get(application_id)
        if not cached:
            return None
        
        # Check if expired
        if datetime.utcnow() > cached["expiresAt"]:
            del self.cached_statuses[application_id]
            return None
        
        return cached["data"]
    
    def _fallback_cached_tracking(
        self,
        application_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fallback handler using cached tracking data
        
        Args:
            application_id: Application identifier
            
        Returns:
            Cached tracking information
        """
        cached = self._get_cached_status(application_id)
        if cached:
            return {
                "success": True,
                "source": "cached",
                "data": cached,
                "message": "Showing cached status. Real-time tracking unavailable."
            }
        
        # No cache available
        tracker = self.trackers.get(application_id)
        if tracker:
            return {
                "success": True,
                "source": "local",
                "applicationId": application_id,
                "status": tracker.application.status,
                "lastChecked": tracker.last_checked.isoformat() if tracker.last_checked else None,
                "message": "Showing local status. Real-time tracking unavailable."
            }
        
        return {
            "success": False,
            "error": "No cached or local status available"
        }
    
    def _fallback_estimated_payment(
        self,
        application_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fallback handler for payment tracking using estimates
        
        Args:
            application_id: Application identifier
            
        Returns:
            Estimated payment information
        """
        tracker = self.trackers.get(application_id)
        if not tracker or not tracker.application.predictions:
            return {
                "success": False,
                "error": "No payment estimation available"
            }
        
        # Provide estimated payment timeline
        predictions = tracker.predict_approval_timeline()
        
        return {
            "success": True,
            "source": "estimated",
            "applicationId": application_id,
            "estimatedPaymentDate": predictions.get("expectedCompletionDate"),
            "confidence": predictions.get("confidence"),
            "message": "Payment tracking unavailable. Showing estimated timeline.",
            "note": "This is an estimate. Actual payment may vary."
        }
    
    def get_status_with_guidance(
        self,
        application_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get application status with user guidance
        
        Args:
            application_id: Application identifier
            language: User's preferred language
            
        Returns:
            Status with guidance and suggested actions
        """
        try:
            status = self.get_application_status(application_id)
            
            if not status.get("success"):
                return status
            
            # Add guidance based on status
            current_status = status.get("currentStatus")
            guidance = self._get_status_guidance(current_status, language)
            
            status["guidance"] = guidance
            
            # Check for delays
            tracker = self.trackers.get(application_id)
            if tracker:
                delay_event = tracker.check_for_delays()
                if delay_event:
                    status["delayWarning"] = {
                        "message": "Your application is taking longer than expected",
                        "delayDays": delay_event.get("delayDays"),
                        "suggestedActions": delay_event.get("suggestedActions")
                    }
            
            return status
        
        except Exception as e:
            logger.error(f"Error getting status with guidance: {str(e)}")
            return handle_error(e, {"applicationId": application_id}, language)
    
    def _get_status_guidance(
        self,
        status: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get user guidance based on application status
        
        Args:
            status: Current application status
            language: User's preferred language
            
        Returns:
            Guidance information
        """
        guidance_map = {
            "submitted": {
                "en": {
                    "message": "Your application has been submitted successfully",
                    "nextSteps": [
                        "Your application is being reviewed",
                        "You will receive updates via SMS",
                        "Typical processing time is 30-45 days"
                    ]
                },
                "hi": {
                    "message": "आपका आवेदन सफलतापूर्वक जमा हो गया है",
                    "nextSteps": [
                        "आपके आवेदन की समीक्षा की जा रही है",
                        "आपको एसएमएस के माध्यम से अपडेट मिलेगा",
                        "सामान्य प्रसंस्करण समय 30-45 दिन है"
                    ]
                }
            },
            "under_review": {
                "en": {
                    "message": "Your application is under review",
                    "nextSteps": [
                        "Officials are verifying your documents",
                        "Ensure your phone is reachable for any clarifications",
                        "Decision expected within 15-20 days"
                    ]
                },
                "hi": {
                    "message": "आपका आवेदन समीक्षाधीन है",
                    "nextSteps": [
                        "अधिकारी आपके दस्तावेज़ों की जांच कर रहे हैं",
                        "किसी भी स्पष्टीकरण के लिए अपना फोन पहुंच योग्य रखें",
                        "15-20 दिनों के भीतर निर्णय की उम्मीद है"
                    ]
                }
            },
            "approved": {
                "en": {
                    "message": "Congratulations! Your application has been approved",
                    "nextSteps": [
                        "Payment will be processed within 7-10 days",
                        "Amount will be credited to your registered bank account",
                        "You will receive SMS confirmation when payment is made"
                    ]
                },
                "hi": {
                    "message": "बधाई हो! आपका आवेदन स्वीकृत हो गया है",
                    "nextSteps": [
                        "7-10 दिनों के भीतर भुगतान संसाधित किया जाएगा",
                        "राशि आपके पंजीकृत बैंक खाते में जमा की जाएगी",
                        "भुगतान होने पर आपको एसएमएस पुष्टि मिलेगी"
                    ]
                }
            },
            "rejected": {
                "en": {
                    "message": "Your application was not approved",
                    "nextSteps": [
                        "Review the rejection reason carefully",
                        "You may be eligible to reapply after addressing issues",
                        "Contact the government office for clarification",
                        "Explore other schemes you may be eligible for"
                    ]
                },
                "hi": {
                    "message": "आपका आवेदन स्वीकृत नहीं हुआ",
                    "nextSteps": [
                        "अस्वीकृति के कारण की सावधानीपूर्वक समीक्षा करें",
                        "समस्याओं को हल करने के बाद आप फिर से आवेदन कर सकते हैं",
                        "स्पष्टीकरण के लिए सरकारी कार्यालय से संपर्क करें",
                        "अन्य योजनाओं का पता लगाएं जिनके लिए आप पात्र हो सकते हैं"
                    ]
                }
            }
        }
        
        lang_guidance = guidance_map.get(status, {}).get(language)
        if not lang_guidance:
            lang_guidance = guidance_map.get(status, {}).get("en", {
                "message": "Application status updated",
                "nextSteps": ["Check back later for updates"]
            })
        
        return lang_guidance
    
    def get_manual_check_instructions(
        self,
        application_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get instructions for manual status check when tracking fails
        
        Args:
            application_id: Application identifier
            language: User's preferred language
            
        Returns:
            Manual check instructions
        """
        tracker = self.trackers.get(application_id)
        if not tracker:
            return {"error": "Application not found"}
        
        application = tracker.application
        
        instructions = {
            "en": {
                "title": "Manual Status Check Instructions",
                "steps": [
                    f"Visit the government office or website for {application.scheme_id}",
                    f"Use your reference number: {application.government_ref_number}",
                    "Contact the helpline for status updates",
                    "Visit during office hours with your application documents"
                ],
                "referenceNumber": application.government_ref_number,
                "schemeId": application.scheme_id
            },
            "hi": {
                "title": "मैनुअल स्थिति जांच निर्देश",
                "steps": [
                    f"{application.scheme_id} के लिए सरकारी कार्यालय या वेबसाइट पर जाएं",
                    f"अपना संदर्भ नंबर उपयोग करें: {application.government_ref_number}",
                    "स्थिति अपडेट के लिए हेल्पलाइन से संपर्क करें",
                    "अपने आवेदन दस्तावेज़ों के साथ कार्यालय समय के दौरान जाएं"
                ],
                "referenceNumber": application.government_ref_number,
                "schemeId": application.scheme_id
            }
        }
        
        return instructions.get(language, instructions["en"])
