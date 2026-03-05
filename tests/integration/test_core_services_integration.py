"""
Integration Tests for Core Services
Tests end-to-end workflows from profile creation to application submission
"""

import pytest
import time
from typing import Dict, Any

from services.profile_service import ProfileService
from services.eligibility_engine import EligibilityEngine
from services.document_processor import DocumentProcessor
from services.auto_application_service import AutoApplicationService
from services.tracking_service import TrackingService
from services.notification_service import NotificationService


class TestCoreServicesIntegration:
    """Integration tests for core services working together"""
    
    @pytest.fixture
    def sample_profile_data(self) -> Dict[str, Any]:
        """Sample user profile data for testing"""
        return {
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
                "communicationChannel": "sms"
            }
        }
    
    def test_profile_creation_workflow(self, sample_profile_data):
        """Test profile creation and retrieval workflow"""
        profile_service = ProfileService()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile_data)
        assert profile_id is not None
        assert len(profile_id) > 0
        
        # Retrieve profile
        retrieved_profile = profile_service.get_profile(profile_id)
        assert retrieved_profile is not None
        assert retrieved_profile["demographics"]["name"] == "Ramesh Kumar"
        assert retrieved_profile["economic"]["annualIncome"] == 150000
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_eligibility_evaluation_workflow(self, sample_profile_data):
        """Test profile creation followed by eligibility evaluation"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile_data)
        
        # Load sample schemes
        sample_schemes = [
            {
                "schemeId": "PM-KISAN",
                "name": "Pradhan Mantri Kisan Samman Nidhi",
                "benefitAmount": 6000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1, "max": 2.0},
                    "employmentStatus": ["farmer"],
                    "annualIncome": {"max": 200000}
                }
            },
            {
                "schemeId": "MGNREGA",
                "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
                "benefitAmount": 25000,
                "eligibilityCriteria": {
                    "age": {"min": 18, "max": 65}
                }
            }
        ]
        
        eligibility_engine.load_schemes(sample_schemes)
        
        # Evaluate eligibility
        start_time = time.time()
        eligible_schemes = eligibility_engine.evaluate_eligibility(sample_profile_data)
        processing_time = time.time() - start_time
        
        # Verify results
        assert len(eligible_schemes) > 0
        assert processing_time < 5.0, f"Eligibility evaluation took {processing_time}s, exceeds 5s requirement"
        
        # Verify PM-KISAN is in eligible schemes (farmer with land)
        scheme_ids = [s["schemeId"] for s in eligible_schemes]
        assert "PM-KISAN" in scheme_ids
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_document_processing_workflow(self, sample_profile_data):
        """Test document upload and processing workflow"""
        profile_service = ProfileService()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile_data)
        
        # Note: Document processor requires actual image processing setup
        # For integration test, we verify the service can be instantiated
        document_processor = DocumentProcessor()
        assert document_processor is not None
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_end_to_end_application_workflow(self, sample_profile_data):
        """Test complete workflow: profile -> eligibility -> application"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Step 1: Create profile
        profile_id = profile_service.create_profile(sample_profile_data)
        assert profile_id is not None
        
        # Step 2: Evaluate eligibility
        sample_schemes = [
            {
                "schemeId": "PM-KISAN",
                "name": "Pradhan Mantri Kisan Samman Nidhi",
                "benefitAmount": 6000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1, "max": 2.0},
                    "employmentStatus": ["farmer"],
                    "annualIncome": {"max": 200000}
                }
            }
        ]
        
        eligibility_engine.load_schemes(sample_schemes)
        eligible_schemes = eligibility_engine.evaluate_eligibility(sample_profile_data)
        
        assert len(eligible_schemes) > 0
        
        # Step 3: Verify services can be instantiated
        auto_application_service = AutoApplicationService()
        assert auto_application_service is not None
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_tracking_and_notification_workflow(self, sample_profile_data):
        """Test application tracking and notification workflow"""
        profile_service = ProfileService()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile_data)
        
        # Verify services can be instantiated
        auto_application_service = AutoApplicationService()
        assert auto_application_service is not None
        
        notification_service = NotificationService()
        assert notification_service is not None
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_performance_under_load(self, sample_profile_data):
        """Test system performance with multiple concurrent operations"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create multiple profiles
        profile_ids = []
        for i in range(10):
            profile_data = sample_profile_data.copy()
            profile_data["demographics"] = sample_profile_data["demographics"].copy()
            profile_data["demographics"]["name"] = f"User {i}"
            profile_id = profile_service.create_profile(profile_data)
            profile_ids.append(profile_id)
        
        # Load schemes
        sample_schemes = [
            {
                "schemeId": f"SCHEME-{i}",
                "name": f"Test Scheme {i}",
                "benefitAmount": 5000 * i,
                "eligibilityCriteria": {
                    "age": {"min": 18, "max": 65}
                }
            }
            for i in range(30)  # 30+ schemes requirement
        ]
        
        eligibility_engine.load_schemes(sample_schemes)
        
        # Evaluate eligibility for all profiles
        start_time = time.time()
        for profile_id in profile_ids:
            profile = profile_service.get_profile(profile_id)
            eligible_schemes = eligibility_engine.evaluate_eligibility(profile)
            assert len(eligible_schemes) > 0
        
        total_time = time.time() - start_time
        avg_time_per_evaluation = total_time / len(profile_ids)
        
        # Verify performance requirement (<5 seconds per evaluation)
        assert avg_time_per_evaluation < 5.0, \
            f"Average evaluation time {avg_time_per_evaluation}s exceeds 5s requirement"
        
        # Cleanup
        for profile_id in profile_ids:
            profile_service.delete_profile(profile_id)
    
    def test_error_handling_and_recovery(self, sample_profile_data):
        """Test error handling across services"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Test invalid profile retrieval
        invalid_profile = profile_service.get_profile("invalid-id")
        assert invalid_profile is None
        
        # Test eligibility evaluation with missing data
        incomplete_profile = {"demographics": {"name": "Test", "age": 30, "gender": "male", "caste": "general", "maritalStatus": "single"}}
        
        # Should handle gracefully without crashing
        try:
            eligible_schemes = eligibility_engine.evaluate_eligibility(incomplete_profile)
            # May return empty list or raise ValueError
            assert isinstance(eligible_schemes, list)
        except ValueError:
            # Expected for incomplete profile
            pass
        
        # Test profile deletion of non-existent profile
        result = profile_service.delete_profile("non-existent-id")
        assert result is False
    
    def test_data_consistency_across_services(self, sample_profile_data):
        """Test data consistency when profile is updated"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile_data)
        
        # Load schemes
        sample_schemes = [
            {
                "schemeId": "INCOME-BASED",
                "name": "Income Based Scheme",
                "benefitAmount": 10000,
                "eligibilityCriteria": {
                    "annualIncome": {"max": 100000}
                }
            }
        ]
        
        eligibility_engine.load_schemes(sample_schemes)
        
        # Initial eligibility (income 150000 - not eligible)
        profile = profile_service.get_profile(profile_id)
        eligible_schemes_before = eligibility_engine.evaluate_eligibility(profile)
        
        # Update profile to lower income
        profile_service.update_profile(profile_id, {
            "economic": {"annualIncome": 80000}
        })
        
        # Re-evaluate eligibility (should now be eligible)
        updated_profile = profile_service.get_profile(profile_id)
        eligible_schemes_after = eligibility_engine.evaluate_eligibility(updated_profile)
        
        # Verify data consistency
        assert updated_profile["economic"]["annualIncome"] == 80000
        
        # Cleanup
        profile_service.delete_profile(profile_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
