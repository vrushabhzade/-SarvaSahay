"""
Unit Tests for Application Tracking Service
Tests tracking functionality, status detection, and predictive analytics
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.tracking_service import (
    TrackingService,
    ApplicationTracker,
    TrackingConfig,
    TrackingEvent
)
from services.government_api_client import GovernmentAPIIntegration
from shared.models.application import (
    Application,
    ApplicationStatus,
    ApplicationPredictions,
    PaymentDetails,
    PaymentStatus
)


@pytest.fixture
def mock_gov_api():
    """Create mock government API client"""
    api = Mock(spec=GovernmentAPIIntegration)
    api.check_application_status.return_value = {
        "status": "under_review",
        "lastUpdated": datetime.utcnow().isoformat()
    }
    api.track_payment.return_value = {
        "status": "pending",
        "amount": 6000
    }
    return api


@pytest.fixture
def sample_application():
    """Create sample application for testing"""
    return Application(
        application_id="app-001",
        user_id="user-123",
        scheme_id="PM-KISAN",
        form_data={"farmer_name": "Test Farmer"},
        government_ref_number="PMKISAN2024001234",
        status=ApplicationStatus.SUBMITTED,
        submitted_at=datetime.utcnow() - timedelta(days=10),
        predictions=ApplicationPredictions(
            approval_probability=0.85,
            expected_processing_days=30,
            confidence_score=0.9,
            suggested_improvements=[],
            risk_factors=[]
        )
    )


@pytest.fixture
def tracking_service(mock_gov_api):
    """Create tracking service instance"""
    config = TrackingConfig(
        polling_interval_seconds=60,
        delay_threshold_days=45,
        enable_predictive_analytics=True
    )
    return TrackingService(mock_gov_api, config)


class TestApplicationTracker:
    """Test ApplicationTracker class"""
    
    def test_check_status_success(self, sample_application, mock_gov_api):
        """Test successful status check"""
        tracker = ApplicationTracker(sample_application, mock_gov_api)
        
        result = tracker.check_status()
        
        assert result["success"] is True
        assert result["applicationId"] == "app-001"
        assert result["currentStatus"] == "under_review"
        assert tracker.check_count == 1
        assert tracker.consecutive_failures == 0
    
    def test_check_status_failure(self, sample_application, mock_gov_api):
        """Test status check failure handling"""
        mock_gov_api.check_application_status.side_effect = Exception("API Error")
        
        tracker = ApplicationTracker(sample_application, mock_gov_api)
        result = tracker.check_status()
        
        assert result["success"] is False
        assert "error" in result
        assert tracker.consecutive_failures == 1
    
    def test_detect_status_change(self, sample_application, mock_gov_api):
        """Test status change detection"""
        tracker = ApplicationTracker(sample_application, mock_gov_api)
        
        # No change
        event = tracker.detect_status_change("submitted")
        assert event is None
        
        # Status changed
        event = tracker.detect_status_change("approved")
        assert event is not None
        assert event["eventType"] == TrackingEvent.STATUS_CHANGED
        assert event["oldStatus"] == ApplicationStatus.SUBMITTED
        assert event["newStatus"] == ApplicationStatus.APPROVED
    
    def test_check_for_delays_no_delay(self, sample_application, mock_gov_api):
        """Test delay detection when no delay"""
        tracker = ApplicationTracker(sample_application, mock_gov_api)
        
        delay_event = tracker.check_for_delays()
        assert delay_event is None
    
    def test_check_for_delays_with_delay(self, sample_application, mock_gov_api):
        """Test delay detection when delayed"""
        # Set submission date to 50 days ago
        sample_application.submitted_at = datetime.utcnow() - timedelta(days=50)
        
        tracker = ApplicationTracker(sample_application, mock_gov_api)
        delay_event = tracker.check_for_delays()
        
        assert delay_event is not None
        assert delay_event["eventType"] == TrackingEvent.DELAY_DETECTED
        assert delay_event["daysSinceSubmission"] == 50
        assert "suggestedActions" in delay_event
    
    def test_predict_approval_timeline(self, sample_application, mock_gov_api):
        """Test approval timeline prediction"""
        tracker = ApplicationTracker(sample_application, mock_gov_api)
        
        predictions = tracker.predict_approval_timeline()
        
        assert "estimatedRemainingDays" in predictions
        assert "expectedCompletionDate" in predictions
        assert "confidence" in predictions
        assert predictions["currentStatus"] == ApplicationStatus.SUBMITTED


class TestTrackingService:
    """Test TrackingService class"""
    
    def test_register_application(self, tracking_service, sample_application):
        """Test application registration"""
        tracker_id = tracking_service.register_application(sample_application)
        
        assert tracker_id == "app-001"
        assert tracker_id in tracking_service.trackers
        assert tracking_service.metrics.total_applications_tracked == 1
    
    def test_register_application_without_ref_number(self, tracking_service):
        """Test registration fails without government reference number"""
        app = Application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            form_data={},
            government_ref_number=None
        )
        
        with pytest.raises(ValueError, match="government reference number"):
            tracking_service.register_application(app)
    
    def test_unregister_application(self, tracking_service, sample_application):
        """Test application unregistration"""
        tracking_service.register_application(sample_application)
        
        result = tracking_service.unregister_application("app-001")
        assert result is True
        assert "app-001" not in tracking_service.trackers
        
        # Try unregistering non-existent application
        result = tracking_service.unregister_application("app-999")
        assert result is False
    
    def test_poll_application_success(self, tracking_service, sample_application):
        """Test successful application polling"""
        tracking_service.register_application(sample_application)
        
        result = tracking_service.poll_application("app-001")
        
        assert result["success"] is True
        assert result["applicationId"] == "app-001"
        assert "statusResult" in result
        assert "events" in result
    
    def test_poll_application_not_registered(self, tracking_service):
        """Test polling unregistered application"""
        result = tracking_service.poll_application("app-999")
        
        assert result["success"] is False
        assert "not registered" in result["error"]
    
    def test_poll_application_detects_status_change(
        self, tracking_service, sample_application, mock_gov_api
    ):
        """Test polling detects status changes"""
        mock_gov_api.check_application_status.return_value = {
            "status": "approved",
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        tracking_service.register_application(sample_application)
        result = tracking_service.poll_application("app-001")
        
        assert result["success"] is True
        assert len(result["events"]) > 0
        
        # Check if status change event was detected
        status_events = [
            e for e in result["events"]
            if e.get("eventType") == TrackingEvent.STATUS_CHANGED
        ]
        assert len(status_events) > 0
        assert tracking_service.metrics.status_changes_detected > 0
    
    def test_add_event_handler(self, tracking_service):
        """Test adding event handler"""
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        tracking_service.add_event_handler(handler)
        
        # Trigger an event
        event = {"eventType": "test", "data": "test_data"}
        tracking_service._publish_event(event)
        
        assert len(events_received) == 1
        assert events_received[0] == event
    
    def test_get_application_status(self, tracking_service, sample_application):
        """Test getting application status"""
        tracking_service.register_application(sample_application)
        
        status = tracking_service.get_application_status("app-001")
        
        assert status["success"] is True
        assert status["applicationId"] == "app-001"
        assert status["currentStatus"] == ApplicationStatus.SUBMITTED
        assert "statusHistory" in status
    
    def test_get_predictions(self, tracking_service, sample_application):
        """Test getting predictions"""
        tracking_service.register_application(sample_application)
        
        predictions = tracking_service.get_predictions("app-001")
        
        assert predictions["success"] is True
        assert "estimatedRemainingDays" in predictions
        assert "expectedCompletionDate" in predictions
    
    def test_get_metrics(self, tracking_service, sample_application):
        """Test getting service metrics"""
        tracking_service.register_application(sample_application)
        
        metrics = tracking_service.get_metrics()
        
        assert metrics["totalApplicationsTracked"] == 1
        assert metrics["activeTrackers"] == 1
        assert "statusChangesDetected" in metrics
        assert "paymentsConfirmed" in metrics
    
    def test_bulk_register(self, tracking_service):
        """Test bulk registration of applications"""
        applications = [
            Application(
                application_id=f"app-{i}",
                user_id=f"user-{i}",
                scheme_id="PM-KISAN",
                form_data={},
                government_ref_number=f"REF-{i}"
            )
            for i in range(5)
        ]
        
        results = tracking_service.bulk_register(applications)
        
        assert len(results["success"]) == 5
        assert len(results["failed"]) == 0
        assert len(tracking_service.trackers) == 5
    
    def test_get_delayed_applications(self, tracking_service):
        """Test getting delayed applications"""
        # Create delayed application
        delayed_app = Application(
            application_id="app-delayed",
            user_id="user-123",
            scheme_id="PM-KISAN",
            form_data={},
            government_ref_number="REF-DELAYED",
            status=ApplicationStatus.SUBMITTED,
            submitted_at=datetime.utcnow() - timedelta(days=60),
            predictions=ApplicationPredictions(
                approval_probability=0.8,
                expected_processing_days=30,
                confidence_score=0.9,
                suggested_improvements=[],
                risk_factors=[]
            )
        )
        
        tracking_service.register_application(delayed_app)
        
        delayed = tracking_service.get_delayed_applications()
        
        assert len(delayed) == 1
        assert delayed[0]["applicationId"] == "app-delayed"
        assert "delayInfo" in delayed[0]
    
    def test_payment_status_check(self, tracking_service, mock_gov_api):
        """Test payment status checking for approved applications"""
        # Create approved application with payment details
        app = Application(
            application_id="app-payment",
            user_id="user-123",
            scheme_id="PM-KISAN",
            form_data={},
            government_ref_number="REF-PAYMENT",
            status=ApplicationStatus.APPROVED,
            payment=PaymentDetails(
                payment_status=PaymentStatus.PENDING,
                expected_amount=6000,
                payment_reference="PAY-123"
            )
        )
        
        # Mock status check to return approved
        mock_gov_api.check_application_status.return_value = {
            "status": "approved",
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        # Mock payment completion
        mock_gov_api.track_payment.return_value = {
            "status": "completed",
            "amount": 6000,
            "completedAt": datetime.utcnow().isoformat()
        }
        
        tracking_service.register_application(app)
        result = tracking_service.poll_application("app-payment")
        
        # Check if payment event was detected
        payment_events = [
            e for e in result["events"]
            if e.get("eventType") == TrackingEvent.PAYMENT_RECEIVED
        ]
        assert len(payment_events) > 0


class TestTrackingConfig:
    """Test TrackingConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = TrackingConfig()
        
        assert config.polling_interval_seconds == 3600
        assert config.delay_threshold_days == 45
        assert config.enable_predictive_analytics is True
        assert config.max_concurrent_polls == 10
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = TrackingConfig(
            polling_interval_seconds=1800,
            delay_threshold_days=30,
            enable_predictive_analytics=False
        )
        
        assert config.polling_interval_seconds == 1800
        assert config.delay_threshold_days == 30
        assert config.enable_predictive_analytics is False
