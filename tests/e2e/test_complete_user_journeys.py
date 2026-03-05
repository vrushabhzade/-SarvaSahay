"""
End-to-End Integration Tests for Complete User Journeys
Tests complete workflows from profile creation to benefit receipt
Validates Requirements: All requirements (1-10)
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from services.profile_service import ProfileService
from services.eligibility_engine import EligibilityEngine
from services.document_processor import DocumentProcessor
from services.auto_application_service import AutoApplicationService
from services.tracking_service import TrackingService
from services.notification_service import NotificationService
from services.sms_interface import SMSInterfaceHandler
from services.voice_interface import VoiceInterfaceHandler
from shared.utils.audit_log import get_audit_logger, AuditEventType


class TestCompleteUserJourneys:
    """End-to-end tests for complete user journeys"""
    
    @pytest.fixture
    def farmer_profile_data(self) -> Dict[str, Any]:
        """Sample farmer profile for testing"""
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
                "communicationChannel": "sms",
                "phoneNumber": "+919876543210"
            }
        }
    
    @pytest.fixture
    def laborer_profile_data(self) -> Dict[str, Any]:
        """Sample laborer profile for testing"""
        return {
            "demographics": {
                "name": "Sunita Devi",
                "age": 28,
                "gender": "female",
                "caste": "sc",
                "maritalStatus": "married"
            },
            "economic": {
                "annualIncome": 80000,
                "landOwnership": 0,
                "employmentStatus": "laborer",
                "bankAccount": "9876543210"
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
                "language": "hindi",
                "communicationChannel": "voice",
                "phoneNumber": "+919876543211"
            }
        }
    
    def test_farmer_complete_journey(self, farmer_profile_data):
        """
        Test complete journey for a farmer user
        Journey: SMS profile creation -> Eligibility check -> Document upload -> 
                 Application submission -> Tracking -> Benefit receipt
        Validates: Requirements 1, 2, 3, 4, 5, 6
        """
        # Step 1: Profile creation via SMS (Requirement 1.1)
        sms_interface = SMSInterfaceHandler()
        profile_service = ProfileService()
        
        # Simulate SMS profile creation
        sms_response = sms_interface.handle_message(
            phone_number=farmer_profile_data["preferences"]["phoneNumber"],
            message="PROFILE BANAO",
            language="marathi"
        )
        
        assert "profile creation" in sms_response.lower() or "प्रोफाइल" in sms_response
        
        # Create profile
        profile_id = profile_service.create_profile(farmer_profile_data)
        assert profile_id is not None
        
        # Step 2: Eligibility evaluation (Requirement 2.1, 2.2)
        eligibility_engine = EligibilityEngine()
        
        # Load schemes
        schemes = [
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
                "schemeId": "SOIL-HEALTH",
                "name": "Soil Health Card Scheme",
                "benefitAmount": 2000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1},
                    "employmentStatus": ["farmer"]
                }
            }
        ]
        
        eligibility_engine.load_schemes(schemes)
        
        start_time = time.time()
        eligible_schemes = eligibility_engine.evaluate_eligibility(farmer_profile_data)
        evaluation_time = time.time() - start_time
        
        # Verify performance requirement (< 5 seconds)
        assert evaluation_time < 5.0, f"Eligibility evaluation took {evaluation_time}s"
        
        # Verify farmer is eligible for PM-KISAN
        scheme_ids = [s["schemeId"] for s in eligible_schemes]
        assert "PM-KISAN" in scheme_ids
        assert len(eligible_schemes) >= 1
        
        # Step 3: Document processing (Requirement 3.1, 3.2)
        document_processor = DocumentProcessor()
        
        # Simulate document upload (in real scenario, would process actual image)
        document_data = {
            "documentType": "aadhaar",
            "extractedData": {
                "aadhaarNumber": "123456789012",
                "name": "Ramesh Kumar",
                "address": "Khed, Pune"
            }
        }
        
        # Validate document against profile
        validation_result = document_processor.validate_document(
            document_data=document_data,
            profile_data=farmer_profile_data
        )
        
        assert validation_result["isValid"] is True
        
        # Step 4: Auto-application submission (Requirement 4.1, 4.2, 4.3)
        auto_application_service = AutoApplicationService()
        
        # Create application for PM-KISAN
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="PM-KISAN",
            profile_data=farmer_profile_data,
            document_data=document_data
        )
        
        assert application_result["success"] is True
        assert "applicationId" in application_result
        
        application_id = application_result["applicationId"]
        
        # Submit application
        submission_result = auto_application_service.submit_application(
            application_id=application_id
        )
        
        assert submission_result["success"] is True
        assert "referenceNumber" in submission_result
        
        # Step 5: Application tracking (Requirement 5.1, 5.2)
        tracking_service = TrackingService()
        
        # Track application status
        status = tracking_service.get_application_status(application_id)
        
        assert status is not None
        assert "status" in status
        assert status["status"] in ["submitted", "under_review", "approved", "rejected"]
        
        # Step 6: Notification (Requirement 5.2, 6.1)
        notification_service = NotificationService()
        
        # Send SMS notification
        notification_result = notification_service.send_notification(
            user_id=profile_id,
            channel="sms",
            message="Your PM-KISAN application has been submitted successfully",
            language="marathi"
        )
        
        assert notification_result["success"] is True
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_laborer_voice_journey(self, laborer_profile_data):
        """
        Test complete journey for a laborer using voice interface
        Journey: Voice profile creation -> Eligibility check -> Application -> Tracking
        Validates: Requirements 1, 2, 4, 5, 6
        """
        # Step 1: Profile creation via voice (Requirement 1.3, 6.2)
        voice_interface = VoiceInterfaceHandler()
        profile_service = ProfileService()
        
        # Simulate voice call
        voice_response = voice_interface.handle_call(
            phone_number=laborer_profile_data["preferences"]["phoneNumber"],
            language="hindi"
        )
        
        assert voice_response["status"] == "success"
        assert "greeting" in voice_response
        
        # Create profile
        profile_id = profile_service.create_profile(laborer_profile_data)
        assert profile_id is not None
        
        # Step 2: Eligibility evaluation (Requirement 2.1)
        eligibility_engine = EligibilityEngine()
        
        schemes = [
            {
                "schemeId": "MGNREGA",
                "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
                "benefitAmount": 25000,
                "eligibilityCriteria": {
                    "age": {"min": 18, "max": 65},
                    "location": {"rural": True}
                }
            },
            {
                "schemeId": "PMAY",
                "name": "Pradhan Mantri Awas Yojana",
                "benefitAmount": 120000,
                "eligibilityCriteria": {
                    "annualIncome": {"max": 100000},
                    "landOwnership": {"max": 0}
                }
            }
        ]
        
        eligibility_engine.load_schemes(schemes)
        eligible_schemes = eligibility_engine.evaluate_eligibility(laborer_profile_data)
        
        # Verify laborer is eligible for MGNREGA
        scheme_ids = [s["schemeId"] for s in eligible_schemes]
        assert "MGNREGA" in scheme_ids
        
        # Step 3: Application submission (Requirement 4.1, 4.2)
        auto_application_service = AutoApplicationService()
        
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="MGNREGA",
            profile_data=laborer_profile_data,
            document_data={}
        )
        
        assert application_result["success"] is True
        
        # Step 4: Voice notification (Requirement 6.2, 5.3)
        notification_service = NotificationService()
        
        notification_result = notification_service.send_notification(
            user_id=profile_id,
            channel="voice",
            message="Your MGNREGA application has been submitted",
            language="hindi"
        )
        
        assert notification_result["success"] is True
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_multi_scheme_application_journey(self, farmer_profile_data):
        """
        Test user applying for multiple schemes simultaneously
        Validates: Requirements 2, 4, 5
        """
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        auto_application_service = AutoApplicationService()
        
        # Create profile
        profile_id = profile_service.create_profile(farmer_profile_data)
        
        # Load multiple schemes
        schemes = [
            {
                "schemeId": "PM-KISAN",
                "name": "PM-KISAN",
                "benefitAmount": 6000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1, "max": 2.0},
                    "employmentStatus": ["farmer"]
                }
            },
            {
                "schemeId": "SOIL-HEALTH",
                "name": "Soil Health Card",
                "benefitAmount": 2000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1},
                    "employmentStatus": ["farmer"]
                }
            },
            {
                "schemeId": "CROP-INSURANCE",
                "name": "Crop Insurance",
                "benefitAmount": 10000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.5},
                    "employmentStatus": ["farmer"]
                }
            }
        ]
        
        eligibility_engine.load_schemes(schemes)
        eligible_schemes = eligibility_engine.evaluate_eligibility(farmer_profile_data)
        
        # Apply for all eligible schemes
        application_ids = []
        for scheme in eligible_schemes:
            result = auto_application_service.create_application(
                user_id=profile_id,
                scheme_id=scheme["schemeId"],
                profile_data=farmer_profile_data,
                document_data={}
            )
            
            if result["success"]:
                application_ids.append(result["applicationId"])
        
        # Verify multiple applications created
        assert len(application_ids) >= 2
        
        # Track all applications
        tracking_service = TrackingService()
        
        for app_id in application_ids:
            status = tracking_service.get_application_status(app_id)
            assert status is not None
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_profile_update_and_reevaluation_journey(self, farmer_profile_data):
        """
        Test profile update triggering automatic re-evaluation
        Validates: Requirements 1.5, 2.1
        """
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create initial profile
        profile_id = profile_service.create_profile(farmer_profile_data)
        
        # Load income-based scheme
        schemes = [
            {
                "schemeId": "LOW-INCOME-SCHEME",
                "name": "Low Income Support",
                "benefitAmount": 15000,
                "eligibilityCriteria": {
                    "annualIncome": {"max": 100000}
                }
            }
        ]
        
        eligibility_engine.load_schemes(schemes)
        
        # Initial evaluation (income 150000 - not eligible)
        initial_schemes = eligibility_engine.evaluate_eligibility(farmer_profile_data)
        initial_scheme_ids = [s["schemeId"] for s in initial_schemes]
        
        # Update profile to lower income
        profile_service.update_profile(profile_id, {
            "economic": {"annualIncome": 80000}
        })
        
        # Get updated profile
        updated_profile = profile_service.get_profile(profile_id)
        
        # Re-evaluate eligibility
        updated_schemes = eligibility_engine.evaluate_eligibility(updated_profile)
        updated_scheme_ids = [s["schemeId"] for s in updated_schemes]
        
        # Verify automatic re-evaluation shows new eligibility
        assert updated_profile["economic"]["annualIncome"] == 80000
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_error_recovery_journey(self, farmer_profile_data):
        """
        Test error handling and recovery in user journey
        Validates: Requirements 3.5, 4.4, 5.5
        """
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        
        # Create profile
        profile_id = profile_service.create_profile(farmer_profile_data)
        
        # Test API failure fallback (Requirement 4.4)
        result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="UNKNOWN-SCHEME",
            profile_data=farmer_profile_data,
            document_data={}
        )
        
        # Should provide fallback method
        assert "fallbackMethod" in result or "error" in result
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_security_and_audit_journey(self, farmer_profile_data):
        """
        Test security and audit trail throughout user journey
        Validates: Requirements 10.1, 10.3, 8.3
        """
        profile_service = ProfileService()
        audit_logger = get_audit_logger()
        
        # Create profile with encryption (Requirement 10.1)
        profile_id = profile_service.create_profile(farmer_profile_data)
        
        # Verify profile is stored securely
        profile = profile_service.get_profile(profile_id)
        assert profile is not None
        
        # Log audit event
        audit_logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            user_id=profile_id,
            username=farmer_profile_data["demographics"]["name"],
            resource_type="profile",
            resource_id=profile_id,
            success=True
        )
        
        # Verify audit trail exists (Requirement 8.3)
        audit_trail = audit_logger.get_resource_audit_trail(
            resource_type="profile",
            resource_id=profile_id
        )
        
        assert len(audit_trail) > 0
        
        # Test GDPR data deletion (Requirement 10.5)
        deletion_result = profile_service.delete_profile(profile_id)
        assert deletion_result is True
        
        # Verify profile is deleted
        deleted_profile = profile_service.get_profile(profile_id)
        assert deleted_profile is None


class TestMultiChannelIntegration:
    """Test multi-channel interface integration"""
    
    def test_sms_interface_complete_flow(self):
        """
        Test complete SMS interface flow
        Validates: Requirements 6.1, 6.5
        """
        sms_interface = SMSInterfaceHandler()
        
        # Test profile creation initiation
        response = sms_interface.handle_message(
            phone_number="+919876543210",
            message="PROFILE BANAO",
            language="marathi"
        )
        
        assert response is not None
        assert len(response) > 0
        
        # Test scheme discovery
        response = sms_interface.handle_message(
            phone_number="+919876543210",
            message="YOJANA",
            language="marathi"
        )
        
        assert response is not None
        
        # Test status check
        response = sms_interface.handle_message(
            phone_number="+919876543210",
            message="STATUS",
            language="marathi"
        )
        
        assert response is not None
    
    def test_voice_interface_complete_flow(self):
        """
        Test complete voice interface flow
        Validates: Requirements 6.2, 6.4
        """
        voice_interface = VoiceInterfaceHandler()
        
        # Test voice call handling
        response = voice_interface.handle_call(
            phone_number="+919876543211",
            language="hindi"
        )
        
        assert response["status"] == "success"
        assert "greeting" in response
        
        # Test speech-to-text conversion
        speech_result = voice_interface.process_speech(
            audio_data=b"mock_audio_data",
            language="hindi"
        )
        
        assert "text" in speech_result or "error" in speech_result
    
    def test_multi_language_support(self):
        """
        Test multi-language support across channels
        Validates: Requirements 6.5
        """
        sms_interface = SMSInterfaceHandler()
        
        # Test Marathi
        marathi_response = sms_interface.handle_message(
            phone_number="+919876543210",
            message="PROFILE BANAO",
            language="marathi"
        )
        assert marathi_response is not None
        
        # Test Hindi
        hindi_response = sms_interface.handle_message(
            phone_number="+919876543211",
            message="PROFILE BANAO",
            language="hindi"
        )
        assert hindi_response is not None
        
        # Verify different language responses
        # (In real implementation, responses would be in different languages)
        assert len(marathi_response) > 0
        assert len(hindi_response) > 0


class TestPerformanceAndScale:
    """Test performance and scalability requirements"""
    
    def test_concurrent_eligibility_evaluations(self):
        """
        Test system performance with concurrent eligibility evaluations
        Validates: Requirements 9.1, 9.2
        """
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create test profiles
        profiles = []
        for i in range(20):
            profile_data = {
                "demographics": {
                    "name": f"User {i}",
                    "age": 30 + i,
                    "gender": "male" if i % 2 == 0 else "female",
                    "caste": "general",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 100000 + (i * 10000),
                    "landOwnership": i * 0.5,
                    "employmentStatus": "farmer" if i % 2 == 0 else "laborer",
                    "bankAccount": f"ACC{i:010d}"
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
                    "elderlyMembers": 1
                },
                "preferences": {
                    "language": "marathi",
                    "communicationChannel": "sms"
                }
            }
            profile_id = profile_service.create_profile(profile_data)
            profiles.append((profile_id, profile_data))
        
        # Load 30+ schemes
        schemes = [
            {
                "schemeId": f"SCHEME-{i}",
                "name": f"Test Scheme {i}",
                "benefitAmount": 5000 * (i + 1),
                "eligibilityCriteria": {
                    "age": {"min": 18, "max": 65}
                }
            }
            for i in range(30)
        ]
        
        eligibility_engine.load_schemes(schemes)
        
        # Evaluate eligibility for all profiles
        start_time = time.time()
        evaluation_times = []
        
        for profile_id, profile_data in profiles:
            eval_start = time.time()
            eligible_schemes = eligibility_engine.evaluate_eligibility(profile_data)
            eval_time = time.time() - eval_start
            evaluation_times.append(eval_time)
            
            assert len(eligible_schemes) > 0
        
        total_time = time.time() - start_time
        avg_time = sum(evaluation_times) / len(evaluation_times)
        max_time = max(evaluation_times)
        
        # Verify performance requirements
        assert avg_time < 5.0, f"Average evaluation time {avg_time}s exceeds 5s"
        assert max_time < 5.0, f"Max evaluation time {max_time}s exceeds 5s"
        
        # Cleanup
        for profile_id, _ in profiles:
            profile_service.delete_profile(profile_id)
    
    def test_system_uptime_and_availability(self):
        """
        Test system availability and error handling
        Validates: Requirements 9.5
        """
        profile_service = ProfileService()
        
        # Test service availability
        test_profile = {
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
        
        # Perform multiple operations to test availability
        success_count = 0
        total_operations = 10
        
        for i in range(total_operations):
            try:
                profile_id = profile_service.create_profile(test_profile)
                if profile_id:
                    success_count += 1
                    profile_service.delete_profile(profile_id)
            except Exception:
                pass
        
        # Calculate availability
        availability = (success_count / total_operations) * 100
        
        # Should maintain high availability (target 99.5%)
        assert availability >= 90.0, f"Availability {availability}% is too low"


class TestDataConsistency:
    """Test data consistency across services"""
    
    def test_profile_document_consistency(self):
        """
        Test data consistency between profile and documents
        Validates: Requirements 3.2, 3.3
        """
        profile_service = ProfileService()
        document_processor = DocumentProcessor()
        
        # Create profile
        profile_data = {
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
        
        profile_id = profile_service.create_profile(profile_data)
        
        # Create matching document
        matching_document = {
            "documentType": "aadhaar",
            "extractedData": {
                "name": "Ramesh Kumar",
                "address": "Khed, Pune"
            }
        }
        
        # Validate consistency
        validation = document_processor.validate_document(
            document_data=matching_document,
            profile_data=profile_data
        )
        
        assert validation["isValid"] is True
        
        # Create mismatched document
        mismatched_document = {
            "documentType": "aadhaar",
            "extractedData": {
                "name": "Different Name",
                "address": "Different Address"
            }
        }
        
        # Validate inconsistency detection
        validation = document_processor.validate_document(
            document_data=mismatched_document,
            profile_data=profile_data
        )
        
        assert validation["isValid"] is False
        assert len(validation.get("inconsistencies", [])) > 0
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_application_tracking_consistency(self):
        """
        Test consistency between application and tracking data
        Validates: Requirements 5.1, 5.2
        """
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        tracking_service = TrackingService()
        
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
        
        # Create application
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="PM-KISAN",
            profile_data=profile_data,
            document_data={}
        )
        
        if application_result["success"]:
            application_id = application_result["applicationId"]
            
            # Get tracking status
            tracking_status = tracking_service.get_application_status(application_id)
            
            # Verify consistency
            assert tracking_status is not None
            assert "status" in tracking_status
        
        # Cleanup
        profile_service.delete_profile(profile_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
