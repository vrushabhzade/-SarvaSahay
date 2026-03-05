"""
Unit tests for Auto-Application Service
Tests form template management, auto-population, validation, and API integration
"""

import pytest
from datetime import datetime
from services.auto_application_service import AutoApplicationService
from services.form_template_manager import FormTemplateManager, FormField, FormTemplate, FieldType
from services.government_api_client import GovernmentAPIIntegration


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing"""
    return {
        "demographics": {
            "name": "Test Farmer",
            "age": 35,
            "gender": "male"
        },
        "economic": {
            "annualIncome": 150000,
            "landOwnership": 2.5,
            "employmentStatus": "farmer"
        },
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "village": "Test Village",
            "block": "Test Block"
        },
        "documents": {
            "aadhaar": "123456789012",
            "bankAccount": "1234567890",
            "bankIfsc": "SBIN0001234"
        }
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "documents": {
            "aadhaar": "123456789012",
            "bankAccount": "1234567890",
            "bankIfsc": "SBIN0001234"
        },
        "documentIds": ["doc-001", "doc-002"]
    }


@pytest.fixture
def auto_app_service():
    """Auto-application service instance"""
    return AutoApplicationService()


class TestFormTemplateManager:
    """Test form template management"""
    
    def test_get_pm_kisan_template(self):
        """Test retrieving PM-KISAN template"""
        manager = FormTemplateManager()
        template = manager.get_template("PM-KISAN")
        
        assert template is not None
        assert template.scheme_id == "PM-KISAN"
        assert template.scheme_name == "Pradhan Mantri Kisan Samman Nidhi"
        assert len(template.fields) > 0
    
    def test_auto_populate_form(self, sample_user_profile, sample_document_data):
        """Test auto-population of form fields"""
        manager = FormTemplateManager()
        
        populated = manager.auto_populate_form(
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        assert populated["schemeId"] == "PM-KISAN"
        assert "formData" in populated
        assert populated["formData"]["age"] == 35
        assert populated["formData"]["gender"] == "male"
        assert populated["formData"]["aadhaar_number"] == "123456789012"
    
    def test_validate_form_success(self, sample_user_profile, sample_document_data):
        """Test form validation with valid data"""
        manager = FormTemplateManager()
        
        populated = manager.auto_populate_form(
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        validation = manager.validate_form(
            scheme_id="PM-KISAN",
            form_data=populated["formData"]
        )
        
        assert validation["isValid"] is True
        assert len(validation["errors"]) == 0
    
    def test_validate_form_missing_required(self):
        """Test form validation with missing required fields"""
        manager = FormTemplateManager()
        
        incomplete_data = {
            "age": 35
            # Missing other required fields
        }
        
        validation = manager.validate_form(
            scheme_id="PM-KISAN",
            form_data=incomplete_data
        )
        
        assert validation["isValid"] is False
        assert len(validation["errors"]) > 0
    
    def test_generate_preview(self, sample_user_profile, sample_document_data):
        """Test form preview generation"""
        manager = FormTemplateManager()
        
        populated = manager.auto_populate_form(
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        preview = manager.generate_preview(
            scheme_id="PM-KISAN",
            form_data=populated["formData"]
        )
        
        assert preview["schemeId"] == "PM-KISAN"
        assert "sections" in preview
        assert len(preview["sections"]) > 0


class TestAutoApplicationService:
    """Test auto-application service"""
    
    def test_create_application(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test application creation with auto-population"""
        result = auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        assert "applicationId" in result
        assert result["schemeId"] == "PM-KISAN"
        assert result["status"] == "draft"
        assert "formData" in result
    
    def test_validate_application(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test application validation"""
        result = auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        validation = auto_app_service.validate_application(result["applicationId"])
        
        assert validation["isValid"] is True
    
    def test_preview_application(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test application preview"""
        result = auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        preview = auto_app_service.preview_application(result["applicationId"])
        
        assert preview["applicationId"] == result["applicationId"]
        assert "sections" in preview
        assert preview["status"] == "draft"
    
    def test_update_application(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test application update"""
        result = auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        updated = auto_app_service.update_application(
            application_id=result["applicationId"],
            form_data={"land_ownership": 3.0}
        )
        
        assert updated["formData"]["land_ownership"] == 3.0
    
    def test_submit_application(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test application submission"""
        result = auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        submission = auto_app_service.submit_application(
            application_id=result["applicationId"],
            user_approval=True
        )
        
        # Check that submission was attempted (may succeed or provide fallback)
        assert "status" in submission
        assert submission["status"] in ["submitted", "submission_failed"]
        
        # If submitted successfully, should have government reference
        if submission["status"] == "submitted":
            assert "governmentRefNumber" in submission
        # If failed, should have fallback information
        elif submission["status"] == "submission_failed":
            assert "fallbackMethod" in submission or "error" in submission
    
    def test_get_application(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test retrieving application details"""
        result = auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        app = auto_app_service.get_application(result["applicationId"])
        
        assert app["applicationId"] == result["applicationId"]
        assert app["userId"] == "user-123"
        assert app["schemeId"] == "PM-KISAN"
    
    def test_list_user_applications(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test listing user applications"""
        # Create multiple applications
        auto_app_service.create_application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        apps = auto_app_service.list_user_applications("user-123")
        
        assert len(apps) >= 1
        assert all(app["userId"] == "user-123" for app in apps if "userId" in app)
    
    def test_bulk_create_applications(self, auto_app_service, sample_user_profile, sample_document_data):
        """Test bulk application creation"""
        scheme_ids = ["PM-KISAN"]
        
        results = auto_app_service.bulk_create_applications(
            user_id="user-123",
            scheme_ids=scheme_ids,
            user_profile=sample_user_profile,
            document_data=sample_document_data
        )
        
        assert len(results) == len(scheme_ids)
        assert results[0]["schemeId"] == "PM-KISAN"


class TestGovernmentAPIIntegration:
    """Test government API integration"""
    
    def test_pm_kisan_submit(self):
        """Test PM-KISAN application submission"""
        api = GovernmentAPIIntegration()
        
        result = api.submit_application(
            scheme_id="PM-KISAN",
            application_data={
                "aadhaar_number": "123456789012",
                "name": "Test Farmer",
                "bank_account": "1234567890",
                "bank_ifsc": "SBIN0001234",
                "land_ownership": 2.5
            }
        )
        
        assert result["success"] is True
        assert "referenceNumber" in result
    
    def test_check_application_status(self):
        """Test checking application status"""
        api = GovernmentAPIIntegration()
        
        status = api.check_application_status(
            scheme_id="PM-KISAN",
            reference_number="PMKISAN20240101123456"
        )
        
        assert "referenceNumber" in status
        assert "status" in status
    
    def test_health_check(self):
        """Test API health check"""
        api = GovernmentAPIIntegration()
        
        health = api.health_check()
        
        assert "pmKisan" in health
        assert "dbt" in health
        assert "pfms" in health


class TestCircuitBreakerAndRetry:
    """Test circuit breaker and retry logic"""
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures"""
        from services.government_api_client import CircuitBreaker, APIError
        
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        def failing_func():
            raise APIError("Service unavailable")
        
        # Trigger failures
        for _ in range(3):
            try:
                cb.call(failing_func)
            except APIError:
                pass
        
        # Circuit should be open now
        assert cb.state == "open"
    
    def test_retry_policy_retries(self):
        """Test that retry policy retries on transient errors"""
        from services.government_api_client import RetryPolicy, APITimeoutError
        
        retry = RetryPolicy(max_retries=2, initial_delay=0.1)
        
        call_count = 0
        
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APITimeoutError("Timeout")
            return "success"
        
        result = retry.execute(flaky_func)
        
        assert result == "success"
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
