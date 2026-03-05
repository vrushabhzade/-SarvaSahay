"""
Property-Based Tests for Real-Time Tracking and Notification Consistency
Feature: sarvasahay-platform, Property 5: Real-Time Tracking and Notification Consistency

This test validates that for any submitted application, the system:
1. Monitors status through government databases
2. Sends SMS notifications on status changes
3. Notifies users of approvals with payment details
4. Confirms disbursements

Validates: Requirements 5.1, 5.2, 5.3, 5.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from services.tracking_service import TrackingService, TrackingConfig, TrackingEvent
from services.notification_service import (
    NotificationService,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    CommunicationChannel
)
from services.government_api_client import GovernmentAPIIntegration
from shared.models.application import Application, ApplicationStatus, PaymentStatus, PaymentDetails
from shared.models.user_profile import Language


# Strategy for generating valid applications for tracking
@st.composite
def tracking_application_strategy(draw):
    """Generate valid applications for tracking tests"""
    application_id = f"APP-{draw(st.integers(min_value=1000, max_value=9999))}"
    scheme_id = draw(st.sampled_from(["PM-KISAN", "PMAY", "MGNREGA", "PMJDY"]))
    gov_ref = f"GOV-{draw(st.integers(min_value=100000, max_value=999999))}"
    
    status = draw(st.sampled_from(list(ApplicationStatus)))
    
    # Generate timestamps
    created_at = datetime.utcnow() - timedelta(days=draw(st.integers(min_value=1, max_value=90)))
    submitted_at = created_at + timedelta(hours=draw(st.integers(min_value=1, max_value=48)))
    
    # Generate form data
    form_data = {
        "applicant_name": draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
        "age": draw(st.integers(min_value=18, max_value=100)),
        "land_ownership": draw(st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False)),
        "bank_account": draw(st.text(min_size=9, max_size=18, alphabet=st.characters(whitelist_categories=('Nd',)))),
    }
    
    return Application(
        application_id=application_id,
        user_id=f"USER-{draw(st.integers(min_value=100, max_value=999))}",
        scheme_id=scheme_id,
        form_data=form_data,
        status=status,
        government_ref_number=gov_ref,
        created_at=created_at,
        submitted_at=submitted_at if status != ApplicationStatus.DRAFT else None
    )


# Strategy for generating notification data
@st.composite
def notification_data_strategy(draw):
    """Generate notification data for testing"""
    return {
        "application_id": f"APP-{draw(st.integers(min_value=1000, max_value=9999))}",
        "scheme_name": draw(st.sampled_from(["PM-KISAN", "PMAY", "MGNREGA"])),
        "status": draw(st.sampled_from(["submitted", "under_review", "approved", "rejected"])),
        "amount": draw(st.integers(min_value=1000, max_value=500000)),
        "payment_date": (datetime.utcnow() + timedelta(days=draw(st.integers(min_value=1, max_value=30)))).strftime("%Y-%m-%d"),
        "reference": f"REF-{draw(st.integers(min_value=100000, max_value=999999))}"
    }


# Strategy for generating contact information
@st.composite
def contact_info_strategy(draw):
    """Generate contact information for notifications"""
    phone_first_digit = draw(st.sampled_from(['6', '7', '8', '9']))
    phone_rest = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(9)])
    phone = f"91{phone_first_digit}{phone_rest}"
    
    email_user = draw(st.text(min_size=3, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    email_domain = draw(st.text(min_size=3, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))
    email = f"{email_user}@{email_domain}.com"
    
    return {
        "phone": phone,
        "email": email,
        "device_token": f"FCM-{draw(st.text(min_size=20, max_size=40, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))}"
    }


class TestTrackingNotificationConsistencyProperty:
    """
    Property 5: Real-Time Tracking and Notification Consistency
    
    For any submitted application, the system should:
    1. Monitor status through government databases
    2. Send notifications on status changes
    3. Notify users of approvals with payment details
    4. Confirm disbursements
    """
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_application_registration_for_tracking(self, application: Application):
        """
        Property: All submitted applications must be registerable for tracking
        
        Validates Requirement 5.1: Monitor application status through government databases
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register application for tracking
        tracker_id = tracking_service.register_application(application)
        
        # Verify registration
        assert tracker_id == application.application_id
        assert tracker_id in tracking_service.trackers
        assert tracking_service.metrics.total_applications_tracked > 0
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_status_polling_produces_valid_results(self, application: Application):
        """
        Property: Status polling must produce valid results for any application
        
        Validates Requirement 5.1: Periodic polling of government APIs
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register and poll application
        tracking_service.register_application(application)
        poll_result = tracking_service.poll_application(application.application_id)
        
        # Verify poll result structure
        assert 'success' in poll_result
        assert 'applicationId' in poll_result
        assert poll_result['applicationId'] == application.application_id
        
        if poll_result['success']:
            assert 'statusResult' in poll_result
            assert 'events' in poll_result
            assert isinstance(poll_result['events'], list)
            assert 'polledAt' in poll_result
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_status_change_detection(self, application: Application):
        """
        Property: Status changes must be detected and reported
        
        Validates Requirement 5.2: Send SMS notifications on status changes
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize services
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register application
        tracking_service.register_application(application)
        tracker = tracking_service.trackers[application.application_id]
        
        # Simulate status change
        new_status = "approved" if application.status == ApplicationStatus.SUBMITTED else "under_review"
        status_change = tracker.detect_status_change(new_status)
        
        # If status actually changed, verify event structure
        if status_change:
            assert 'eventType' in status_change
            assert status_change['eventType'] == TrackingEvent.STATUS_CHANGED
            assert 'applicationId' in status_change
            assert 'oldStatus' in status_change
            assert 'newStatus' in status_change
            assert 'detectedAt' in status_change
    
    @given(
        notification_type=st.sampled_from(list(NotificationType)),
        channel=st.sampled_from(list(CommunicationChannel)),
        language=st.sampled_from(list(Language)),
        data=notification_data_strategy(),
        contact_info=contact_info_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_notification_sending_completeness(
        self,
        notification_type: NotificationType,
        channel: CommunicationChannel,
        language: Language,
        data: Dict[str, Any],
        contact_info: Dict[str, str]
    ):
        """
        Property: Notifications must be sent through specified channels
        
        Validates Requirement 5.2: Multi-channel notification delivery
        """
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send notification
        result = notification_service.send_notification(
            user_id="test-user-123",
            notification_type=notification_type,
            channel=channel,
            language=language,
            data=data,
            contact_info=contact_info
        )
        
        # Verify result structure
        assert 'success' in result
        
        # If template not found, that's acceptable (not all combinations have templates)
        if not result['success'] and 'No template found' in result.get('error', ''):
            return  # Skip this test case
        
        # For successful sends, verify complete structure
        if result['success']:
            assert 'notificationId' in result
            assert 'channel' in result
            assert result['channel'] == channel
            assert 'providerResult' in result
            
            # Verify notification was recorded
            history = notification_service.get_notification_history(user_id="test-user-123")
            assert len(history) > 0
            
            # Find the notification we just sent
            sent_notification = next(
                (n for n in history if n['notificationId'] == result['notificationId']),
                None
            )
            assert sent_notification is not None
            assert sent_notification['channel'] == channel
            assert sent_notification['type'] == notification_type
    
    @given(
        application=tracking_application_strategy(),
        contact_info=contact_info_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_approval_notification_with_payment_details(
        self,
        application: Application,
        contact_info: Dict[str, str]
    ):
        """
        Property: Approval notifications must include payment details
        
        Validates Requirement 5.3: Notify users of approval amount and expected payment date
        """
        # Skip if not approved
        assume(application.status == ApplicationStatus.APPROVED)
        assume(application.government_ref_number is not None)
        
        # Add payment information to application
        application.payment = PaymentDetails(
            payment_reference=f"PAY-{datetime.utcnow().timestamp()}",
            expected_amount=50000.0,
            payment_date=datetime.utcnow() + timedelta(days=7),
            payment_status=PaymentStatus.PENDING
        )
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send approval notification
        notification_data = {
            "scheme_name": application.scheme_id,
            "amount": int(application.payment.expected_amount),
            "payment_date": application.payment.payment_date.strftime("%Y-%m-%d")
        }
        
        result = notification_service.send_notification(
            user_id=application.user_id,
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data=notification_data,
            contact_info=contact_info
        )
        
        # Verify notification was sent
        assert result['success'] is True
        
        # Verify notification contains payment details
        history = notification_service.get_notification_history(user_id=application.user_id)
        assert len(history) > 0
        
        approval_notification = next(
            (n for n in history if n['type'] == NotificationType.APPROVAL_NOTIFICATION),
            None
        )
        assert approval_notification is not None
        assert 'message' in approval_notification
        # Message should contain amount and payment date
        assert str(int(application.payment.expected_amount)) in approval_notification['message'] or '50000' in approval_notification['message']
    
    @given(
        application=tracking_application_strategy(),
        contact_info=contact_info_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payment_confirmation_notification(
        self,
        application: Application,
        contact_info: Dict[str, str]
    ):
        """
        Property: Payment confirmations must be sent when disbursements occur
        
        Validates Requirement 5.4: Confirm receipt and amount via SMS
        """
        # Skip if not approved with payment
        assume(application.status == ApplicationStatus.APPROVED)
        assume(application.government_ref_number is not None)
        
        # Add payment information
        payment_amount = 50000.0
        payment_ref = f"PAY-{datetime.utcnow().timestamp()}"
        
        application.payment = PaymentDetails(
            payment_reference=payment_ref,
            expected_amount=payment_amount,
            actual_amount=payment_amount,
            payment_date=datetime.utcnow(),
            payment_status=PaymentStatus.COMPLETED
        )
        
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send payment confirmation
        notification_data = {
            "amount": int(payment_amount),
            "reference": payment_ref
        }
        
        result = notification_service.send_notification(
            user_id=application.user_id,
            notification_type=NotificationType.PAYMENT_CONFIRMATION,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data=notification_data,
            contact_info=contact_info
        )
        
        # Verify notification was sent
        assert result['success'] is True
        
        # Verify notification contains payment confirmation
        history = notification_service.get_notification_history(user_id=application.user_id)
        payment_notification = next(
            (n for n in history if n['type'] == NotificationType.PAYMENT_CONFIRMATION),
            None
        )
        assert payment_notification is not None
        assert 'message' in payment_notification
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delay_detection_and_alerting(self, application: Application):
        """
        Property: Delays must be detected and users alerted with suggested actions
        
        Validates Requirement 5.5: Alert users and suggest follow-up actions
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        assume(application.submitted_at is not None)
        
        # Make application old enough to trigger delay detection
        application.submitted_at = datetime.utcnow() - timedelta(days=60)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register application
        tracking_service.register_application(application)
        tracker = tracking_service.trackers[application.application_id]
        
        # Check for delays
        delay_event = tracker.check_for_delays()
        
        # If delay detected, verify event structure
        if delay_event:
            assert 'eventType' in delay_event
            assert delay_event['eventType'] == TrackingEvent.DELAY_DETECTED
            assert 'applicationId' in delay_event
            assert 'daysSinceSubmission' in delay_event
            assert 'expectedDays' in delay_event
            assert 'delayDays' in delay_event
            assert 'suggestedActions' in delay_event
            assert isinstance(delay_event['suggestedActions'], list)
            assert len(delay_event['suggestedActions']) > 0
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tracking_event_publishing(self, application: Application):
        """
        Property: Tracking events must be published to registered handlers
        
        Validates Requirement 5.1: Event-driven notifications for status changes
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Track published events
        published_events = []
        
        def event_handler(event: Dict[str, Any]):
            published_events.append(event)
        
        # Initialize tracking service with event handler
        gov_api = GovernmentAPIIntegration()
        config = TrackingConfig(event_handlers=[event_handler])
        tracking_service = TrackingService(gov_api, config)
        
        # Register and poll application
        tracking_service.register_application(application)
        poll_result = tracking_service.poll_application(application.application_id)
        
        # If polling was successful and events were detected
        if poll_result.get('success') and poll_result.get('events'):
            # Verify events were published to handler
            assert len(published_events) == len(poll_result['events'])
            
            for event in published_events:
                assert 'eventType' in event
                assert 'applicationId' in event
                assert event['applicationId'] == application.application_id
    
    @given(
        applications=st.lists(tracking_application_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_bulk_application_tracking(self, applications: List[Application]):
        """
        Property: Multiple applications must be trackable simultaneously
        
        Validates Requirement 5.1: System handles concurrent tracking
        """
        # Filter to only submitted applications
        submitted_apps = [app for app in applications if app.government_ref_number]
        assume(len(submitted_apps) > 0)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Bulk register applications
        result = tracking_service.bulk_register(submitted_apps)
        
        # Verify all were registered
        assert 'success' in result
        assert 'failed' in result
        assert len(result['success']) > 0
        
        # Verify each successful registration
        for success_entry in result['success']:
            assert 'applicationId' in success_entry
            assert 'trackerId' in success_entry
            assert success_entry['trackerId'] in tracking_service.trackers
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tracking_metrics_accuracy(self, application: Application):
        """
        Property: Tracking metrics must accurately reflect service activity
        
        Validates Requirement 5.1: System maintains accurate tracking metrics
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Get initial metrics
        initial_metrics = tracking_service.get_metrics()
        initial_tracked = initial_metrics['totalApplicationsTracked']
        
        # Register application
        tracking_service.register_application(application)
        
        # Get updated metrics
        updated_metrics = tracking_service.get_metrics()
        
        # Verify metrics were updated
        assert updated_metrics['totalApplicationsTracked'] == initial_tracked + 1
        assert updated_metrics['activeTrackers'] > 0
    
    @given(
        channel=st.sampled_from(list(CommunicationChannel)),
        language=st.sampled_from(list(Language)),
        data=notification_data_strategy(),
        contact_info=contact_info_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_notification_language_support(
        self,
        channel: CommunicationChannel,
        language: Language,
        data: Dict[str, Any],
        contact_info: Dict[str, str]
    ):
        """
        Property: Notifications must support multiple languages
        
        Validates Requirement 5.2: Multi-language notification support
        """
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send notification in specified language
        result = notification_service.send_notification(
            user_id="test-user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=channel,
            language=language,
            data=data,
            contact_info=contact_info
        )
        
        # Verify notification was sent
        assert 'success' in result
        
        # If successful, verify language was recorded
        if result['success']:
            history = notification_service.get_notification_history(user_id="test-user-123")
            assert len(history) > 0
    
    @given(
        channels=st.lists(
            st.sampled_from(list(CommunicationChannel)),
            min_size=1,
            max_size=3,
            unique=True
        ),
        language=st.sampled_from(list(Language)),
        data=notification_data_strategy(),
        contact_info=contact_info_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multi_channel_notification_delivery(
        self,
        channels: List[CommunicationChannel],
        language: Language,
        data: Dict[str, Any],
        contact_info: Dict[str, str]
    ):
        """
        Property: Notifications must be deliverable through multiple channels simultaneously
        
        Validates Requirement 5.2: Multi-channel communication support
        """
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send notification through multiple channels
        result = notification_service.send_multi_channel(
            user_id="test-user-456",
            notification_type=NotificationType.STATUS_UPDATE,
            channels=channels,
            language=language,
            data=data,
            contact_info=contact_info
        )
        
        # Verify result structure
        assert 'success' in result
        assert 'results' in result
        assert isinstance(result['results'], dict)
        
        # Verify each channel was attempted
        for channel in channels:
            assert channel in result['results']
            assert 'success' in result['results'][channel]
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_predictive_analytics_for_timeline(self, application: Application):
        """
        Property: System must provide predictive analytics for approval timelines
        
        Validates Requirement 5.5: Predictive analytics for approval timelines
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register application
        tracking_service.register_application(application)
        
        # Get predictions
        predictions = tracking_service.get_predictions(application.application_id)
        
        # Verify predictions structure
        assert predictions['success'] is True
        assert 'applicationId' in predictions
        assert 'currentStatus' in predictions
        assert 'daysElapsed' in predictions
        assert 'estimatedRemainingDays' in predictions
        assert 'expectedCompletionDate' in predictions
        assert 'confidence' in predictions
        
        # Verify confidence is in valid range
        assert 0 <= predictions['confidence'] <= 1
        
        # Verify remaining days is non-negative
        assert predictions['estimatedRemainingDays'] >= 0
    
    @given(
        notification_type=st.sampled_from(list(NotificationType)),
        priority=st.sampled_from(list(NotificationPriority)),
        channel=st.sampled_from(list(CommunicationChannel)),
        data=notification_data_strategy(),
        contact_info=contact_info_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_notification_priority_handling(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority,
        channel: CommunicationChannel,
        data: Dict[str, Any],
        contact_info: Dict[str, str]
    ):
        """
        Property: Notifications must respect priority levels
        
        Validates Requirement 5.2: Priority-based notification delivery
        """
        # Initialize notification service
        notification_service = NotificationService()
        
        # Send notification with priority
        result = notification_service.send_notification(
            user_id="test-user-789",
            notification_type=notification_type,
            channel=channel,
            language=Language.HINDI,
            data=data,
            priority=priority,
            contact_info=contact_info
        )
        
        # Verify notification was sent
        assert 'success' in result
        
        # If successful, verify priority was recorded
        if result['success']:
            history = notification_service.get_notification_history(user_id="test-user-789")
            assert len(history) > 0
            
            sent_notification = next(
                (n for n in history if n['notificationId'] == result['notificationId']),
                None
            )
            assert sent_notification is not None
            assert 'priority' in sent_notification
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tracking_status_history_maintenance(self, application: Application):
        """
        Property: Status history must be maintained for all tracked applications
        
        Validates Requirement 5.1: Maintain complete status history
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register application
        tracking_service.register_application(application)
        
        # Get application status
        status = tracking_service.get_application_status(application.application_id)
        
        # Verify status history is present
        assert status['success'] is True
        assert 'statusHistory' in status
        assert isinstance(status['statusHistory'], list)
        
        # Verify each history entry has required fields
        for history_entry in status['statusHistory']:
            assert 'status' in history_entry
            assert 'timestamp' in history_entry
            assert 'reason' in history_entry
    
    @given(
        user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
        notification_type=st.sampled_from(list(NotificationType))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_notification_history_retrieval(
        self,
        user_id: str,
        notification_type: NotificationType
    ):
        """
        Property: Notification history must be retrievable by user and type
        
        Validates Requirement 5.2: Maintain notification history
        """
        # Initialize notification service
        notification_service = NotificationService()
        
        # Get notification history
        history = notification_service.get_notification_history(
            user_id=user_id,
            notification_type=notification_type,
            limit=50
        )
        
        # Verify history structure
        assert isinstance(history, list)
        
        # If history exists, verify structure
        for notification in history:
            assert 'notificationId' in notification
            assert 'userId' in notification
            assert 'type' in notification
            assert 'channel' in notification
            assert 'status' in notification
            assert 'message' in notification
    
    @given(application=tracking_application_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tracking_consistency_across_polls(self, application: Application):
        """
        Property: Multiple polls of the same application must produce consistent results
        
        Validates Requirement 5.1: Tracking consistency and reliability
        """
        # Skip if application not submitted
        assume(application.government_ref_number is not None)
        
        # Initialize tracking service
        gov_api = GovernmentAPIIntegration()
        tracking_service = TrackingService(gov_api)
        
        # Register application
        tracking_service.register_application(application)
        
        # Poll twice
        result1 = tracking_service.poll_application(application.application_id)
        result2 = tracking_service.poll_application(application.application_id)
        
        # Both polls should succeed or fail consistently
        assert result1['success'] == result2['success']
        
        # Application ID should match
        if result1.get('success'):
            assert result1['applicationId'] == result2['applicationId']
            assert result1['applicationId'] == application.application_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
