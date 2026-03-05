"""
Multi-Channel Notification Service
Handles SMS, voice, push, and email notifications for users
Supports multiple languages and communication preferences
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import re

from shared.models.user_profile import Language, CommunicationChannel


class NotificationType(str, Enum):
    """Notification type enumeration"""
    STATUS_UPDATE = "status_update"
    APPROVAL_NOTIFICATION = "approval_notification"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    DELAY_ALERT = "delay_alert"
    DOCUMENT_REQUEST = "document_request"
    REMINDER = "reminder"
    WELCOME = "welcome"
    VERIFICATION = "verification"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class NotificationTemplate:
    """Notification message template"""
    template_id: str
    notification_type: NotificationType
    language: Language
    sms_template: Optional[str] = None
    voice_script: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    variables: List[str] = field(default_factory=list)


@dataclass
class NotificationRecord:
    """Record of sent notification"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    channel: CommunicationChannel
    priority: NotificationPriority
    status: NotificationStatus
    message: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SMSProvider:
    """
    SMS notification provider
    Integrates with Twilio or similar SMS gateway
    """
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.is_configured = all([account_sid, auth_token, from_number])
    
    def send_sms(
        self,
        to_number: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Send SMS message
        
        Args:
            to_number: Recipient phone number
            message: SMS message text
            priority: Message priority
            
        Returns:
            Send result
        """
        # Validate phone number
        if not self._validate_phone_number(to_number):
            return {
                "success": False,
                "error": "Invalid phone number format"
            }
        
        # Validate message length (160 chars for single SMS)
        if len(message) > 160:
            return {
                "success": False,
                "error": f"Message too long: {len(message)} chars (max 160)"
            }
        
        if not self.is_configured:
            # Mock mode for development
            return {
                "success": True,
                "messageId": f"SMS-{datetime.utcnow().timestamp()}",
                "to": to_number,
                "message": message,
                "status": "sent",
                "sentAt": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # In production, integrate with Twilio:
        # from twilio.rest import Client
        # client = Client(self.account_sid, self.auth_token)
        # message = client.messages.create(
        #     body=message,
        #     from_=self.from_number,
        #     to=to_number
        # )
        # return {"success": True, "messageId": message.sid}
        
        return {
            "success": True,
            "messageId": f"SMS-{datetime.utcnow().timestamp()}",
            "to": to_number,
            "status": "sent",
            "sentAt": datetime.utcnow().isoformat()
        }
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate Indian phone number format"""
        cleaned = re.sub(r'[\s\-]', '', phone)
        return bool(re.match(r'^\+?91?[6-9]\d{9}$', cleaned))
    
    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get SMS delivery status
        
        Args:
            message_id: SMS message ID
            
        Returns:
            Delivery status
        """
        return {
            "messageId": message_id,
            "status": "delivered",
            "deliveredAt": datetime.utcnow().isoformat()
        }


class VoiceProvider:
    """
    Voice call notification provider
    Integrates with voice call service for non-literate users
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_gateway_url: Optional[str] = None
    ):
        self.api_key = api_key
        self.voice_gateway_url = voice_gateway_url
        self.is_configured = all([api_key, voice_gateway_url])
    
    def make_voice_call(
        self,
        to_number: str,
        script: str,
        language: Language = Language.HINDI,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Make automated voice call
        
        Args:
            to_number: Recipient phone number
            script: Voice message script
            language: Language for text-to-speech
            priority: Call priority
            
        Returns:
            Call result
        """
        if not self.is_configured:
            # Mock mode
            return {
                "success": True,
                "callId": f"VOICE-{datetime.utcnow().timestamp()}",
                "to": to_number,
                "language": language,
                "status": "initiated",
                "initiatedAt": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # In production, integrate with voice service
        return {
            "success": True,
            "callId": f"VOICE-{datetime.utcnow().timestamp()}",
            "to": to_number,
            "status": "initiated",
            "initiatedAt": datetime.utcnow().isoformat()
        }
    
    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Get voice call status
        
        Args:
            call_id: Call ID
            
        Returns:
            Call status
        """
        return {
            "callId": call_id,
            "status": "completed",
            "duration": 45,
            "completedAt": datetime.utcnow().isoformat()
        }


class EmailProvider:
    """
    Email notification provider
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.is_configured = all([smtp_host, smtp_port, username, password, from_email])
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Send email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            html_body: Email body (HTML)
            priority: Email priority
            
        Returns:
            Send result
        """
        if not self._validate_email(to_email):
            return {
                "success": False,
                "error": "Invalid email address"
            }
        
        if not self.is_configured:
            # Mock mode
            return {
                "success": True,
                "messageId": f"EMAIL-{datetime.utcnow().timestamp()}",
                "to": to_email,
                "subject": subject,
                "status": "sent",
                "sentAt": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # In production, use SMTP or email service
        return {
            "success": True,
            "messageId": f"EMAIL-{datetime.utcnow().timestamp()}",
            "to": to_email,
            "status": "sent",
            "sentAt": datetime.utcnow().isoformat()
        }
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class PushNotificationProvider:
    """
    Push notification provider for mobile apps
    """
    
    def __init__(
        self,
        fcm_server_key: Optional[str] = None
    ):
        self.fcm_server_key = fcm_server_key
        self.is_configured = fcm_server_key is not None
    
    def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Send push notification
        
        Args:
            device_token: Device FCM token
            title: Notification title
            body: Notification body
            data: Additional data payload
            priority: Notification priority
            
        Returns:
            Send result
        """
        if not self.is_configured:
            # Mock mode
            return {
                "success": True,
                "messageId": f"PUSH-{datetime.utcnow().timestamp()}",
                "deviceToken": device_token[:20] + "...",
                "status": "sent",
                "sentAt": datetime.utcnow().isoformat(),
                "mock": True
            }
        
        # In production, integrate with FCM
        return {
            "success": True,
            "messageId": f"PUSH-{datetime.utcnow().timestamp()}",
            "status": "sent",
            "sentAt": datetime.utcnow().isoformat()
        }


class NotificationService:
    """
    Multi-Channel Notification Service
    Manages notifications across SMS, voice, email, and push channels
    """
    
    def __init__(
        self,
        sms_provider: Optional[SMSProvider] = None,
        voice_provider: Optional[VoiceProvider] = None,
        email_provider: Optional[EmailProvider] = None,
        push_provider: Optional[PushNotificationProvider] = None
    ):
        self.sms_provider = sms_provider or SMSProvider()
        self.voice_provider = voice_provider or VoiceProvider()
        self.email_provider = email_provider or EmailProvider()
        self.push_provider = push_provider or PushNotificationProvider()
        
        # Notification templates
        self.templates: Dict[str, NotificationTemplate] = {}
        self._initialize_templates()
        
        # Notification history
        self.notification_history: List[NotificationRecord] = []
    
    def _initialize_templates(self):
        """Initialize default notification templates"""
        # Status update templates
        self.templates["status_update_hindi_sms"] = NotificationTemplate(
            template_id="status_update_hindi_sms",
            notification_type=NotificationType.STATUS_UPDATE,
            language=Language.HINDI,
            sms_template="आपके आवेदन {application_id} की स्थिति अपडेट: {status}. विवरण के लिए ऐप देखें।",
            variables=["application_id", "status"]
        )
        
        self.templates["status_update_marathi_sms"] = NotificationTemplate(
            template_id="status_update_marathi_sms",
            notification_type=NotificationType.STATUS_UPDATE,
            language=Language.MARATHI,
            sms_template="तुमच्या अर्जाची {application_id} स्थिती अद्यतनित: {status}. तपशीलासाठी अॅप पहा।",
            variables=["application_id", "status"]
        )
        
        # Approval notification templates
        self.templates["approval_hindi_sms"] = NotificationTemplate(
            template_id="approval_hindi_sms",
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            language=Language.HINDI,
            sms_template="बधाई हो! आपका {scheme_name} आवेदन स्वीकृत हो गया है। राशि: ₹{amount}. भुगतान तिथि: {payment_date}",
            variables=["scheme_name", "amount", "payment_date"]
        )
        
        self.templates["approval_marathi_sms"] = NotificationTemplate(
            template_id="approval_marathi_sms",
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            language=Language.MARATHI,
            sms_template="अभिनंदन! तुमचा {scheme_name} अर्ज मंजूर झाला आहे। रक्कम: ₹{amount}. पेमेंट तारीख: {payment_date}",
            variables=["scheme_name", "amount", "payment_date"]
        )
        
        # Payment confirmation templates
        self.templates["payment_hindi_sms"] = NotificationTemplate(
            template_id="payment_hindi_sms",
            notification_type=NotificationType.PAYMENT_CONFIRMATION,
            language=Language.HINDI,
            sms_template="भुगतान प्राप्त! ₹{amount} आपके खाते में जमा किया गया है। संदर्भ: {reference}",
            variables=["amount", "reference"]
        )
        
        # Delay alert templates
        self.templates["delay_hindi_sms"] = NotificationTemplate(
            template_id="delay_hindi_sms",
            notification_type=NotificationType.DELAY_ALERT,
            language=Language.HINDI,
            sms_template="आपका आवेदन {application_id} में देरी हो रही है। कृपया {action} करें।",
            variables=["application_id", "action"]
        )
        
        # Voice script templates
        self.templates["approval_hindi_voice"] = NotificationTemplate(
            template_id="approval_hindi_voice",
            notification_type=NotificationType.APPROVAL_NOTIFICATION,
            language=Language.HINDI,
            voice_script="नमस्ते। यह सरवसहाय से संदेश है। आपका {scheme_name} योजना का आवेदन स्वीकृत हो गया है। आपको {amount} रुपये की राशि {payment_date} तक मिलेगी। धन्यवाद।",
            variables=["scheme_name", "amount", "payment_date"]
        )
    
    def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        channel: CommunicationChannel,
        language: Language,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        contact_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send notification through specified channel
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            channel: Communication channel
            language: Preferred language
            data: Data for template variables
            priority: Notification priority
            contact_info: Contact information (phone, email, etc.)
            
        Returns:
            Send result
        """
        # Get appropriate template
        template_key = f"{notification_type}_{language}_{channel}"
        template = self.templates.get(template_key)
        
        if not template:
            # Fallback to English SMS
            template_key = f"{notification_type}_hindi_sms"
            template = self.templates.get(template_key)
        
        if not template:
            return {
                "success": False,
                "error": f"No template found for {notification_type} in {language}"
            }
        
        # Generate notification ID
        notification_id = f"NOTIF-{datetime.utcnow().timestamp()}"
        
        # Send through appropriate channel
        result = None
        message = None
        
        if channel == CommunicationChannel.SMS:
            if not contact_info or "phone" not in contact_info:
                return {"success": False, "error": "Phone number required for SMS"}
            
            message = self._render_template(template.sms_template, data)
            result = self.sms_provider.send_sms(
                to_number=contact_info["phone"],
                message=message,
                priority=priority
            )
        
        elif channel == CommunicationChannel.VOICE:
            if not contact_info or "phone" not in contact_info:
                return {"success": False, "error": "Phone number required for voice call"}
            
            script = self._render_template(template.voice_script, data)
            result = self.voice_provider.make_voice_call(
                to_number=contact_info["phone"],
                script=script,
                language=language,
                priority=priority
            )
            message = script
        
        elif channel == CommunicationChannel.EMAIL:
            if not contact_info or "email" not in contact_info:
                return {"success": False, "error": "Email address required"}
            
            subject = template.email_subject or f"SarvaSahay - {notification_type}"
            body = self._render_template(template.email_body or template.sms_template, data)
            result = self.email_provider.send_email(
                to_email=contact_info["email"],
                subject=subject,
                body=body,
                priority=priority
            )
            message = body
        
        elif channel == CommunicationChannel.APP:
            if not contact_info or "device_token" not in contact_info:
                return {"success": False, "error": "Device token required for push notification"}
            
            title = template.push_title or "SarvaSahay Update"
            body = self._render_template(template.push_body or template.sms_template, data)
            result = self.push_provider.send_push(
                device_token=contact_info["device_token"],
                title=title,
                body=body,
                data=data,
                priority=priority
            )
            message = body
        
        # Record notification
        if result and result.get("success"):
            record = NotificationRecord(
                notification_id=notification_id,
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                priority=priority,
                status=NotificationStatus.SENT,
                message=message,
                sent_at=datetime.utcnow(),
                metadata={
                    "template_id": template.template_id,
                    "language": language,
                    "data": data,
                    "provider_result": result
                }
            )
            self.notification_history.append(record)
        
        return {
            "success": result.get("success", False) if result else False,
            "notificationId": notification_id,
            "channel": channel,
            "providerResult": result
        }
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Render template with data
        
        Args:
            template: Template string with {variable} placeholders
            data: Data dictionary
            
        Returns:
            Rendered message
        """
        if not template:
            return ""
        
        try:
            return template.format(**data)
        except KeyError as e:
            return template  # Return template as-is if variable missing
    
    def send_multi_channel(
        self,
        user_id: str,
        notification_type: NotificationType,
        channels: List[CommunicationChannel],
        language: Language,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        contact_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send notification through multiple channels
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            channels: List of channels to use
            language: Preferred language
            data: Data for template variables
            priority: Notification priority
            contact_info: Contact information
            
        Returns:
            Results for all channels
        """
        results = {}
        
        for channel in channels:
            result = self.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                language=language,
                data=data,
                priority=priority,
                contact_info=contact_info
            )
            results[channel] = result
        
        return {
            "success": any(r.get("success") for r in results.values()),
            "results": results
        }
    
    def get_notification_history(
        self,
        user_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get notification history
        
        Args:
            user_id: Filter by user ID
            notification_type: Filter by notification type
            limit: Maximum number of records
            
        Returns:
            List of notification records
        """
        filtered = self.notification_history
        
        if user_id:
            filtered = [n for n in filtered if n.user_id == user_id]
        
        if notification_type:
            filtered = [n for n in filtered if n.notification_type == notification_type]
        
        # Sort by sent_at descending
        filtered.sort(key=lambda n: n.sent_at or datetime.min, reverse=True)
        
        return [
            {
                "notificationId": n.notification_id,
                "userId": n.user_id,
                "type": n.notification_type,
                "channel": n.channel,
                "priority": n.priority,
                "status": n.status,
                "message": n.message,
                "sentAt": n.sent_at.isoformat() if n.sent_at else None,
                "deliveredAt": n.delivered_at.isoformat() if n.delivered_at else None
            }
            for n in filtered[:limit]
        ]
    
    def add_template(self, template: NotificationTemplate):
        """
        Add custom notification template
        
        Args:
            template: Notification template
        """
        self.templates[template.template_id] = template
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get notification service metrics
        
        Returns:
            Service metrics
        """
        total = len(self.notification_history)
        sent = sum(1 for n in self.notification_history if n.status == NotificationStatus.SENT)
        delivered = sum(1 for n in self.notification_history if n.status == NotificationStatus.DELIVERED)
        failed = sum(1 for n in self.notification_history if n.status == NotificationStatus.FAILED)
        
        by_channel = {}
        for channel in CommunicationChannel:
            count = sum(1 for n in self.notification_history if n.channel == channel)
            by_channel[channel] = count
        
        return {
            "totalNotifications": total,
            "sent": sent,
            "delivered": delivered,
            "failed": failed,
            "successRate": (sent / total * 100) if total > 0 else 0,
            "byChannel": by_channel,
            "templates": len(self.templates)
        }
