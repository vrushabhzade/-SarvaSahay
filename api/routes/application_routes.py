"""
Application Management Routes
Auto-application creation and submission endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
import logging

from services.auto_application_service import AutoApplicationService
from services.form_template_manager import FormTemplateManager
from services.profile_service import ProfileService
from shared.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


def get_auto_application_service() -> AutoApplicationService:
    """Get auto application service instance"""
    return AutoApplicationService()


def get_form_template_manager() -> FormTemplateManager:
    """Get form template manager instance"""
    return FormTemplateManager()


def get_profile_service() -> ProfileService:
    """Get profile service instance"""
    return ProfileService()


@router.post("/applications/create")
async def create_application(
    user_id: str,
    scheme_id: str,
    auto_application_service: AutoApplicationService = Depends(get_auto_application_service),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Create a new application for a government scheme
    
    - **user_id**: User profile identifier
    - **scheme_id**: Government scheme identifier
    - Returns: Created application with pre-filled form data
    """
    try:
        # Get user profile
        user_profile = profile_service.get_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found: {user_id}"
            )
        
        # Create application
        application_data = {
            "user_id": user_id,
            "scheme_id": scheme_id,
            "profile_data": user_profile
        }
        
        application_id = auto_application_service.create_application(application_data)
        
        # Get created application
        application = auto_application_service.get_application(application_id)
        
        logger.info(f"Application created: {application_id} for user {user_id}, scheme {scheme_id}")
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )


@router.post("/applications/submit/{application_id}")
async def submit_application(
    application_id: str,
    auto_application_service: AutoApplicationService = Depends(get_auto_application_service)
):
    """
    Submit an application to government portal
    
    - **application_id**: Application identifier
    - Returns: Submission confirmation with reference number
    """
    try:
        # Submit application
        submission_result = auto_application_service.submit_application(application_id)
        
        logger.info(f"Application submitted: {application_id}")
        
        return submission_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application"
        )


@router.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    auto_application_service: AutoApplicationService = Depends(get_auto_application_service)
):
    """
    Get application details
    
    - **application_id**: Application identifier
    - Returns: Complete application information
    """
    try:
        application = auto_application_service.get_application(application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {application_id}"
            )
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application"
        )


@router.get("/applications/user/{user_id}")
async def get_user_applications(
    user_id: str,
    status_filter: Optional[str] = None,
    auto_application_service: AutoApplicationService = Depends(get_auto_application_service),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get all applications for a user
    
    - **user_id**: User profile identifier
    - **status_filter**: Optional status filter (draft, submitted, approved, etc.)
    - Returns: List of user applications
    """
    try:
        # Verify user exists
        user_profile = profile_service.get_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found: {user_id}"
            )
        
        # Get user applications
        applications = auto_application_service.get_user_applications(user_id)
        
        # Apply status filter if provided
        if status_filter:
            applications = [
                app for app in applications 
                if app.get("status", {}).get("current") == status_filter
            ]
        
        return {
            "user_id": user_id,
            "total_applications": len(applications),
            "applications": applications
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User applications retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user applications"
        )


@router.get("/applications/forms/{scheme_id}")
async def get_form_template(
    scheme_id: str,
    form_template_manager: FormTemplateManager = Depends(get_form_template_manager)
):
    """
    Get form template for a government scheme
    
    - **scheme_id**: Government scheme identifier
    - Returns: Form template structure
    """
    try:
        template = form_template_manager.get_template(scheme_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Form template not found for scheme: {scheme_id}"
            )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form template retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve form template"
        )
