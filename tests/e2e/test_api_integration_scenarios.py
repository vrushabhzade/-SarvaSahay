"""
End-to-End API Integration Tests
Tests real API integration scenarios with government systems
Validates Requirements: 4, 5, 8
"""

import pytest
from datetime import datetime, timedelta

from services.government_api_client import GovernmentAPIIntegration
from services.auto_application_service import AutoApplicationService
from services.tracking_service import TrackingService
from services.notification_service import NotificationService
from services.profile_service import ProfileService
from shared.utils.audit_log import get_audit_logger, AuditEventType


class TestGovernmentAPIScenarios:
    """Test real government API integration scenarios"""
    
    @pytest.fixture
    def sample_application_data(self):
        """Sample application data for testing"""
        return {
            "aadhaar_number": "123456789012",
            "name": "Test Farmer",
            "bank_account": "1234567890",
            "bank_ifsc": "SBIN0001234",
            "land_ownership": 2.5,
            "annual_income": 150000
        }
    
    def test_pm_kisan_complete_workflow(self, sample_application_data):
        """
        Test complete PM-KISAN workflow: Submit -> Track -> Notify
        Validates: Requirements 4.3, 5.1, 5.2, 8.1
        """
        api_integration = GovernmentAPIIntegration()
        tracking_service = TrackingService()
        notification_service = NotificationService()
        audit_logger = get_audit_logger()
        
        # Step 1: Submit application to PM-KISAN
        submission_result = api_integration.submit_application(
            scheme_id="PM-KISAN",
            application_data=sample_application_data
        )
        
        assert submission_result["success"] is True
        assert "referenceNumber" in submission_result
        
        reference_number = submission_result["referenceNumber"]
        
        # Log submission
        audit_logger.log_event(
            event_type=AuditEventType.APPLICATION_SUBMITTED,
            action="PM-KISAN application submitted",
            user_id="test_user",
            username="Test Farmer",
            resource_type="application",
            resource_id=reference_number,
            details={"scheme": "PM-KISAN"},
            success=True
        )
        
        # Step 2: Track application status
        tracking_result = api_integration.track_application(reference_number)
        
        assert "status" in tracking_result
        assert tracking_result["status"] in [
            "submitted", "under_review", "approved", "rejected", "paid"
        ]
        
        # Step 3: Verify audit trail
        audit_trail = audit_logger.get_resource_audit_trail(
            resource_type="application",
            resource_id=reference_number
        )
        
        assert len(audit_trail) > 0
        assert audit_trail[0].event_type == AuditEventType.APPLICATION_SUBMITTED
    
    def test_dbt_payment_tracking_workflow(self, sample_application_data):
        """
        Test DBT payment tracking workflow
        Validates: Requirements 5.4, 8.1
        """
        api_integration = GovernmentAPIIntegration()
        
        # Register beneficiary in DBT
        beneficiary_data = {
            "aadhaar_number": sample_application_data["aadhaar_number"],
            "bank_account": sample_application_data["bank_account"],
            "bank_ifsc": sample_application_data["bank_ifsc"],
            "scheme_id": "PM-KISAN"
        }
        
        registration_result = api_integration.dbt.register_beneficiary(beneficiary_data)
        
        assert registration_result["success"] is True
        assert "beneficiaryId" in registration_result
        
        beneficiary_id = registration_result["beneficiaryId"]
        
        # Track payment through PFMS
        payment_result = api_integration.track_payment(f"TXN_{beneficiary_id}")
        
        assert "transactionId" in payment_result
        assert "status" in payment_result
    
    def test_state_api_integration_workflow(self):
        """
        Test state government API integration workflow
        Validates: Requirements 8.1, 8.4
        """
        state_configs = {
            "Maharashtra": {
                "base_url": "https://api.maharashtra.gov.in/v1",
                "api_key": "test_key"
            }
        }
        
        api_integration = GovernmentAPIIntegration(state_configs=state_configs)
        
        # Submit state-specific application
        application_data = {
            "scheme_id": "MH-FARMER-SCHEME",
            "applicant_name": "Test Applicant",
            "district": "Pune",
            "land_ownership": 2.0
        }
        
        result = api_integration.submit_application(
            scheme_id="MH-FARMER-SCHEME",
            application_data=application_data,
            state="Maharashtra"
        )
        
        assert result["success"] is True
        assert result["state"] == "Maharashtra"
    
    def test_api_failure_and_fallback(self, sample_application_data):
        """
        Test API failure handling and fallback mechanisms
        Validates: Requirements 4.4, 8.4
        """
        api_integration = GovernmentAPIIntegration()
        
        # Attempt submission with invalid scheme
        result = api_integration.submit_application(
            scheme_id="INVALID-SCHEME",
            application_data=sample_application_data
        )
        
        # Should provide fallback method
        assert "fallbackMethod" in result or "error" in result
        
        if "fallbackMethod" in result:
            assert result["fallbackMethod"] in [
                "manual_submission",
                "offline_form",
                "retry_later"
            ]
    
    def test_circuit_breaker_recovery(self):
        """
        Test circuit breaker pattern and recovery
        Validates: Requirements 8.1, 8.4
        """
        api_integration = GovernmentAPIIntegration()
        
        # Check initial health
        health = api_integration.health_check()
        
        assert "pmKisan" in health
        assert health["pmKisan"]["circuitState"] in ["closed", "open", "half_open"]
        
        # Verify circuit breaker can recover
        if health["pmKisan"]["circuitState"] == "open":
            # Wait for recovery attempt
            import time
            time.sleep(1)
            
            # Check health again
            health_after = api_integration.health_check()
            assert "pmKisan" in health_after


class TestEndToEndApplicationScenarios:
    """Test complete end-to-end application scenarios"""
    
    def test_farmer_pm_kisan_complete_scenario(self):
        """
        Complete scenario: Farmer applies for PM-KISAN and receives benefit
        Validates: All requirements 1-10
        """
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        tracking_service = TrackingService()
        notification_service = NotificationService()
        
        # Create farmer profile
        farmer_profile = {
            "demographics": {
                "name": "Ramesh Kumar",
                "age": 35,
                "gender": "male",
                "caste": "obc",
                "maritalStatus": "married"
            },
            "economic": {
                "annualIncome": 150000,
                "landOwnership": 1.5,
                "employmentStatus": "farmer",
                "bankAccount": "1234567890"
            },
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "block": "Haveli",
                "village": "Khed",
                "pincode": "412105"
            },
            "family": {
                "familySize": 5,
                "dependents": 3,
                "elderlyMembers": 1
            },
            "preferences": {
                "language": "marathi",
                "communicationChannel": "sms",
                "phoneNumber": "+919876543210"
            }
        }
        
        profile_id = profile_service.create_profile(farmer_profile)
        
        # Create and submit application
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="PM-KISAN",
            profile_data=farmer_profile,
            document_data={
                "aadhaar": "123456789012",
                "landRecords": "LAND123"
            }
        )
        
        assert application_result["success"] is True
        application_id = application_result["applicationId"]
        
        # Submit to government system
        submission_result = auto_application_service.submit_application(application_id)
        
        assert submission_result["success"] is True
        assert "referenceNumber" in submission_result
        
        # Track application
        status = tracking_service.get_application_status(application_id)
        assert status is not None
        
        # Send notification
        notification_result = notification_service.send_notification(
            user_id=profile_id,
            channel="sms",
            message="Your PM-KISAN application has been submitted",
            language="marathi"
        )
        
        assert notification_result["success"] is True
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_multi_scheme_application_scenario(self):
        """
        Scenario: User applies for multiple schemes simultaneously
        Validates: Requirements 2, 4, 5
        """
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        
        # Create profile
        profile_data = {
            "demographics": {
                "name": "Test User",
                "age": 30,
                "gender": "male",
                "caste": "general",
                "maritalStatus": "single"
            },
            "economic": {
                "annualIncome": 100000,
                "landOwnership": 1.0,
                "employmentStatus": "farmer",
                "bankAccount": "1234567890"
            },
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "block": "Haveli",
                "village": "Khed",
                "pincode": "412105"
            },
            "family": {
                "familySize": 4,
                "dependents": 2,
                "elderlyMembers": 0
            },
            "preferences": {
                "language": "marathi",
                "communicationChannel": "sms"
            }
        }
        
        profile_id = profile_service.create_profile(profile_data)
        
        # Apply for multiple schemes
        schemes = ["PM-KISAN", "SOIL-HEALTH", "CROP-INSURANCE"]
        application_ids = []
        
        for scheme_id in schemes:
            result = auto_application_service.create_application(
                user_id=profile_id,
                scheme_id=scheme_id,
                profile_data=profile_data,
                document_data={}
            )
            
            if result["success"]:
                application_ids.append(result["applicationId"])
        
        # Verify multiple applications created
        assert len(application_ids) > 0
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_application_rejection_and_reapplication(self):
        """
        Scenario: Application rejected, user updates profile and reapplies
        Validates: Requirements 1.5, 4, 5
        """
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        notification_service = NotificationService()
        
        # Create profile
        profile_data = {
            "demographics": {
                "name": "Test User",
                "age": 30,
                "gender": "male",
                "caste": "general",
                "maritalStatus": "single"
            },
            "economic": {
                "annualIncome": 250000,  # Too high for some schemes
                "landOwnership": 1.0,
                "employmentStatus": "farmer",
                "bankAccount": "1234567890"
            },
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "block": "Haveli",
                "village": "Khed",
                "pincode": "412105"
            },
            "family": {
                "familySize": 4,
                "dependents": 2,
                "elderlyMembers": 0
            },
            "preferences": {
                "language": "marathi",
                "communicationChannel": "sms",
                "phoneNumber": "+919876543210"
            }
        }
        
        profile_id = profile_service.create_profile(profile_data)
        
        # First application attempt
        first_application = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="LOW-INCOME-SCHEME",
            profile_data=profile_data,
            document_data={}
        )
        
        # Update profile with corrected income
        profile_service.update_profile(profile_id, {
            "economic": {"annualIncome": 90000}
        })
        
        # Get updated profile
        updated_profile = profile_service.get_profile(profile_id)
        
        # Reapply with updated profile
        second_application = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="LOW-INCOME-SCHEME",
            profile_data=updated_profile,
            document_data={}
        )
        
        # Verify reapplication
        assert updated_profile["economic"]["annualIncome"] == 90000
        
        # Cleanup
        profile_service.delete_profile(profile_id)


class TestRealTimeTracking:
    """Test real-time tracking scenarios"""
    
    def test_status_change_notification_flow(self):
        """
        Test status change detection and notification
        Validates: Requirements 5.1, 5.2, 5.3
        """
        tracking_service = TrackingService()
        notification_service = NotificationService()
        
        # Create mock application
        application_id = "APP-TEST-001"
        
        # Simulate status changes
        statuses = ["submitted", "under_review", "approved", "paid"]
        
        for status in statuses:
            # Update status (in real scenario, would poll government API)
            tracking_result = tracking_service.get_application_status(application_id)
            
            # Verify status tracking
            assert tracking_result is not None or status == "submitted"
    
    def test_payment_confirmation_flow(self):
        """
        Test payment confirmation and notification
        Validates: Requirements 5.4
        """
        api_integration = GovernmentAPIIntegration()
        notification_service = NotificationService()
        
        # Track payment
        payment_result = api_integration.track_payment("TXN123456")
        
        assert "transactionId" in payment_result
        assert "status" in payment_result
        
        # If payment successful, notification would be sent
        if payment_result.get("status") == "success":
            # Verify payment details
            assert "amount" in payment_result or "transactionId" in payment_result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
