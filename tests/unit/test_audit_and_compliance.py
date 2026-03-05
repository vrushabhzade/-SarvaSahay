"""
Unit tests for audit logging and GDPR compliance
Tests comprehensive audit trails and data protection features
"""

import pytest
from datetime import datetime, timedelta
from shared.utils.audit_log import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    get_audit_logger
)
from shared.utils.gdpr_compliance import (
    GDPRComplianceService,
    DataRequestType,
    RequestStatus,
    ConsentType,
    get_gdpr_service
)


class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_log_basic_event(self):
        """Test logging a basic audit event"""
        logger = AuditLogger()
        
        event = logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            user_id="user123",
            username="testuser",
            resource_type="profile",
            resource_id="profile456"
        )
        
        assert event.event_type == AuditEventType.PROFILE_CREATED
        assert event.user_id == "user123"
        assert event.username == "testuser"
        assert event.resource_type == "profile"
        assert event.resource_id == "profile456"
        assert event.success is True
    
    def test_log_user_login_success(self):
        """Test logging successful user login"""
        logger = AuditLogger()
        
        event = logger.log_user_login(
            username="testuser",
            user_id="user123",
            ip_address="192.168.1.1",
            success=True,
            mfa_used=True
        )
        
        assert event.event_type == AuditEventType.USER_LOGIN
        assert event.success is True
        assert event.details['mfa_used'] is True
        assert event.severity == AuditSeverity.INFO
    
    def test_log_user_login_failure(self):
        """Test logging failed user login"""
        logger = AuditLogger()
        
        event = logger.log_user_login(
            username="testuser",
            user_id="user123",
            ip_address="192.168.1.1",
            success=False,
            error_message="Invalid password"
        )
        
        assert event.event_type == AuditEventType.USER_LOGIN_FAILED
        assert event.success is False
        assert event.error_message == "Invalid password"
        assert event.severity == AuditSeverity.WARNING
    
    def test_log_profile_access(self):
        """Test logging profile access"""
        logger = AuditLogger()
        
        event = logger.log_profile_access(
            action="updated",
            profile_id="profile123",
            user_id="user456",
            username="testuser",
            changes={'income': 'updated'}
        )
        
        assert event.event_type == AuditEventType.PROFILE_UPDATED
        assert event.resource_id == "profile123"
        assert event.details['changes'] == {'income': 'updated'}
    
    def test_log_document_access(self):
        """Test logging document access"""
        logger = AuditLogger()
        
        event = logger.log_document_access(
            action="uploaded",
            document_id="doc123",
            document_type="aadhaar",
            user_id="user456",
            username="testuser"
        )
        
        assert event.event_type == AuditEventType.DOCUMENT_UPLOADED
        assert event.resource_id == "doc123"
        assert event.details['document_type'] == "aadhaar"
    
    def test_log_gdpr_action(self):
        """Test logging GDPR action"""
        logger = AuditLogger()
        
        event = logger.log_gdpr_action(
            action="data_deletion",
            user_id="user123",
            username="testuser",
            request_type="erasure"
        )
        
        assert event.event_type == AuditEventType.GDPR_DATA_DELETION
        assert event.details['request_type'] == "erasure"
    
    def test_log_suspicious_activity(self):
        """Test logging suspicious activity"""
        logger = AuditLogger()
        
        event = logger.log_suspicious_activity(
            description="Multiple failed login attempts",
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1"
        )
        
        assert event.event_type == AuditEventType.SUSPICIOUS_ACTIVITY
        assert event.severity == AuditSeverity.WARNING
        assert "Multiple failed login attempts" in event.action
    
    def test_get_user_audit_trail(self):
        """Test retrieving user audit trail"""
        logger = AuditLogger()
        
        # Log multiple events for user
        logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            user_id="user123"
        )
        logger.log_event(
            event_type=AuditEventType.PROFILE_UPDATED,
            action="Profile updated",
            user_id="user123"
        )
        logger.log_event(
            event_type=AuditEventType.PROFILE_VIEWED,
            action="Profile viewed",
            user_id="user456"
        )
        
        # Get audit trail for user123
        trail = logger.get_user_audit_trail("user123")
        
        assert len(trail) == 2
        assert all(event.user_id == "user123" for event in trail)
    
    def test_get_resource_audit_trail(self):
        """Test retrieving resource audit trail"""
        logger = AuditLogger()
        
        # Log events for specific resource
        logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            resource_type="profile",
            resource_id="profile123"
        )
        logger.log_event(
            event_type=AuditEventType.PROFILE_UPDATED,
            action="Profile updated",
            resource_type="profile",
            resource_id="profile123"
        )
        
        # Get audit trail for resource
        trail = logger.get_resource_audit_trail("profile", "profile123")
        
        assert len(trail) == 2
        assert all(event.resource_id == "profile123" for event in trail)
    
    def test_get_security_events(self):
        """Test retrieving security events"""
        logger = AuditLogger()
        
        # Log various events
        logger.log_event(
            event_type=AuditEventType.USER_LOGIN_FAILED,
            action="Login failed"
        )
        logger.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            action="Suspicious activity"
        )
        logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created"
        )
        
        # Get security events
        security_events = logger.get_security_events()
        
        assert len(security_events) == 2
        assert all(
            event.event_type in [
                AuditEventType.USER_LOGIN_FAILED,
                AuditEventType.SUSPICIOUS_ACTIVITY
            ]
            for event in security_events
        )
    
    def test_suspicious_activity_detection(self):
        """Test automatic suspicious activity detection"""
        logger = AuditLogger()
        
        # Simulate 5 failed login attempts
        for _ in range(5):
            logger.log_user_login(
                username="testuser",
                user_id="user123",
                ip_address="192.168.1.1",
                success=False
            )
        
        # Check for suspicious activity event
        suspicious_events = [
            event for event in logger.audit_logs
            if event.event_type == AuditEventType.SUSPICIOUS_ACTIVITY
        ]
        
        assert len(suspicious_events) > 0
    
    def test_export_audit_logs_json(self):
        """Test exporting audit logs as JSON"""
        logger = AuditLogger()
        
        logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created"
        )
        
        exported = logger.export_audit_logs(format='json')
        
        assert isinstance(exported, str)
        assert 'profile_created' in exported
    
    def test_export_audit_logs_csv(self):
        """Test exporting audit logs as CSV"""
        logger = AuditLogger()
        
        logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created"
        )
        
        exported = logger.export_audit_logs(format='csv')
        
        assert isinstance(exported, str)
        assert 'event_id' in exported
        assert 'profile_created' in exported
    
    def test_get_audit_statistics(self):
        """Test getting audit statistics"""
        logger = AuditLogger()
        
        # Log various events
        logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            success=True
        )
        logger.log_event(
            event_type=AuditEventType.PROFILE_UPDATED,
            action="Profile updated",
            success=False
        )
        
        stats = logger.get_audit_statistics()
        
        assert stats['total_events'] == 2
        assert stats['failed_events'] == 1
        assert 'event_type_counts' in stats
        assert 'severity_counts' in stats


class TestGDPRCompliance:
    """Test GDPR compliance functionality"""
    
    def test_create_access_request(self):
        """Test creating a data access request"""
        service = GDPRComplianceService()
        
        request = service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ACCESS,
            requested_by="user123"
        )
        
        assert request.user_id == "user123"
        assert request.request_type == DataRequestType.ACCESS
        assert request.status == RequestStatus.PENDING
    
    def test_create_erasure_request(self):
        """Test creating a data erasure request"""
        service = GDPRComplianceService()
        
        request = service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ERASURE,
            requested_by="user123"
        )
        
        assert request.request_type == DataRequestType.ERASURE
        assert "user123" in service.deletion_queue
    
    def test_process_access_request(self):
        """Test processing a data access request"""
        service = GDPRComplianceService()
        
        # Create request
        request = service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ACCESS,
            requested_by="user123"
        )
        
        # Process request
        user_data = {
            'profile': {'name': 'Test User', 'age': 30},
            'documents': ['doc1', 'doc2']
        }
        
        result = service.process_access_request(request.request_id, user_data)
        
        assert result['user_id'] == "user123"
        assert result['data'] == user_data
        assert request.status == RequestStatus.COMPLETED
    
    def test_process_erasure_request(self):
        """Test processing a data erasure request"""
        service = GDPRComplianceService()
        
        # Create request
        request = service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ERASURE,
            requested_by="user123"
        )
        
        # Process request
        result = service.process_erasure_request(request.request_id, "user123")
        
        assert result['user_id'] == "user123"
        assert result['status'] == 'scheduled'
        assert 'scheduled_deletion_date' in result
        assert request.status == RequestStatus.COMPLETED
    
    def test_process_portability_request_json(self):
        """Test processing a data portability request (JSON)"""
        service = GDPRComplianceService()
        
        # Create request
        request = service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.PORTABILITY,
            requested_by="user123"
        )
        
        # Process request
        user_data = {'name': 'Test User', 'age': 30}
        result = service.process_portability_request(
            request.request_id,
            user_data,
            format='json'
        )
        
        assert isinstance(result, str)
        assert 'Test User' in result
        assert request.status == RequestStatus.COMPLETED
    
    def test_process_portability_request_csv(self):
        """Test processing a data portability request (CSV)"""
        service = GDPRComplianceService()
        
        # Create request
        request = service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.PORTABILITY,
            requested_by="user123"
        )
        
        # Process request
        user_data = {'name': 'Test User', 'age': 30}
        result = service.process_portability_request(
            request.request_id,
            user_data,
            format='csv'
        )
        
        assert isinstance(result, str)
        assert 'name,Test User' in result
    
    def test_record_consent_granted(self):
        """Test recording user consent"""
        service = GDPRComplianceService()
        
        consent = service.record_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=True,
            ip_address="192.168.1.1"
        )
        
        assert consent.user_id == "user123"
        assert consent.consent_type == ConsentType.DATA_PROCESSING
        assert consent.granted is True
        assert consent.withdrawn_at is None
    
    def test_record_consent_withdrawn(self):
        """Test recording consent withdrawal"""
        service = GDPRComplianceService()
        
        consent = service.record_consent(
            user_id="user123",
            consent_type=ConsentType.MARKETING,
            granted=False
        )
        
        assert consent.granted is False
        assert consent.withdrawn_at is not None
    
    def test_check_consent_granted(self):
        """Test checking if consent is granted"""
        service = GDPRComplianceService()
        
        # Grant consent
        service.record_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=True
        )
        
        # Check consent
        has_consent = service.check_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING
        )
        
        assert has_consent is True
    
    def test_check_consent_not_granted(self):
        """Test checking consent when not granted"""
        service = GDPRComplianceService()
        
        # Check consent without granting
        has_consent = service.check_consent(
            user_id="user123",
            consent_type=ConsentType.MARKETING
        )
        
        assert has_consent is False
    
    def test_check_consent_after_withdrawal(self):
        """Test checking consent after withdrawal"""
        service = GDPRComplianceService()
        
        # Grant consent
        service.record_consent(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
            granted=True
        )
        
        # Withdraw consent
        service.record_consent(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
            granted=False
        )
        
        # Check consent
        has_consent = service.check_consent(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS
        )
        
        assert has_consent is False
    
    def test_get_user_consents(self):
        """Test retrieving all user consents"""
        service = GDPRComplianceService()
        
        # Record multiple consents
        service.record_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=True
        )
        service.record_consent(
            user_id="user123",
            consent_type=ConsentType.MARKETING,
            granted=False
        )
        
        consents = service.get_user_consents("user123")
        
        assert len(consents) == 2
    
    def test_get_user_requests(self):
        """Test retrieving all user GDPR requests"""
        service = GDPRComplianceService()
        
        # Create multiple requests
        service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ACCESS,
            requested_by="user123"
        )
        service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ERASURE,
            requested_by="user123"
        )
        
        requests = service.get_user_requests("user123")
        
        assert len(requests) == 2
    
    def test_get_pending_requests(self):
        """Test retrieving pending GDPR requests"""
        service = GDPRComplianceService()
        
        # Create pending request
        service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ACCESS,
            requested_by="user123"
        )
        
        pending = service.get_pending_requests()
        
        assert len(pending) == 1
        assert pending[0].status == RequestStatus.PENDING
    
    def test_anonymize_user_data(self):
        """Test anonymizing user data"""
        service = GDPRComplianceService()
        
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30,
            'documents': {
                'aadhaar': '123456789012',
                'pan': 'ABCDE1234F'
            }
        }
        
        anonymized = service.anonymize_user_data(user_data)
        
        assert anonymized['name'] == '[REDACTED]'
        assert anonymized['email'] == '[REDACTED]'
        assert anonymized['age'] == 30  # Non-PII field preserved
        assert anonymized['documents']['aadhaar'] == '[REDACTED]'
    
    def test_generate_compliance_report(self):
        """Test generating GDPR compliance report"""
        service = GDPRComplianceService()
        
        # Create some requests
        service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ACCESS,
            requested_by="user123"
        )
        service.create_data_request(
            user_id="user456",
            request_type=DataRequestType.ERASURE,
            requested_by="user456"
        )
        
        report = service.generate_compliance_report()
        
        assert report['total_requests'] == 2
        assert 'request_type_counts' in report
        assert 'status_counts' in report
        assert 'compliance_rate' in report


class TestGlobalServices:
    """Test global service instances"""
    
    def test_get_audit_logger_singleton(self):
        """Test that get_audit_logger returns singleton instance"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        assert logger1 is logger2
    
    def test_get_gdpr_service_singleton(self):
        """Test that get_gdpr_service returns singleton instance"""
        service1 = get_gdpr_service()
        service2 = get_gdpr_service()
        
        assert service1 is service2
