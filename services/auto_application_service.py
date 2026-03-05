"""
Auto-Application Service
Automated form filling and submission to government portals
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from services.form_template_manager import FormTemplateManager
from services.government_api_client import GovernmentAPIIntegration, APIError
from shared.models.application import (
    Application, ApplicationStatus, ApplicationCreate,
    ApplicationPredictions, StatusHistory
)


class AutoApplicationService:
    """
    Handles automated application creation, form filling, and submission
    Integrates with government APIs for direct submission
    """
    
    def __init__(
        self,
        pm_kisan_key: Optional[str] = None,
        dbt_key: Optional[str] = None,
        pfms_key: Optional[str] = None
    ):
        self.form_manager = FormTemplateManager()
        self.gov_api = GovernmentAPIIntegration(pm_kisan_key, dbt_key, pfms_key)
        self.applications: Dict[str, Application] = {}
    
    def create_application(
        self,
        user_id: str,
        scheme_id: str,
        user_profile: Dict[str, Any],
        document_data: Optional[Dict[str, Any]] = None,
        predictions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new application with auto-populated form data
        
        Args:
            user_id: User profile identifier
            scheme_id: Government scheme identifier
            user_profile: User profile data for auto-population
            document_data: Extracted document data
            predictions: AI predictions for approval probability
            
        Returns:
            Created application with pre-filled form
        """
        # Auto-populate form using template manager
        populated_form = self.form_manager.auto_populate_form(
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        # Create application
        application_id = str(uuid.uuid4())
        
        # Convert predictions if provided
        app_predictions = None
        if predictions:
            app_predictions = ApplicationPredictions(
                approval_probability=predictions.get("approvalProbability", 0.5),
                expected_processing_days=predictions.get("expectedProcessingDays", 30),
                confidence_score=predictions.get("confidenceScore", 0.5),
                suggested_improvements=predictions.get("suggestedImprovements", []),
                risk_factors=predictions.get("riskFactors", [])
            )
        
        application = Application(
            application_id=application_id,
            user_id=user_id,
            scheme_id=scheme_id,
            form_data=populated_form["formData"],
            submitted_documents=document_data.get("documentIds", []) if document_data else [],
            status=ApplicationStatus.DRAFT,
            predictions=app_predictions
        )
        
        self.applications[application_id] = application
        
        return {
            "applicationId": application_id,
            "schemeId": scheme_id,
            "schemeName": populated_form["schemeName"],
            "formData": populated_form["formData"],
            "status": "draft",
            "populatedAt": populated_form["populatedAt"],
            "predictions": predictions
        }
    
    def validate_application(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Validate application form data
        
        Args:
            application_id: Application identifier
            
        Returns:
            Validation result with errors if any
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        validation_result = self.form_manager.validate_form(
            scheme_id=application.scheme_id,
            form_data=application.form_data
        )
        
        return validation_result
    
    def preview_application(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Generate application preview for user review
        
        Args:
            application_id: Application identifier
            
        Returns:
            Formatted preview data
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        preview = self.form_manager.generate_preview(
            scheme_id=application.scheme_id,
            form_data=application.form_data
        )
        
        # Add application metadata
        preview["applicationId"] = application_id
        preview["status"] = application.status
        preview["createdAt"] = application.created_at.isoformat()
        
        if application.predictions:
            preview["predictions"] = {
                "approvalProbability": application.predictions.approval_probability,
                "expectedProcessingDays": application.predictions.expected_processing_days,
                "suggestedImprovements": application.predictions.suggested_improvements
            }
        
        return preview
    
    def update_application(
        self,
        application_id: str,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update application form data
        
        Args:
            application_id: Application identifier
            form_data: Updated form data
            
        Returns:
            Updated application
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Cannot update application in {application.status} status")
        
        application.form_data.update(form_data)
        application.updated_at = datetime.utcnow()
        
        return {
            "applicationId": application_id,
            "formData": application.form_data,
            "updatedAt": application.updated_at.isoformat()
        }
    
    def submit_application(
        self,
        application_id: str,
        user_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Submit application to government portal via API integration
        Includes circuit breaker and retry logic for resilience
        
        Args:
            application_id: Application identifier
            user_approval: User approval confirmation
            
        Returns:
            Submission result with reference number
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        if not user_approval:
            raise ValueError("User approval required for submission")
        
        # Validate before submission
        validation = self.validate_application(application_id)
        if not validation["isValid"]:
            raise ValueError(f"Application validation failed: {validation['errors']}")
        
        # Submit to government API with circuit breaker and retry
        try:
            submission_result = self.gov_api.submit_application(
                scheme_id=application.scheme_id,
                application_data=application.form_data
            )
            
            if submission_result.get("success"):
                # Update status to submitted
                application.add_status_change(
                    new_status=ApplicationStatus.SUBMITTED,
                    reason="Application submitted to government portal via API",
                    updated_by="system"
                )
                application.submitted_at = datetime.utcnow()
                application.government_ref_number = submission_result["referenceNumber"]
                
                return {
                    "applicationId": application_id,
                    "status": "submitted",
                    "governmentRefNumber": submission_result["referenceNumber"],
                    "submittedAt": application.submitted_at.isoformat(),
                    "message": submission_result.get("message", "Application submitted successfully")
                }
            else:
                # API submission failed, provide fallback
                application.retry_count += 1
                application.error_messages.append(submission_result.get("error", "Submission failed"))
                
                return {
                    "applicationId": application_id,
                    "status": "submission_failed",
                    "error": submission_result.get("error"),
                    "fallbackMethod": submission_result.get("fallbackMethod"),
                    "instructions": submission_result.get("instructions"),
                    "requiredDocuments": submission_result.get("requiredDocuments", [])
                }
        
        except Exception as e:
            # Handle unexpected errors
            application.retry_count += 1
            application.error_messages.append(str(e))
            
            return {
                "applicationId": application_id,
                "status": "submission_failed",
                "error": str(e),
                "fallbackMethod": "manual",
                "instructions": "Please visit the nearest government office to submit your application manually."
            }
    
    def get_application(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Get application details
        
        Args:
            application_id: Application identifier
            
        Returns:
            Application details
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        return {
            "applicationId": application.application_id,
            "userId": application.user_id,
            "schemeId": application.scheme_id,
            "formData": application.form_data,
            "status": application.status,
            "governmentRefNumber": application.government_ref_number,
            "submittedAt": application.submitted_at.isoformat() if application.submitted_at else None,
            "createdAt": application.created_at.isoformat(),
            "updatedAt": application.updated_at.isoformat(),
            "statusHistory": [
                {
                    "status": h.status,
                    "timestamp": h.timestamp.isoformat(),
                    "reason": h.reason
                }
                for h in application.status_history
            ]
        }
    
    def list_user_applications(
        self,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all applications for a user
        
        Args:
            user_id: User identifier
            status_filter: Optional status filter
            
        Returns:
            List of applications
        """
        user_apps = [
            app for app in self.applications.values()
            if app.user_id == user_id
        ]
        
        if status_filter:
            user_apps = [
                app for app in user_apps
                if app.status == status_filter
            ]
        
        return [
            {
                "applicationId": app.application_id,
                "schemeId": app.scheme_id,
                "status": app.status,
                "governmentRefNumber": app.government_ref_number,
                "submittedAt": app.submitted_at.isoformat() if app.submitted_at else None,
                "createdAt": app.created_at.isoformat()
            }
            for app in sorted(user_apps, key=lambda x: x.created_at, reverse=True)
        ]
    
    def bulk_create_applications(
        self,
        user_id: str,
        scheme_ids: List[str],
        user_profile: Dict[str, Any],
        document_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create multiple applications at once for eligible schemes
        
        Args:
            user_id: User identifier
            scheme_ids: List of scheme identifiers
            user_profile: User profile data
            document_data: Document data
            
        Returns:
            List of created applications
        """
        created_apps = []
        
        for scheme_id in scheme_ids:
            try:
                app = self.create_application(
                    user_id=user_id,
                    scheme_id=scheme_id,
                    user_profile=user_profile,
                    document_data=document_data
                )
                created_apps.append(app)
            except Exception as e:
                created_apps.append({
                    "schemeId": scheme_id,
                    "error": str(e),
                    "status": "failed"
                })
        
        return created_apps
    
    def check_application_status(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Check application status from government system
        
        Args:
            application_id: Application identifier
            
        Returns:
            Current application status
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        if not application.government_ref_number:
            return {
                "applicationId": application_id,
                "status": application.status,
                "message": "Application not yet submitted to government system"
            }
        
        try:
            status_result = self.gov_api.check_application_status(
                scheme_id=application.scheme_id,
                reference_number=application.government_ref_number
            )
            
            # Update application status if changed
            gov_status = status_result.get("status")
            if gov_status and gov_status != application.status:
                status_map = {
                    "under_review": ApplicationStatus.UNDER_REVIEW,
                    "approved": ApplicationStatus.APPROVED,
                    "rejected": ApplicationStatus.REJECTED
                }
                
                if gov_status in status_map:
                    application.add_status_change(
                        new_status=status_map[gov_status],
                        reason=f"Status updated from government system",
                        updated_by="system"
                    )
            
            return {
                "applicationId": application_id,
                "governmentRefNumber": application.government_ref_number,
                "status": application.status,
                "governmentStatus": status_result,
                "lastChecked": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "applicationId": application_id,
                "status": application.status,
                "error": str(e),
                "message": "Unable to fetch status from government system"
            }
    
    def track_payment(
        self,
        application_id: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Track payment for approved application
        
        Args:
            application_id: Application identifier
            transaction_id: PFMS transaction ID
            
        Returns:
            Payment tracking information
        """
        application = self.applications.get(application_id)
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        try:
            payment_info = self.gov_api.track_payment(transaction_id)
            
            return {
                "applicationId": application_id,
                "paymentInfo": payment_info,
                "trackedAt": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "applicationId": application_id,
                "error": str(e),
                "message": "Unable to track payment"
            }
    
    def get_api_health(self) -> Dict[str, Any]:
        """
        Get health status of government API integrations
        
        Returns:
            Health status of all APIs
        """
        return self.gov_api.health_check()
