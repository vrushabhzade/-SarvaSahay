"""
Application Tracking Routes
Real-time application status monitoring endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
import logging

from services.tracking_service import TrackingService
from services.notification_service import NotificationService
from shared.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


def get_tracking_service() -> TrackingService:
    """Get tracking service instance"""
    return TrackingService()


def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    return NotificationService()


@router.get("/tracking/status/{application_id}")
async def get_application_status(
    application_id: str,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """
    Get current status of an application
    
    - **application_id**: Application identifier
    - Returns: Current application status and history
    """
    try:
        status_info = tracking_service.get_application_status(application_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {application_id}"
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application status"
        )


@router.post("/tracking/update/{application_id}")
async def update_application_status(
    application_id: str,
    new_status: str,
    tracking_service: TrackingService = Depends(get_tracking_service),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Update application status (admin/system endpoint)
    
    - **application_id**: Application identifier
    - **new_status**: New status value
    - Returns: Updated status information
    """
    try:
        # Update status
        success = tracking_service.update_application_status(application_id, new_status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {application_id}"
            )
        
        # Get updated status
        status_info = tracking_service.get_application_status(application_id)
        
        # Send notification about status change
        # (In real implementation, get user_id from application)
        # notification_service.send_notification(user_id, f"Status updated to {new_status}", "sms")
        
        logger.info(f"Application status updated: {application_id} -> {new_status}")
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application status"
        )


@router.get("/tracking/predictions/{application_id}")
async def get_approval_predictions(
    application_id: str,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """
    Get approval predictions and timeline estimates
    
    - **application_id**: Application identifier
    - Returns: Predicted approval probability and processing time
    """
    try:
        predictions = tracking_service.get_approval_predictions(application_id)
        
        if not predictions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application not found: {application_id}"
            )
        
        return predictions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predictions retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve predictions"
        )


@router.post("/tracking/webhook")
async def receive_government_webhook(
    webhook_data: dict,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """
    Receive webhook notifications from government systems
    
    - **webhook_data**: Webhook payload from government API
    - Returns: Acknowledgment of webhook receipt
    """
    try:
        # Process webhook
        processed = tracking_service.process_government_webhook(webhook_data)
        
        logger.info(f"Government webhook processed: {webhook_data.get('application_id')}")
        
        return {
            "status": "received",
            "processed": processed,
            "timestamp": "2026-03-02T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.get("/tracking/user/{user_id}")
async def get_user_tracking_info(
    user_id: str,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """
    Get tracking information for all user applications
    
    - **user_id**: User profile identifier
    - Returns: Tracking information for all user applications
    """
    try:
        tracking_info = tracking_service.get_user_tracking_info(user_id)
        
        return {
            "user_id": user_id,
            "total_applications": len(tracking_info),
            "applications": tracking_info
        }
        
    except Exception as e:
        logger.error(f"User tracking info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tracking information"
        )
