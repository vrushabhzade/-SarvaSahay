"""
Application Tracking Service
Monitors application status across government systems with periodic polling,
status change detection, event publishing, and predictive analytics
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from dataclasses import dataclass, field

from shared.models.application import Application, ApplicationStatus, PaymentStatus, StatusHistory
from services.government_api_client import GovernmentAPIIntegration


class TrackingEvent(str, Enum):
    """Tracking event types"""
    STATUS_CHANGED = "status_changed"
    PAYMENT_RECEIVED = "payment_received"
    DELAY_DETECTED = "delay_detected"
    APPROVAL_RECEIVED = "approval_received"
    REJECTION_RECEIVED = "rejection_received"


@dataclass
class TrackingConfig:
    """Configuration for tracking service"""
    polling_interval_seconds: int = 3600  # Poll every hour
    delay_threshold_days: int = 45  # Alert if processing exceeds 45 days
    enable_predictive_analytics: bool = True
    max_concurrent_polls: int = 10
    retry_failed_polls: bool = True
    event_handlers: List[Callable] = field(default_factory=list)


@dataclass
class TrackingMetrics:
    """Tracking service metrics"""
    total_applications_tracked: int = 0
    status_changes_detected: int = 0
    payments_confirmed: int = 0
    delays_detected: int = 0
    last_poll_time: Optional[datetime] = None
    failed_polls: int = 0
    average_processing_days: float = 0.0


class ApplicationTracker:
    """
    Tracks individual application status and history
    """
    
    def __init__(
        self,
        application: Application,
        gov_api: GovernmentAPIIntegration
    ):
        self.application = application
        self.gov_api = gov_api
        self.last_checked: Optional[datetime] = None
        self.check_count: int = 0
        self.consecutive_failures: int = 0
    
    def check_status(self) -> Dict[str, Any]:
        """
        Check current application status from government system
        
        Returns:
            Status update information
        """
        try:
            # Query government API for status
            status_response = self.gov_api.check_application_status(
                scheme_id=self.application.scheme_id,
                reference_number=self.application.government_ref_number
            )
            
            self.last_checked = datetime.utcnow()
            self.check_count += 1
            self.consecutive_failures = 0
            
            return {
                "success": True,
                "applicationId": self.application.application_id,
                "currentStatus": status_response.get("status"),
                "lastUpdated": status_response.get("lastUpdated"),
                "checkedAt": self.last_checked.isoformat(),
                "governmentData": status_response
            }
            
        except Exception as e:
            self.consecutive_failures += 1
            return {
                "success": False,
                "applicationId": self.application.application_id,
                "error": str(e),
                "consecutiveFailures": self.consecutive_failures,
                "checkedAt": datetime.utcnow().isoformat()
            }
    
    def detect_status_change(self, new_status: str) -> Optional[Dict[str, Any]]:
        """
        Detect if application status has changed
        
        Args:
            new_status: New status from government system
            
        Returns:
            Status change event if detected, None otherwise
        """
        # Map government status to internal status
        status_mapping = {
            "submitted": ApplicationStatus.SUBMITTED,
            "under_review": ApplicationStatus.UNDER_REVIEW,
            "approved": ApplicationStatus.APPROVED,
            "rejected": ApplicationStatus.REJECTED,
            "paid": ApplicationStatus.PAID
        }
        
        mapped_status = status_mapping.get(new_status.lower())
        
        if mapped_status and mapped_status != self.application.status:
            return {
                "eventType": TrackingEvent.STATUS_CHANGED,
                "applicationId": self.application.application_id,
                "oldStatus": self.application.status,
                "newStatus": mapped_status,
                "detectedAt": datetime.utcnow().isoformat()
            }
        
        return None
    
    def check_for_delays(self) -> Optional[Dict[str, Any]]:
        """
        Check if application processing is delayed
        
        Returns:
            Delay event if detected, None otherwise
        """
        if not self.application.submitted_at:
            return None
        
        days_since_submission = (datetime.utcnow() - self.application.submitted_at).days
        
        # Get expected processing time from predictions
        expected_days = 30  # Default
        if self.application.predictions:
            expected_days = self.application.predictions.expected_processing_days
        
        # Check if delayed beyond threshold
        if days_since_submission > expected_days + 15:  # 15 day grace period
            return {
                "eventType": TrackingEvent.DELAY_DETECTED,
                "applicationId": self.application.application_id,
                "daysSinceSubmission": days_since_submission,
                "expectedDays": expected_days,
                "delayDays": days_since_submission - expected_days,
                "detectedAt": datetime.utcnow().isoformat(),
                "suggestedActions": [
                    "Contact government office for status update",
                    "Verify all submitted documents are complete",
                    "Check for any pending clarifications"
                ]
            }
        
        return None
    
    def predict_approval_timeline(self) -> Dict[str, Any]:
        """
        Predict approval timeline based on current status and historical data
        
        Returns:
            Timeline predictions
        """
        # Calculate days since submission
        days_elapsed = 0
        if self.application.submitted_at:
            days_elapsed = (datetime.utcnow() - self.application.submitted_at).days
        
        # Base predictions on status
        status_timelines = {
            ApplicationStatus.SUBMITTED: {"remaining": 30, "confidence": 0.7},
            ApplicationStatus.UNDER_REVIEW: {"remaining": 20, "confidence": 0.8},
            ApplicationStatus.APPROVED: {"remaining": 7, "confidence": 0.9},
            ApplicationStatus.REJECTED: {"remaining": 0, "confidence": 1.0},
            ApplicationStatus.PAID: {"remaining": 0, "confidence": 1.0}
        }
        
        timeline = status_timelines.get(
            self.application.status,
            {"remaining": 30, "confidence": 0.5}
        )
        
        expected_completion = datetime.utcnow() + timedelta(days=timeline["remaining"])
        
        return {
            "applicationId": self.application.application_id,
            "currentStatus": self.application.status,
            "daysElapsed": days_elapsed,
            "estimatedRemainingDays": timeline["remaining"],
            "expectedCompletionDate": expected_completion.isoformat(),
            "confidence": timeline["confidence"],
            "predictedAt": datetime.utcnow().isoformat()
        }


class TrackingService:
    """
    Application Tracking Service
    Manages periodic polling, status detection, and event publishing
    """
    
    def __init__(
        self,
        gov_api: GovernmentAPIIntegration,
        config: Optional[TrackingConfig] = None
    ):
        self.gov_api = gov_api
        self.config = config or TrackingConfig()
        self.metrics = TrackingMetrics()
        
        # Active trackers
        self.trackers: Dict[str, ApplicationTracker] = {}
        
        # Event handlers
        self.event_handlers: List[Callable] = self.config.event_handlers.copy()
        
        # Polling state
        self.is_polling = False
        self.polling_task: Optional[asyncio.Task] = None
    
    def register_application(self, application: Application) -> str:
        """
        Register application for tracking
        
        Args:
            application: Application to track
            
        Returns:
            Tracker ID
        """
        if not application.government_ref_number:
            raise ValueError("Application must have government reference number to track")
        
        tracker_id = application.application_id
        self.trackers[tracker_id] = ApplicationTracker(application, self.gov_api)
        self.metrics.total_applications_tracked += 1
        
        return tracker_id
    
    def unregister_application(self, application_id: str) -> bool:
        """
        Stop tracking an application
        
        Args:
            application_id: Application ID to stop tracking
            
        Returns:
            True if unregistered, False if not found
        """
        if application_id in self.trackers:
            del self.trackers[application_id]
            return True
        return False
    
    def add_event_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """
        Add event handler for tracking events
        
        Args:
            handler: Callback function for events
        """
        self.event_handlers.append(handler)
    
    def _publish_event(self, event: Dict[str, Any]):
        """
        Publish tracking event to all handlers
        
        Args:
            event: Event data
        """
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
    
    def poll_application(self, application_id: str) -> Dict[str, Any]:
        """
        Poll single application for status updates
        
        Args:
            application_id: Application ID to poll
            
        Returns:
            Poll result with any detected events
        """
        if application_id not in self.trackers:
            return {
                "success": False,
                "error": "Application not registered for tracking"
            }
        
        tracker = self.trackers[application_id]
        
        # Check status
        status_result = tracker.check_status()
        
        if not status_result["success"]:
            self.metrics.failed_polls += 1
            return status_result
        
        events = []
        
        # Detect status changes
        new_status = status_result.get("currentStatus")
        if new_status:
            status_change = tracker.detect_status_change(new_status)
            if status_change:
                events.append(status_change)
                self.metrics.status_changes_detected += 1
                self._publish_event(status_change)
                
                # Update application status
                tracker.application.add_status_change(
                    new_status=status_change["newStatus"],
                    reason="Status updated from government system"
                )
        
        # Check for delays
        delay_event = tracker.check_for_delays()
        if delay_event:
            events.append(delay_event)
            self.metrics.delays_detected += 1
            self._publish_event(delay_event)
        
        # Check payment status if approved and has payment details
        if tracker.application.status == ApplicationStatus.APPROVED and tracker.application.payment:
            payment_event = self._check_payment_status(tracker)
            if payment_event:
                events.append(payment_event)
                self.metrics.payments_confirmed += 1
                self._publish_event(payment_event)
        
        self.metrics.last_poll_time = datetime.utcnow()
        
        return {
            "success": True,
            "applicationId": application_id,
            "statusResult": status_result,
            "events": events,
            "polledAt": datetime.utcnow().isoformat()
        }
    
    def _check_payment_status(self, tracker: ApplicationTracker) -> Optional[Dict[str, Any]]:
        """
        Check payment status for approved application
        
        Args:
            tracker: Application tracker
            
        Returns:
            Payment event if detected
        """
        try:
            # Check if payment details exist
            if not tracker.application.payment:
                return None
            
            payment_ref = tracker.application.payment.payment_reference
            if not payment_ref:
                return None
            
            # Query PFMS for payment status
            payment_status = self.gov_api.track_payment(payment_ref)
            
            # Check if payment completed
            if payment_status.get("status") == "completed":
                return {
                    "eventType": TrackingEvent.PAYMENT_RECEIVED,
                    "applicationId": tracker.application.application_id,
                    "paymentReference": payment_ref,
                    "amount": payment_status.get("amount", 0),
                    "paymentDate": payment_status.get("completedAt"),
                    "detectedAt": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            print(f"Error checking payment status: {e}")
        
        return None
    
    async def start_polling(self):
        """
        Start periodic polling of all registered applications
        """
        if self.is_polling:
            return
        
        self.is_polling = True
        
        while self.is_polling:
            try:
                # Poll all registered applications
                application_ids = list(self.trackers.keys())
                
                # Process in batches to avoid overwhelming APIs
                batch_size = self.config.max_concurrent_polls
                for i in range(0, len(application_ids), batch_size):
                    batch = application_ids[i:i + batch_size]
                    
                    # Poll batch concurrently
                    tasks = [
                        asyncio.to_thread(self.poll_application, app_id)
                        for app_id in batch
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait for next polling interval
                await asyncio.sleep(self.config.polling_interval_seconds)
                
            except Exception as e:
                print(f"Error in polling loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def stop_polling(self):
        """
        Stop periodic polling
        """
        self.is_polling = False
        if self.polling_task:
            self.polling_task.cancel()
    
    def get_application_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get current tracked status for application
        
        Args:
            application_id: Application ID
            
        Returns:
            Current status and tracking information
        """
        if application_id not in self.trackers:
            return {
                "success": False,
                "error": "Application not registered for tracking"
            }
        
        tracker = self.trackers[application_id]
        
        return {
            "success": True,
            "applicationId": application_id,
            "currentStatus": tracker.application.status,
            "lastChecked": tracker.last_checked.isoformat() if tracker.last_checked else None,
            "checkCount": tracker.check_count,
            "consecutiveFailures": tracker.consecutive_failures,
            "statusHistory": [
                {
                    "status": h.status,
                    "timestamp": h.timestamp.isoformat(),
                    "reason": h.reason
                }
                for h in tracker.application.status_history
            ]
        }
    
    def get_predictions(self, application_id: str) -> Dict[str, Any]:
        """
        Get predictive analytics for application
        
        Args:
            application_id: Application ID
            
        Returns:
            Predictions and timeline estimates
        """
        if application_id not in self.trackers:
            return {
                "success": False,
                "error": "Application not registered for tracking"
            }
        
        tracker = self.trackers[application_id]
        predictions = tracker.predict_approval_timeline()
        
        return {
            "success": True,
            **predictions
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get tracking service metrics
        
        Returns:
            Service metrics
        """
        return {
            "totalApplicationsTracked": self.metrics.total_applications_tracked,
            "activeTrackers": len(self.trackers),
            "statusChangesDetected": self.metrics.status_changes_detected,
            "paymentsConfirmed": self.metrics.payments_confirmed,
            "delaysDetected": self.metrics.delays_detected,
            "lastPollTime": self.metrics.last_poll_time.isoformat() if self.metrics.last_poll_time else None,
            "failedPolls": self.metrics.failed_polls,
            "averageProcessingDays": self.metrics.average_processing_days,
            "isPolling": self.is_polling
        }
    
    def bulk_register(self, applications: List[Application]) -> Dict[str, Any]:
        """
        Register multiple applications for tracking
        
        Args:
            applications: List of applications to track
            
        Returns:
            Registration results
        """
        results = {
            "success": [],
            "failed": []
        }
        
        for app in applications:
            try:
                tracker_id = self.register_application(app)
                results["success"].append({
                    "applicationId": app.application_id,
                    "trackerId": tracker_id
                })
            except Exception as e:
                results["failed"].append({
                    "applicationId": app.application_id,
                    "error": str(e)
                })
        
        return results
    
    def get_delayed_applications(self) -> List[Dict[str, Any]]:
        """
        Get list of applications with detected delays
        
        Returns:
            List of delayed applications with details
        """
        delayed = []
        
        for app_id, tracker in self.trackers.items():
            delay_event = tracker.check_for_delays()
            if delay_event:
                delayed.append({
                    "applicationId": app_id,
                    "schemeId": tracker.application.scheme_id,
                    "status": tracker.application.status,
                    "delayInfo": delay_event
                })
        
        return delayed
