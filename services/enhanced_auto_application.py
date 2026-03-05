"""
Enhanced Auto-Application Service with Comprehensive Error Handling
Implements graceful degradation and fallback mechanisms for application submission
"""

from typing import Dict, Any, Optional, List
from services.auto_application_service import AutoApplicationService
from services.government_api_client import APIError
from shared.utils.error_handling import (
    APIIntegrationError,
    ErrorSeverity,
    with_circuit_breaker,
    with_retry,
    handle_error,
    error_message_generator,
    fallback_manager
)
import logging

logger = logging.getLogger(__name__)


class EnhancedAutoApplicationService(AutoApplicationService):
    """
    Enhanced auto-application service with error handling and fallback mechanisms
    """
    
    def __init__(
        self,
        pm_kisan_key: Optional[str] = None,
        dbt_key: Optional[str] = None,
        pfms_key: Optional[str] = None
    ):
        super().__init__(pm_kisan_key, dbt_key, pfms_key)
        self._register_fallbacks()
        self.offline_queue = []
    
    def _register_fallbacks(self):
        """Register fallback handlers for API failures"""
        fallback_manager.register_fallback(
            "application_submission",
            self._fallback_manual_submission
        )
        fallback_manager.register_fallback(
            "status_check",
            self._fallback_cached_status
        )
    
    @with_circuit_breaker(failure_threshold=5, timeout_seconds=300)
    @with_retry(max_attempts=3, initial_delay=2.0)
    def submit_application_safe(
        self,
        application_id: str,
        user_approval: bool = True,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Submit application with comprehensive error handling and fallback
        
        Args:
            application_id: Application identifier
            user_approval: User approval confirmation
            language: User's preferred language
            
        Returns:
            Submission result with fallback handling
        """
        try:
            # Validate application exists
            application = self.applications.get(application_id)
            if not application:
                raise APIIntegrationError(
                    message=f"Application not found: {application_id}",
                    severity=ErrorSeverity.HIGH,
                    user_message="Application not found. Please create a new application.",
                    suggested_actions=[
                        "Verify the application ID",
                        "Create a new application if needed"
                    ]
                )
            
            # Check user approval
            if not user_approval:
                return {
                    "success": False,
                    "applicationId": application_id,
                    "status": "approval_required",
                    "message": "User approval is required to submit the application"
                }
            
            # Validate application
            validation = self.validate_application(application_id)
            if not validation["isValid"]:
                raise APIIntegrationError(
                    message="Application validation failed",
                    severity=ErrorSeverity.MEDIUM,
                    user_message=error_message_generator.get_message("validation_failed", language),
                    suggested_actions=[
                        "Review and correct the highlighted errors",
                        "Ensure all required fields are filled",
                        "Upload any missing documents"
                    ] + [f"• {error}" for error in validation.get("errors", [])]
                )
            
            # Attempt submission
            result = self.submit_application(application_id, user_approval)
            
            # Check if submission failed
            if result.get("status") == "submission_failed":
                # Provide fallback instructions
                fallback_info = self._get_fallback_instructions(
                    application.scheme_id,
                    language
                )
                
                result["fallback"] = fallback_info
                result["error"]["suggestedActions"] = fallback_info["instructions"]
                
                # Queue for offline submission if possible
                self._queue_offline_submission(application_id, application)
                result["queuedForRetry"] = True
            
            return result
        
        except APIIntegrationError as e:
            logger.error(f"API integration error: {str(e)}")
            error_response = handle_error(e, {"applicationId": application_id}, language)
            
            # Add fallback information
            fallback_info = self._get_fallback_instructions(
                self.applications[application_id].scheme_id if application_id in self.applications else "unknown",
                language
            )
            error_response["fallback"] = fallback_info
            
            return error_response
        
        except Exception as e:
            logger.error(f"Unexpected error in application submission: {str(e)}")
            error_response = handle_error(e, {"applicationId": application_id}, language)
            
            # Provide fallback
            error_response["error"]["fallbackAvailable"] = True
            error_response["error"]["fallbackMethod"] = "manual_submission"
            
            return error_response
    
    def _get_fallback_instructions(
        self,
        scheme_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get fallback instructions for manual submission
        
        Args:
            scheme_id: Government scheme identifier
            language: User's preferred language
            
        Returns:
            Fallback instructions and required documents
        """
        # Scheme-specific fallback information
        fallback_data = {
            "pm_kisan": {
                "office": "Agriculture Department Office",
                "website": "https://pmkisan.gov.in",
                "helpline": "155261 / 011-24300606",
                "documents": ["Aadhaar Card", "Bank Passbook", "Land Records"]
            },
            "default": {
                "office": "District Collectorate or Block Development Office",
                "website": "Contact local government office",
                "helpline": "Contact local government helpline",
                "documents": ["Aadhaar Card", "Income Certificate", "Caste Certificate"]
            }
        }
        
        info = fallback_data.get(scheme_id, fallback_data["default"])
        
        instructions = [
            f"Visit your nearest {info['office']}",
            f"Bring the following documents: {', '.join(info['documents'])}",
            f"You can also apply online at: {info['website']}",
            f"For assistance, call helpline: {info['helpline']}"
        ]
        
        if language == "hi":
            instructions = [
                f"अपने निकटतम {info['office']} पर जाएं",
                f"निम्नलिखित दस्तावेज़ लाएं: {', '.join(info['documents'])}",
                f"आप ऑनलाइन भी आवेदन कर सकते हैं: {info['website']}",
                f"सहायता के लिए हेल्पलाइन पर कॉल करें: {info['helpline']}"
            ]
        elif language == "mr":
            instructions = [
                f"आपल्या जवळच्या {info['office']} ला भेट द्या",
                f"खालील कागदपत्रे आणा: {', '.join(info['documents'])}",
                f"आपण ऑनलाइन देखील अर्ज करू शकता: {info['website']}",
                f"मदतीसाठी हेल्पलाइनवर कॉल करा: {info['helpline']}"
            ]
        
        return {
            "method": "manual_submission",
            "office": info["office"],
            "website": info["website"],
            "helpline": info["helpline"],
            "requiredDocuments": info["documents"],
            "instructions": instructions
        }
    
    def _fallback_manual_submission(
        self,
        application_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fallback handler for manual submission
        
        Args:
            application_id: Application identifier
            
        Returns:
            Manual submission instructions
        """
        application = self.applications.get(application_id)
        if not application:
            return {"error": "Application not found"}
        
        return {
            "method": "manual",
            "applicationId": application_id,
            "schemeId": application.scheme_id,
            "instructions": self._get_fallback_instructions(application.scheme_id),
            "formData": application.form_data,
            "message": "Please submit this application manually at the government office"
        }
    
    def _fallback_cached_status(
        self,
        application_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fallback handler for status check using cached data
        
        Args:
            application_id: Application identifier
            
        Returns:
            Cached status information
        """
        application = self.applications.get(application_id)
        if not application:
            return {"error": "Application not found"}
        
        return {
            "applicationId": application_id,
            "status": application.status,
            "lastUpdated": application.updated_at.isoformat(),
            "source": "cached",
            "message": "Showing cached status. Real-time status unavailable."
        }
    
    def _queue_offline_submission(
        self,
        application_id: str,
        application: Any
    ):
        """
        Queue application for retry when service is restored
        
        Args:
            application_id: Application identifier
            application: Application object
        """
        queue_item = {
            "applicationId": application_id,
            "schemeId": application.scheme_id,
            "formData": application.form_data,
            "queuedAt": application.updated_at.isoformat(),
            "retryCount": 0
        }
        
        self.offline_queue.append(queue_item)
        logger.info(f"Application {application_id} queued for offline retry")
    
    def process_offline_queue(self) -> Dict[str, Any]:
        """
        Process queued applications when service is restored
        
        Returns:
            Processing results
        """
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        queue_copy = self.offline_queue.copy()
        self.offline_queue.clear()
        
        for item in queue_copy:
            try:
                result = self.submit_application(
                    item["applicationId"],
                    user_approval=True
                )
                
                if result.get("status") == "submitted":
                    results["successful"] += 1
                    results["details"].append({
                        "applicationId": item["applicationId"],
                        "status": "success"
                    })
                else:
                    results["failed"] += 1
                    # Re-queue if still failing
                    item["retryCount"] += 1
                    if item["retryCount"] < 3:
                        self.offline_queue.append(item)
                    
                    results["details"].append({
                        "applicationId": item["applicationId"],
                        "status": "failed",
                        "error": result.get("error")
                    })
                
                results["processed"] += 1
            
            except Exception as e:
                logger.error(f"Error processing queued application: {str(e)}")
                results["failed"] += 1
                results["details"].append({
                    "applicationId": item["applicationId"],
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def get_offline_queue_status(self) -> Dict[str, Any]:
        """Get status of offline submission queue"""
        return {
            "queueLength": len(self.offline_queue),
            "applications": [
                {
                    "applicationId": item["applicationId"],
                    "schemeId": item["schemeId"],
                    "queuedAt": item["queuedAt"],
                    "retryCount": item["retryCount"]
                }
                for item in self.offline_queue
            ]
        }
    
    def get_api_health_safe(self, language: str = "en") -> Dict[str, Any]:
        """
        Get API health status with error handling
        
        Args:
            language: User's preferred language
            
        Returns:
            Health status with fallback information
        """
        try:
            health = self.get_api_health()
            
            # Check for degraded services
            degraded_services = [
                service for service, status in health.items()
                if status.get("status") != "healthy"
            ]
            
            if degraded_services:
                health["warning"] = {
                    "message": error_message_generator.get_message("service_degraded", language),
                    "degradedServices": degraded_services,
                    "fallbackAvailable": True
                }
            
            return health
        
        except Exception as e:
            logger.error(f"Error checking API health: {str(e)}")
            return {
                "status": "unknown",
                "error": str(e),
                "message": error_message_generator.get_message("api_unavailable", language),
                "fallbackAvailable": True
            }
