"""
Unit Tests for Multi-Channel Notification Service
Tests SMS, voice, email, and push notification functionality
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from services.notification_service import (
    NotificationService,
    SMSProvider,
    VoiceProvider,
    EmailProvider,
    PushNotificationProvider,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate
)
from shared.models.user_profile import Language, CommunicationChannel


@pytest.fixture
def sms_provider():
    """Create SMS provider instance"""
    return SMSProvider(
        account_sid="test_sid",
        auth_token="test_token",
        from_number="+919876543210"
    )


@pytest.fixture
def voice_provider():
    """Create voice provider instance"""
    return VoiceProvider(
        api_key="test_key",
        voice_gateway_url="https://voice.example.com"
    )


@pytest.fixture
def email_provider():
    """Create email provider instance"""
    return EmailProvider(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password",
        from_email="noreply@sarvasahay.gov.in"
    )


@pytest.fixture
def push_provider():
    """Create push notification provider instance"""
    return PushNotificationProvider(
        fcm_server_key="test_fcm_key"
    )


@pytest.fixture
def notification_service(sms_provider, voice_provider, email_provider, push_provider):
    """Create notification service instance"""
    return NotificationService(
        sms_provider=sms_provider,
        voice_provider=voice_provider,
        email_provider=email_provider,
        push_provider=push_provider
    )


class TestSMSProvider:
    """Test SMS provider"""
    
    def test_send_sms_success(self, sms_provider):
        """Test successful SMS sending"""
        result = sms_provider.send_sms(
            to_number="+919876543210",
            message="Test message"
        )
        
        assert result["success"] is True
        assert "messageId" in result
        assert result["to"] == "+919876543210"
        assert result["status"] == "sent"
    
    def test_send_sms_invalid_phone(self, sms_provider):
        """Test SMS with invalid phone number"""
        result = sms_provider.send_sms(
            to_number="invalid",
            message="Test message"
        )
        
        assert result["success"] is False
        assert "Invalid phone number" in result["error"]
    
    def test_send_sms_message_too_long(self, sms_provider):
        """Test SMS with message exceeding 160 characters"""
        long_message = "A" * 161
        result = sms_provider.send_sms(
            to_number="+919876543210",
            message=long_message
        )
        
        assert result["success"] is False
        assert "too long" in result["error"]
    
    def test_validate_phone_number(self, sms_provider):
        """Test phone number validation"""
        # Valid numbers
        assert sms_provider._validate_phone_number("+919876543210") is True
        assert sms_provider._validate_phone_number("9876543210") is True
        assert sms_provider._validate_phone_number("919876543210") is True
        
        # Invalid numbers
        assert sms_provider._validate_phone_number("123456") is False
        assert sms_provider._validate_phone_number("invalid") is False
    
    def test_get_delivery_status(self, sms_provider):
        """Test getting SMS delivery status"""
        status = sms_provider.get_delivery_status("SMS-123")
        
        assert status["messageId"] == "SMS-123"
        assert status["status"] == "delivered"


class TestVoiceProvider:
    """Test voice call provider"""
    
    def test_make_voice_call_success(self, voice_provider):
        """Test successful voice call"""
        result = voice_provider.make_voice_call(
            to_number="+919876543210",
            script="Test voice message",
            language=Language.HINDI
        )
        
        assert result["success"] is True
        assert "callId" in result
        assert result["to"] == "+919876543210"
        assert result["language"] == Language.HINDI
        assert result["status"] == "initiated"
    
    def test_get_call_status(self, voice_provider):
        """Test getting call status"""
        status = voice_provider.get_call_status("VOICE-123")
        
        assert status["callId"] == "VOICE-123"
        assert status["status"] == "completed"
        assert "duration" in status


class TestEmailProvider:
    """Test email provider"""
    
    def test_send_email_success(self, email_provider):
        """Test successful email sending"""
        result = email_provider.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        assert result["success"] is True
        assert "messageId" in result
        assert result["to"] == "user@example.com"
        assert result["status"] == "sent"
    
    def test_send_email_invalid_address(self, email_provider):
        """Test email with invalid address"""
        result = email_provider.send_email(
            to_email="invalid-email",
            subject="Test",
            body="Test"
        )
        
        assert result["success"] is False
        assert "Invalid email" in result["error"]
    
    def test_validate_email(self, email_provider):
        """Test email validation"""
        # Valid emails
        assert email_provider._validate_email("user@example.com") is True
        assert email_provider._validate_email("test.user@example.co.in") is True
        
        # Invalid emails
        assert email_provider._validate_email("invalid") is False
        assert email_provider._validate_email("@example.com") is False


class TestPushNotificationProvider:
    """Test push notification provider"""
    
    def test_send_push_success(self, push_provider):
        """Test successful push notification"""
        result = push_provider.send_push(
            device_token="test_device_token_123",
            title="Test Title",
            body="Test body"
        )
        
        assert result["success"] is True
        assert "messageId" in result
        assert result["status"] == "sent"


class TestNotificationService:
    """Test notification service"""
    
    def test_initialization(self, notification_service):
        """Test service initialization"""
        assert notification_service.sms_provider is not None
        assert notification_service.voice_provider is not None
        assert notification_service.email_provider is not None
        assert notification_service.push_provider is not None
        assert len(notification_service.templates) > 0
    
    def test_templates_initialized(self, notification_service):
        """Test that default templates are initialized"""
        # Check for status update templates
        assert "status_update_hindi_sms" in notification_service.templates
        assert "status_update_marathi_sms" in notification_service.templates
        
        # Check for approval templates
        assert "approval_hindi_sms" in notification_service.templates
        assert "approval_marathi_sms" in notification_service.templates
        
        # Check for payment templates
        assert "payment_hindi_sms" in notification_service.templates
    
    def test_send_sms_notification(self, notification_service):
        """Test sending SMS notification"""
        result = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={
                "application_id": "APP-001",
                "status": "Approved"
            },
            contact_info={"phone": "+919876543210"}
        )
        
        assert result["success"] is True
        assert result["channel"] == CommunicationChannel.SMS
        assert "notificationId" in result
    
    def test_send_voice_notification(self, notification_service):
        """Test sending voice notification"""
        result = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            channel=CommunicationChannel.VOICE,
            language=Language.HINDI,
            data={
                "scheme_name": "PM-KISAN",
                "amount": "6000",
                "payment_date": "15 days"
            },
            contact_info={"phone": "+919876543210"}
        )
        
        assert result["success"] is True
        assert result["channel"] == CommunicationChannel.VOICE
    
    def test_send_email_notification(self, notification_service):
        """Test sending email notification"""
        result = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.EMAIL,
            language=Language.HINDI,
            data={
                "application_id": "APP-001",
                "status": "Approved"
            },
            contact_info={"email": "user@example.com"}
        )
        
        assert result["success"] is True
        assert result["channel"] == CommunicationChannel.EMAIL
    
    def test_send_push_notification(self, notification_service):
        """Test sending push notification"""
        result = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.APP,
            language=Language.HINDI,
            data={
                "application_id": "APP-001",
                "status": "Approved"
            },
            contact_info={"device_token": "test_device_token"}
        )
        
        assert result["success"] is True
        assert result["channel"] == CommunicationChannel.APP
    
    def test_send_notification_missing_contact_info(self, notification_service):
        """Test sending notification without contact info"""
        result = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={"application_id": "APP-001", "status": "Approved"}
        )
        
        assert result["success"] is False
        assert "required" in result["error"].lower()
    
    def test_send_multi_channel(self, notification_service):
        """Test sending notification through multiple channels"""
        result = notification_service.send_multi_channel(
            user_id="user-123",
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            channels=[CommunicationChannel.SMS, CommunicationChannel.EMAIL],
            language=Language.HINDI,
            data={
                "scheme_name": "PM-KISAN",
                "amount": "6000",
                "payment_date": "15 days"
            },
            contact_info={
                "phone": "+919876543210",
                "email": "user@example.com"
            }
        )
        
        assert "results" in result
        assert CommunicationChannel.SMS in result["results"]
        assert CommunicationChannel.EMAIL in result["results"]
    
    def test_render_template(self, notification_service):
        """Test template rendering"""
        template = "Hello {name}, your application {app_id} is {status}"
        data = {
            "name": "John",
            "app_id": "APP-001",
            "status": "approved"
        }
        
        rendered = notification_service._render_template(template, data)
        
        assert rendered == "Hello John, your application APP-001 is approved"
    
    def test_render_template_missing_variable(self, notification_service):
        """Test template rendering with missing variable"""
        template = "Hello {name}, your application {app_id} is {status}"
        data = {"name": "John", "app_id": "APP-001"}
        
        # Should return template as-is if variable missing
        rendered = notification_service._render_template(template, data)
        assert rendered == template
    
    def test_get_notification_history(self, notification_service):
        """Test getting notification history"""
        # Send some notifications
        notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={"application_id": "APP-001", "status": "Approved"},
            contact_info={"phone": "+919876543210"}
        )
        
        history = notification_service.get_notification_history(user_id="user-123")
        
        assert len(history) > 0
        assert history[0]["userId"] == "user-123"
        assert history[0]["type"] == NotificationType.STATUS_UPDATE
    
    def test_get_notification_history_filtered(self, notification_service):
        """Test getting filtered notification history"""
        # Send notifications for different users
        notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={"application_id": "APP-001", "status": "Approved"},
            contact_info={"phone": "+919876543210"}
        )
        
        notification_service.send_notification(
            user_id="user-456",
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={"scheme_name": "PM-KISAN", "amount": "6000", "payment_date": "15 days"},
            contact_info={"phone": "+919876543211"}
        )
        
        # Filter by user
        history = notification_service.get_notification_history(user_id="user-123")
        assert all(n["userId"] == "user-123" for n in history)
        
        # Filter by type
        history = notification_service.get_notification_history(
            notification_type=NotificationType.APPROVAL_NOTIFICATION
        )
        assert all(n["type"] == NotificationType.APPROVAL_NOTIFICATION for n in history)
    
    def test_add_custom_template(self, notification_service):
        """Test adding custom template"""
        template = NotificationTemplate(
            template_id="custom_template",
            notification_type=NotificationType.REMINDER,
            language=Language.HINDI,
            sms_template="Custom message: {message}"
        )
        
        notification_service.add_template(template)
        
        assert "custom_template" in notification_service.templates
    
    def test_get_metrics(self, notification_service):
        """Test getting service metrics"""
        # Send some notifications
        notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={"application_id": "APP-001", "status": "Approved"},
            contact_info={"phone": "+919876543210"}
        )
        
        metrics = notification_service.get_metrics()
        
        assert "totalNotifications" in metrics
        assert "sent" in metrics
        assert "successRate" in metrics
        assert "byChannel" in metrics
        assert metrics["totalNotifications"] > 0
    
    def test_language_support(self, notification_service):
        """Test multi-language support"""
        # Test Hindi
        result_hindi = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.HINDI,
            data={"application_id": "APP-001", "status": "Approved"},
            contact_info={"phone": "+919876543210"}
        )
        assert result_hindi["success"] is True
        
        # Test Marathi
        result_marathi = notification_service.send_notification(
            user_id="user-123",
            notification_type=NotificationType.STATUS_UPDATE,
            channel=CommunicationChannel.SMS,
            language=Language.MARATHI,
            data={"application_id": "APP-001", "status": "Approved"},
            contact_info={"phone": "+919876543210"}
        )
        assert result_marathi["success"] is True
    
    def test_priority_levels(self, notification_service):
        """Test notification priority levels"""
        for priority in NotificationPriority:
            result = notification_service.send_notification(
                user_id="user-123",
                notification_type=NotificationType.STATUS_UPDATE,
                channel=CommunicationChannel.SMS,
                language=Language.HINDI,
                data={"application_id": "APP-001", "status": "Approved"},
                priority=priority,
                contact_info={"phone": "+919876543210"}
            )
            assert result["success"] is True


class TestNotificationTemplate:
    """Test notification template"""
    
    def test_template_creation(self):
        """Test creating notification template"""
        template = NotificationTemplate(
            template_id="test_template",
            notification_type=NotificationType.STATUS_UPDATE,
            language=Language.HINDI,
            sms_template="Test message: {variable}",
            variables=["variable"]
        )
        
        assert template.template_id == "test_template"
        assert template.notification_type == NotificationType.STATUS_UPDATE
        assert template.language == Language.HINDI
        assert "variable" in template.variables
