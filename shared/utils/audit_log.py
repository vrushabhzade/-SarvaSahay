"""
Audit Logging Service
Implements comprehensive audit trails for compliance and security monitoring
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from dataclasses import dataclass, asdict


class AuditEventType(str, Enum):
    """Types of audit events"""
    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    
    # Profile actions
    PROFILE_CREATED = "profile_created"
    PROFILE_VIEWED = "profile_viewed"
    PROFILE_UPDATED = "profile_updated"
    PROFILE_DELETED = "profile_deleted"
    
    # Document actions
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_VIEWED = "document_viewed"
    DOCUMENT_DELETED = "document_deleted"
    
    # Application actions
    APPLICATION_CREATED = "application_created"
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_VIEWED = "application_viewed"
    APPLICATION_UPDATED = "application_updated"
    
    # Data access
    DATA_EXPORTED = "data_exported"
    DATA_ACCESSED = "data_accessed"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # Admin actions
    ADMIN_ACCESS = "admin_access"
    PERMISSION_CHANGED = "permission_changed"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    
    # GDPR compliance
    GDPR_DATA_REQUEST = "gdpr_data_request"
    GDPR_DATA_DELETION = "gdpr_data_deletion"
    GDPR_CONSENT_GIVEN = "gdpr_consent_given"
    GDPR_CONSENT_WITHDRAWN = "gdpr_consent_withdrawn"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: str
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Audit logging service for compliance and security monitoring
    Maintains comprehensive audit trails for all system actions
    """
    
    def __init__(self):
        # In-memory storage for demo (use database in production)
        self.audit_logs: List[AuditEvent] = []
        self.suspicious_activity_threshold = 5
        self.suspicious_activity_window_minutes = 15
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO
    ) -> AuditEvent:
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            action: Description of action performed
            user_id: User ID performing the action
            username: Username performing the action
            ip_address: IP address of the request
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional event details
            success: Whether the action was successful
            error_message: Error message if action failed
            severity: Event severity level
            
        Returns:
            Created audit event
        """
        # Generate event ID
        event_id = self._generate_event_id(event_type, user_id, resource_id)
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            success=success,
            error_message=error_message
        )
        
        # Store event
        self.audit_logs.append(event)
        
        # Check for suspicious activity
        if not success and event_type in [
            AuditEventType.USER_LOGIN_FAILED,
            AuditEventType.SUSPICIOUS_ACTIVITY
        ]:
            self._check_suspicious_activity(user_id, username, ip_address)
        
        return event
    
    def log_user_login(
        self,
        username: str,
        user_id: str,
        ip_address: str,
        success: bool,
        mfa_used: bool = False,
        error_message: Optional[str] = None
    ) -> AuditEvent:
        """Log user login attempt"""
        event_type = AuditEventType.USER_LOGIN if success else AuditEventType.USER_LOGIN_FAILED
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        return self.log_event(
            event_type=event_type,
            action=f"User login {'successful' if success else 'failed'}",
            user_id=user_id if success else None,
            username=username,
            ip_address=ip_address,
            details={
                'mfa_used': mfa_used,
                'login_method': 'password_mfa' if mfa_used else 'password'
            },
            success=success,
            error_message=error_message,
            severity=severity
        )
    
    def log_profile_access(
        self,
        action: str,
        profile_id: str,
        user_id: str,
        username: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log profile access or modification"""
        event_type_map = {
            'created': AuditEventType.PROFILE_CREATED,
            'viewed': AuditEventType.PROFILE_VIEWED,
            'updated': AuditEventType.PROFILE_UPDATED,
            'deleted': AuditEventType.PROFILE_DELETED
        }
        
        event_type = event_type_map.get(action, AuditEventType.PROFILE_VIEWED)
        
        return self.log_event(
            event_type=event_type,
            action=f"Profile {action}",
            user_id=user_id,
            username=username,
            resource_type='profile',
            resource_id=profile_id,
            details={'changes': changes} if changes else {}
        )
    
    def log_document_access(
        self,
        action: str,
        document_id: str,
        document_type: str,
        user_id: str,
        username: str
    ) -> AuditEvent:
        """Log document access or processing"""
        event_type_map = {
            'uploaded': AuditEventType.DOCUMENT_UPLOADED,
            'processed': AuditEventType.DOCUMENT_PROCESSED,
            'viewed': AuditEventType.DOCUMENT_VIEWED,
            'deleted': AuditEventType.DOCUMENT_DELETED
        }
        
        event_type = event_type_map.get(action, AuditEventType.DOCUMENT_VIEWED)
        
        return self.log_event(
            event_type=event_type,
            action=f"Document {action}",
            user_id=user_id,
            username=username,
            resource_type='document',
            resource_id=document_id,
            details={'document_type': document_type}
        )
    
    def log_gdpr_action(
        self,
        action: str,
        user_id: str,
        username: str,
        request_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log GDPR compliance action"""
        event_type_map = {
            'data_request': AuditEventType.GDPR_DATA_REQUEST,
            'data_deletion': AuditEventType.GDPR_DATA_DELETION,
            'consent_given': AuditEventType.GDPR_CONSENT_GIVEN,
            'consent_withdrawn': AuditEventType.GDPR_CONSENT_WITHDRAWN
        }
        
        event_type = event_type_map.get(action, AuditEventType.GDPR_DATA_REQUEST)
        
        return self.log_event(
            event_type=event_type,
            action=f"GDPR {action}",
            user_id=user_id,
            username=username,
            resource_type='gdpr_request',
            details={
                'request_type': request_type,
                **(details or {})
            },
            severity=AuditSeverity.INFO
        )
    
    def log_suspicious_activity(
        self,
        description: str,
        user_id: Optional[str],
        username: Optional[str],
        ip_address: Optional[str],
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log suspicious activity"""
        return self.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            action=f"Suspicious activity detected: {description}",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details or {},
            severity=AuditSeverity.WARNING
        )
    
    def get_user_audit_trail(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> List[AuditEvent]:
        """
        Get audit trail for a specific user
        
        Args:
            user_id: User ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to filter
            
        Returns:
            List of audit events for the user
        """
        filtered_events = [
            event for event in self.audit_logs
            if event.user_id == user_id
        ]
        
        # Apply date filters
        if start_date:
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event.timestamp) >= start_date
            ]
        
        if end_date:
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event.timestamp) <= end_date
            ]
        
        # Apply event type filter
        if event_types:
            filtered_events = [
                event for event in filtered_events
                if event.event_type in event_types
            ]
        
        return filtered_events
    
    def get_resource_audit_trail(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[AuditEvent]:
        """Get audit trail for a specific resource"""
        return [
            event for event in self.audit_logs
            if event.resource_type == resource_type and event.resource_id == resource_id
        ]
    
    def get_security_events(
        self,
        severity: Optional[AuditSeverity] = None,
        hours: int = 24
    ) -> List[AuditEvent]:
        """
        Get security-related events
        
        Args:
            severity: Optional severity filter
            hours: Number of hours to look back
            
        Returns:
            List of security events
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        security_event_types = [
            AuditEventType.USER_LOGIN_FAILED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.ACCOUNT_LOCKED,
            AuditEventType.ACCOUNT_UNLOCKED,
            AuditEventType.ADMIN_ACCESS,
            AuditEventType.PERMISSION_CHANGED
        ]
        
        filtered_events = [
            event for event in self.audit_logs
            if event.event_type in security_event_types
            and datetime.fromisoformat(event.timestamp) >= cutoff_time
        ]
        
        if severity:
            filtered_events = [
                event for event in filtered_events
                if event.severity == severity
            ]
        
        return filtered_events
    
    def _check_suspicious_activity(
        self,
        user_id: Optional[str],
        username: Optional[str],
        ip_address: Optional[str]
    ) -> None:
        """
        Check for suspicious activity patterns
        Triggers alert if threshold is exceeded
        """
        cutoff_time = datetime.utcnow() - timedelta(
            minutes=self.suspicious_activity_window_minutes
        )
        
        # Count recent failed attempts
        recent_failures = [
            event for event in self.audit_logs
            if event.event_type == AuditEventType.USER_LOGIN_FAILED
            and datetime.fromisoformat(event.timestamp) >= cutoff_time
            and (
                (user_id and event.user_id == user_id) or
                (username and event.username == username) or
                (ip_address and event.ip_address == ip_address)
            )
        ]
        
        if len(recent_failures) >= self.suspicious_activity_threshold:
            self.log_suspicious_activity(
                description=f"Multiple failed login attempts ({len(recent_failures)})",
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                details={
                    'failed_attempts': len(recent_failures),
                    'time_window_minutes': self.suspicious_activity_window_minutes
                }
            )
    
    def _generate_event_id(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        resource_id: Optional[str]
    ) -> str:
        """Generate unique event ID"""
        data = f"{event_type.value}-{user_id}-{resource_id}-{datetime.utcnow().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def export_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json'
    ) -> str:
        """
        Export audit logs for compliance reporting
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            format: Export format ('json' or 'csv')
            
        Returns:
            Exported audit logs as string
        """
        filtered_events = self.audit_logs
        
        if start_date:
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event.timestamp) >= start_date
            ]
        
        if end_date:
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event.timestamp) <= end_date
            ]
        
        if format == 'json':
            return json.dumps(
                [event.to_dict() for event in filtered_events],
                indent=2
            )
        elif format == 'csv':
            # Simple CSV export
            lines = ['event_id,event_type,timestamp,user_id,username,action,success']
            for event in filtered_events:
                lines.append(
                    f"{event.event_id},{event.event_type.value},{event.timestamp},"
                    f"{event.user_id or ''},{event.username or ''},{event.action},"
                    f"{event.success}"
                )
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_audit_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get audit statistics for monitoring
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with audit statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.audit_logs
            if datetime.fromisoformat(event.timestamp) >= cutoff_time
        ]
        
        # Count by event type
        event_type_counts = {}
        for event in recent_events:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for event in recent_events:
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count failures
        failed_events = [event for event in recent_events if not event.success]
        
        return {
            'total_events': len(recent_events),
            'time_period_hours': hours,
            'event_type_counts': event_type_counts,
            'severity_counts': severity_counts,
            'failed_events': len(failed_events),
            'success_rate': (len(recent_events) - len(failed_events)) / len(recent_events) * 100
            if recent_events else 0
        }


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
