"""
Integration tests for government API compliance and integration
Tests Requirements 8.1, 8.2, 8.3, 8.4
"""

import pytest
from datetime import datetime, timedelta

from services.government_api_client import (
    GovernmentAPIIntegration,
    StateGovernmentClient,
    APIVersionManager,
    APIError
)
from services.compliance_reporting_service import (
    get_compliance_service,
    ComplianceStandard,
    ReportType
)
from shared.utils.audit_log import get_audit_logger, AuditEventType
from shared.utils.gdpr_compliance import get_gdpr_service, DataRequestType


class TestGovernmentAPIIntegration:
    """Test government API integration features"""
    
    def test_pm_kisan_integration(self):
        """Test PM-KISAN API integration"""
        # Requirement 8.1: Use official government APIs
        api_integration = GovernmentAPIIntegration()
        
        # Submit application
        application_data = {
            "aadhaar_number": "123456789012",
            "name": "Test Farmer",
            "bank_account": "1234567890",
            "bank_ifsc": "SBIN0001234",
            "land_ownership": 2.5
        }
        
        result = api_integration.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        assert result["success"] is True
        assert "referenceNumber" in result
        assert result["status"] == "submitted"
    
    def test_dbt_integration(self):
        """Test DBT system integration"""
        # Requirement 8.1: Use official government APIs
        api_integration = GovernmentAPIIntegration()
        
        # Register beneficiary
        beneficiary_data = {
            "aadhaar_number": "123456789012",
            "bank_account": "1234567890",
            "bank_ifsc": "SBIN0001234",
            "scheme_id": "PM-KISAN"
        }
        
        result = api_integration.dbt.register_beneficiary(beneficiary_data)
        
        assert result["success"] is True
        assert "beneficiaryId" in result
        assert result["status"] == "registered"
    
    def test_pfms_integration(self):
        """Test PFMS payment tracking"""
        # Requirement 8.1: Use official government APIs
        api_integration = GovernmentAPIIntegration()
        
        # Track payment
        result = api_integration.track_payment("TXN123456")
        
        assert "transactionId" in result
        assert "status" in result
    
    def test_state_government_api_integration(self):
        """Test state government API connections"""
        # Requirement 8.1: Add state government API connections
        state_configs = {
            "Maharashtra": {
                "base_url": "https://api.maharashtra.gov.in/v1",
                "api_key": "test_key"
            },
            "Karnataka": {
                "base_url": "https://api.karnataka.gov.in/v1",
                "api_key": "test_key"
            }
        }
        
        api_integration = GovernmentAPIIntegration(
            state_configs=state_configs
        )
        
        # Verify state clients are initialized
        assert "Maharashtra" in api_integration.state_clients
        assert "Karnataka" in api_integration.state_clients
        
        # Submit state application
        application_data = {
            "scheme_id": "MH-FARMER-SCHEME",
            "applicant_name": "Test Applicant"
        }
        
        result = api_integration.submit_application(
            scheme_id="MH-FARMER-SCHEME",
            application_data=application_data,
            state="Maharashtra"
        )
        
        assert result["success"] is True
        assert result["state"] == "Maharashtra"
    
    def test_api_versioning(self):
        """Test API versioning and change adaptation"""
        # Requirement 8.4: Implement API versioning and change adaptation
        version_manager = APIVersionManager()
        
        # Register API version
        version_manager.register_version(
            "TEST-API",
            "v1",
            {
                "submit": "/v1/submit",
                "status": "/v1/status"
            }
        )
        
        # Get endpoint
        endpoint = version_manager.get_endpoint("TEST-API", "v1", "submit")
        assert endpoint == "/v1/submit"
        
        # Register new version
        version_manager.register_version(
            "TEST-API",
            "v2",
            {
                "submit": "/v2/applications/submit",
                "status": "/v2/applications/status"
            }
        )
        
        # Get new endpoint
        endpoint = version_manager.get_endpoint("TEST-API", "v2", "submit")
        assert endpoint == "/v2/applications/submit"
    
    def test_api_change_adaptation(self):
        """Test adaptation to API changes within 48 hours"""
        # Requirement 8.4: Adapt to API changes within 48 hours
        api_integration = GovernmentAPIIntegration()
        
        # Simulate API change
        change_log = {
            "endpoint_mappings": {
                "submit_application": "/v2/farmer/register",
                "check_status": "/v2/applications/status/{ref}"
            },
            "deprecated_endpoints": {
                "/applications": {
                    "replacement": "/v2/farmer/register",
                    "deprecation_date": "2026-04-01"
                }
            }
        }
        
        result = api_integration.adapt_to_api_change(
            api_name="PM-KISAN",
            new_version="v2",
            change_log=change_log
        )
        
        assert result["status"] == "adapted"
        assert result["apiName"] == "PM-KISAN"
        assert result["newVersion"] == "v2"
    
    def test_circuit_breaker_pattern(self):
        """Test circuit breaker for API failures"""
        # Requirement 8.1: Include circuit breaker pattern
        api_integration = GovernmentAPIIntegration()
        
        # Check circuit breaker state
        health = api_integration.health_check()
        
        assert "pmKisan" in health
        assert health["pmKisan"]["circuitState"] == "closed"
    
    def test_fallback_mechanism(self):
        """Test fallback mechanism for API failures"""
        # Requirement 8.4: Provide fallback mechanisms
        api_integration = GovernmentAPIIntegration()
        
        # Simulate API failure by using invalid data
        # The circuit breaker should provide fallback
        result = api_integration.submit_application(
            scheme_id="UNKNOWN-SCHEME",
            application_data={}
        )
        
        # Should still return a result (either success or fallback)
        assert "success" in result or "fallbackMethod" in result


class TestComplianceAndAudit:
    """Test compliance and audit features"""
    
    def test_audit_trail_maintenance(self):
        """Test audit trail maintenance"""
        # Requirement 8.3: Maintain audit trails for all transactions
        audit_logger = get_audit_logger()
        compliance_service = get_compliance_service()
        
        # Log some events
        audit_logger.log_event(
            event_type=AuditEventType.APPLICATION_SUBMITTED,
            action="Application submitted to PM-KISAN",
            user_id="user123",
            username="testuser",
            resource_type="application",
            resource_id="app123",
            details={"scheme": "PM-KISAN"}
        )
        
        # Maintain audit trail
        result = compliance_service.maintain_audit_trail()
        
        assert "logs_retained" in result
        assert "logs_archived" in result
    
    def test_data_privacy_compliance(self):
        """Test data privacy regulation compliance"""
        # Requirement 8.2: Comply with data privacy regulations
        gdpr_service = get_gdpr_service()
        
        # Create data access request
        request = gdpr_service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ACCESS,
            requested_by="user123"
        )
        
        assert request.request_type == DataRequestType.ACCESS
        assert request.status.value == "pending"
        
        # Process request
        user_data = {
            "profile": {"name": "Test User", "age": 30},
            "applications": []
        }
        
        result = gdpr_service.process_access_request(
            request_id=request.request_id,
            user_data=user_data
        )
        
        assert result["user_id"] == "user123"
        assert "data" in result
    
    def test_transparent_reporting(self):
        """Test transparent reporting capabilities"""
        # Requirement 8.2: Add transparent reporting capabilities
        compliance_service = get_compliance_service()
        
        # Generate API usage report
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        report = compliance_service.generate_api_usage_report(
            start_date=start_date,
            end_date=end_date
        )
        
        assert report["report_type"] == "api_usage"
        assert "summary" in report
        assert "endpoint_statistics" in report
    
    def test_gdpr_compliance_report(self):
        """Test GDPR compliance reporting"""
        # Requirement 8.2: Data privacy regulation compliance
        compliance_service = get_compliance_service()
        
        report = compliance_service.generate_gdpr_compliance_report()
        
        assert report["report_type"] == "gdpr_compliance"
        assert "summary" in report
        assert "request_breakdown" in report
    
    def test_security_incidents_report(self):
        """Test security incidents reporting"""
        # Requirement 8.3: Audit trails and security monitoring
        compliance_service = get_compliance_service()
        audit_logger = get_audit_logger()
        
        # Log security event
        audit_logger.log_suspicious_activity(
            description="Multiple failed login attempts",
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1"
        )
        
        # Generate report
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow()
        
        report = compliance_service.generate_security_incidents_report(
            start_date=start_date,
            end_date=end_date
        )
        
        assert report["report_type"] == "security_incidents"
        assert "summary" in report
        assert "incident_categories" in report
    
    def test_compliance_violation_tracking(self):
        """Test compliance violation tracking"""
        # Requirement 8.2: Compliance monitoring
        compliance_service = get_compliance_service()
        
        # Record violation
        violation = compliance_service.record_compliance_violation(
            standard=ComplianceStandard.GDPR,
            severity="high",
            description="GDPR request overdue"
        )
        
        assert violation.standard == ComplianceStandard.GDPR
        assert violation.severity == "high"
        assert violation.resolved_at is None
        
        # Resolve violation
        resolved = compliance_service.resolve_compliance_violation(
            violation_id=violation.violation_id,
            resolution_notes="Request processed and completed"
        )
        
        assert resolved is not None
        assert resolved.resolved_at is not None
    
    def test_api_change_adaptation_tracking(self):
        """Test API change adaptation tracking"""
        # Requirement 8.4: Adapt to API changes within 48 hours
        compliance_service = get_compliance_service()
        
        # Track compliant adaptation (< 48 hours)
        result = compliance_service.track_api_change_adaptation(
            api_name="PM-KISAN",
            old_version="v1",
            new_version="v2",
            adaptation_time_hours=24
        )
        
        assert result["compliant"] is True
        assert result["adaptation_time_hours"] == 24
        
        # Track non-compliant adaptation (> 48 hours)
        result = compliance_service.track_api_change_adaptation(
            api_name="DBT",
            old_version="v1",
            new_version="v2",
            adaptation_time_hours=72
        )
        
        assert result["compliant"] is False
        assert result["adaptation_time_hours"] == 72
    
    def test_audit_trail_for_resource(self):
        """Test audit trail generation for specific resource"""
        # Requirement 8.3: Audit trails for all transactions
        audit_logger = get_audit_logger()
        compliance_service = get_compliance_service()
        
        # Log events for a resource
        audit_logger.log_event(
            event_type=AuditEventType.APPLICATION_CREATED,
            action="Application created",
            user_id="user123",
            username="testuser",
            resource_type="application",
            resource_id="app123"
        )
        
        audit_logger.log_event(
            event_type=AuditEventType.APPLICATION_SUBMITTED,
            action="Application submitted",
            user_id="user123",
            username="testuser",
            resource_type="application",
            resource_id="app123"
        )
        
        # Generate audit trail report
        report = compliance_service.generate_audit_trail_report(
            resource_type="application",
            resource_id="app123"
        )
        
        assert report["report_type"] == "audit_trail"
        assert report["resource"]["id"] == "app123"
        assert len(report["timeline"]) >= 2
    
    def test_data_access_report(self):
        """Test data access reporting"""
        # Requirement 8.2: Transparent reporting
        audit_logger = get_audit_logger()
        compliance_service = get_compliance_service()
        
        # Log data access events
        audit_logger.log_profile_access(
            action="viewed",
            profile_id="profile123",
            user_id="user123",
            username="testuser"
        )
        
        # Generate report
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow()
        
        report = compliance_service.generate_data_access_report(
            start_date=start_date,
            end_date=end_date
        )
        
        assert report["report_type"] == "data_access"
        assert "summary" in report
        assert "user_access_statistics" in report


class TestEndToEndCompliance:
    """End-to-end compliance tests"""
    
    def test_complete_application_with_audit(self):
        """Test complete application flow with audit trail"""
        # Requirement 8.1, 8.3: API integration with audit trails
        api_integration = GovernmentAPIIntegration()
        audit_logger = get_audit_logger()
        
        # Submit application
        application_data = {
            "aadhaar_number": "123456789012",
            "name": "Test Farmer",
            "bank_account": "1234567890",
            "bank_ifsc": "SBIN0001234",
            "land_ownership": 2.5
        }
        
        result = api_integration.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Log the submission
        audit_logger.log_event(
            event_type=AuditEventType.APPLICATION_SUBMITTED,
            action="Application submitted to PM-KISAN",
            user_id="user123",
            username="testuser",
            resource_type="application",
            resource_id=result.get("referenceNumber"),
            details={"scheme": "PM-KISAN"},
            success=result.get("success", False)
        )
        
        # Verify audit trail exists
        audit_trail = audit_logger.get_resource_audit_trail(
            resource_type="application",
            resource_id=result.get("referenceNumber")
        )
        
        assert len(audit_trail) > 0
        assert audit_trail[0].event_type == AuditEventType.APPLICATION_SUBMITTED
    
    def test_gdpr_request_with_compliance_check(self):
        """Test GDPR request with compliance checking"""
        # Requirement 8.2: Data privacy compliance
        gdpr_service = get_gdpr_service()
        compliance_service = get_compliance_service()
        
        # Create erasure request
        request = gdpr_service.create_data_request(
            user_id="user123",
            request_type=DataRequestType.ERASURE,
            requested_by="user123"
        )
        
        # Check GDPR compliance
        compliance_check = compliance_service.check_compliance(
            standard=ComplianceStandard.GDPR
        )
        
        assert "compliant" in compliance_check
        assert "violations" in compliance_check
