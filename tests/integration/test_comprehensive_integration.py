"""
Comprehensive Integration Tests
Tests cross-service communication, data consistency, and performance under realistic load
Task 14.2: Write comprehensive integration tests
"""

import pytest
import time
import concurrent.futures
from typing import Dict, Any, List
from datetime import datetime, timedelta

from services.profile_service import ProfileService
from services.eligibility_engine import EligibilityEngine
from services.document_processor import DocumentProcessor
from services.auto_application_service import AutoApplicationService
from services.tracking_service import TrackingService
from services.notification_service import NotificationService
from services.sms_interface import SMSInterfaceHandler
from services.voice_interface import VoiceInterfaceHandler
from services.government_api_client import GovernmentAPIIntegration
from shared.utils.audit_log import get_audit_logger, AuditEventType
from shared.cache.redis_client import get_redis_client
from shared.database.models import get_db_session


class TestCrossServiceCommunication:
    """Test communication and data flow between services"""
    
    @pytest.fixture
    def sample_profile(self) -> Dict[str, Any]:
        """Sample profile for testing"""
        return {
            "demographics": {
                "name": "Integration Test User",
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
    
    def test_profile_to_eligibility_communication(self, sample_profile):
        """Test data flow from profile service to eligibility engine"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile)
        
        # Retrieve profile
        retrieved_profile = profile_service.get_profile(profile_id)
        
        # Load schemes
        schemes = [
            {
                "schemeId": "PM-KISAN",
                "name": "PM-KISAN",
                "benefitAmount": 6000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1, "max": 2.0},
                    "employmentStatus": ["farmer"]
                }
            }
        ]
        eligibility_engine.load_schemes(schemes)
        
        # Evaluate eligibility using retrieved profile
        eligible_schemes = eligibility_engine.evaluate_eligibility(retrieved_profile)
        
        # Verify communication worked
        assert len(eligible_schemes) > 0
        assert eligible_schemes[0]["schemeId"] == "PM-KISAN"
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_eligibility_to_application_communication(self, sample_profile):
        """Test data flow from eligibility engine to auto-application service"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        auto_application_service = AutoApplicationService()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile)
        
        # Evaluate eligibility
        schemes = [
            {
                "schemeId": "PM-KISAN",
                "name": "PM-KISAN",
                "benefitAmount": 6000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1, "max": 2.0},
                    "employmentStatus": ["farmer"]
                }
            }
        ]
        eligibility_engine.load_schemes(schemes)
        eligible_schemes = eligibility_engine.evaluate_eligibility(sample_profile)
        
        # Create application using eligible scheme
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id=eligible_schemes[0]["schemeId"],
            profile_data=sample_profile,
            document_data={}
        )
        
        # Verify communication worked
        assert application_result["success"] is True
        assert "applicationId" in application_result
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_application_to_tracking_communication(self, sample_profile):
        """Test data flow from application service to tracking service"""
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        tracking_service = TrackingService()
        
        # Create profile and application
        profile_id = profile_service.create_profile(sample_profile)
        
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="PM-KISAN",
            profile_data=sample_profile,
            document_data={}
        )
        
        if application_result["success"]:
            application_id = application_result["applicationId"]
            
            # Track application
            tracking_status = tracking_service.get_application_status(application_id)
            
            # Verify communication worked
            assert tracking_status is not None
            assert "status" in tracking_status
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_tracking_to_notification_communication(self, sample_profile):
        """Test data flow from tracking service to notification service"""
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        tracking_service = TrackingService()
        notification_service = NotificationService()
        
        # Create profile and application
        profile_id = profile_service.create_profile(sample_profile)
        
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="PM-KISAN",
            profile_data=sample_profile,
            document_data={}
        )
        
        if application_result["success"]:
            application_id = application_result["applicationId"]
            
            # Get tracking status
            tracking_status = tracking_service.get_application_status(application_id)
            
            # Send notification based on tracking status
            notification_result = notification_service.send_notification(
                user_id=profile_id,
                channel="sms",
                message=f"Application status: {tracking_status.get('status', 'unknown')}",
                language="marathi"
            )
            
            # Verify communication worked
            assert notification_result["success"] is True
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_document_to_application_communication(self, sample_profile):
        """Test data flow from document processor to application service"""
        profile_service = ProfileService()
        document_processor = DocumentProcessor()
        auto_application_service = AutoApplicationService()
        
        # Create profile
        profile_id = profile_service.create_profile(sample_profile)
        
        # Process document
        document_data = {
            "documentType": "aadhaar",
            "extractedData": {
                "aadhaarNumber": "123456789012",
                "name": "Integration Test User",
                "address": "Khed, Pune"
            }
        }
        
        # Validate document
        validation_result = document_processor.validate_document(
            document_data=document_data,
            profile_data=sample_profile
        )
        
        # Create application using validated document
        if validation_result["isValid"]:
            application_result = auto_application_service.create_application(
                user_id=profile_id,
                scheme_id="PM-KISAN",
                profile_data=sample_profile,
                document_data=document_data
            )
            
            # Verify communication worked
            assert application_result["success"] is True
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_multi_channel_interface_communication(self, sample_profile):
        """Test communication between SMS/voice interfaces and core services"""
        sms_interface = SMSInterfaceHandler()
        voice_interface = VoiceInterfaceHandler()
        profile_service = ProfileService()
        
        # Test SMS interface communication
        sms_response = sms_interface.handle_message(
            phone_number=sample_profile["preferences"]["phoneNumber"],
            message="PROFILE BANAO",
            language="marathi"
        )
        
        assert sms_response is not None
        assert len(sms_response) > 0
        
        # Test voice interface communication
        voice_response = voice_interface.handle_call(
            phone_number=sample_profile["preferences"]["phoneNumber"],
            language="marathi"
        )
        
        assert voice_response["status"] == "success"
        assert "greeting" in voice_response


class TestDataConsistency:
    """Test data consistency across services"""
    
    @pytest.fixture
    def test_profile(self) -> Dict[str, Any]:
        """Test profile for consistency checks"""
        return {
            "demographics": {
                "name": "Consistency Test User",
                "age": 40,
                "gender": "female",
                "caste": "sc",
                "maritalStatus": "married"
            },
            "economic": {
                "annualIncome": 120000,
                "landOwnership": 0.8,
                "employmentStatus": "farmer",
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
                "elderlyMembers": 1
            },
            "preferences": {
                "language": "marathi",
                "communicationChannel": "sms",
                "phoneNumber": "+919876543220"
            }
        }
    
    def test_profile_update_consistency(self, test_profile):
        """Test data consistency when profile is updated across services"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
        # Create profile
        profile_id = profile_service.create_profile(test_profile)
        
        # Load income-based scheme
        schemes = [
            {
                "schemeId": "LOW-INCOME",
                "name": "Low Income Support",
                "benefitAmount": 15000,
                "eligibilityCriteria": {
                    "annualIncome": {"max": 100000}
                }
            }
        ]
        
        eligibility_engine.load_schemes(schemes)
        
        # Initial eligibility check (income 120000 - not eligible)
        initial_profile = profile_service.get_profile(profile_id)
        initial_schemes = eligibility_engine.evaluate_eligibility(initial_profile)
        initial_scheme_ids = [s["schemeId"] for s in initial_schemes]
        
        # Update profile to lower income
        profile_service.update_profile(profile_id, {
            "economic": {"annualIncome": 80000}
        })
        
        # Re-check eligibility (should now be eligible)
        updated_profile = profile_service.get_profile(profile_id)
        updated_schemes = eligibility_engine.evaluate_eligibility(updated_profile)
        updated_scheme_ids = [s["schemeId"] for s in updated_schemes]
        
        # Verify consistency
        assert updated_profile["economic"]["annualIncome"] == 80000
        assert "LOW-INCOME" in updated_scheme_ids
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_document_profile_consistency(self, test_profile):
        """Test consistency between document data and profile data"""
        profile_service = ProfileService()
        document_processor = DocumentProcessor()
        
        # Create profile
        profile_id = profile_service.create_profile(test_profile)
        
        # Matching document
        matching_doc = {
            "documentType": "aadhaar",
            "extractedData": {
                "name": "Consistency Test User",
                "address": "Khed, Pune"
            }
        }
        
        validation = document_processor.validate_document(
            document_data=matching_doc,
            profile_data=test_profile
        )
        
        assert validation["isValid"] is True
        
        # Mismatched document
        mismatched_doc = {
            "documentType": "aadhaar",
            "extractedData": {
                "name": "Different Name",
                "address": "Different Location"
            }
        }
        
        validation = document_processor.validate_document(
            document_data=mismatched_doc,
            profile_data=test_profile
        )
        
        assert validation["isValid"] is False
        assert len(validation.get("inconsistencies", [])) > 0
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_application_tracking_consistency(self, test_profile):
        """Test consistency between application and tracking data"""
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        tracking_service = TrackingService()
        
        # Create profile and application
        profile_id = profile_service.create_profile(test_profile)
        
        application_result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="PM-KISAN",
            profile_data=test_profile,
            document_data={}
        )
        
        if application_result["success"]:
            application_id = application_result["applicationId"]
            
            # Get tracking data
            tracking_data = tracking_service.get_application_status(application_id)
            
            # Verify consistency
            assert tracking_data is not None
            assert "status" in tracking_data
            assert tracking_data["status"] in ["draft", "submitted", "under_review", "approved", "rejected"]
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_cache_database_consistency(self, test_profile):
        """Test consistency between cache and database"""
        profile_service = ProfileService()
        redis_client = get_redis_client()
        
        # Create profile (should be in both DB and cache)
        profile_id = profile_service.create_profile(test_profile)
        
        # Get from service (may use cache)
        cached_profile = profile_service.get_profile(profile_id)
        
        # Clear cache
        cache_key = f"profile:{profile_id}"
        redis_client.delete(cache_key)
        
        # Get from service again (should fetch from DB)
        db_profile = profile_service.get_profile(profile_id)
        
        # Verify consistency
        assert cached_profile["demographics"]["name"] == db_profile["demographics"]["name"]
        assert cached_profile["economic"]["annualIncome"] == db_profile["economic"]["annualIncome"]
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_audit_trail_consistency(self, test_profile):
        """Test consistency of audit trail across operations"""
        profile_service = ProfileService()
        audit_logger = get_audit_logger()
        
        # Create profile
        profile_id = profile_service.create_profile(test_profile)
        
        # Log event
        audit_logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            user_id=profile_id,
            username=test_profile["demographics"]["name"],
            resource_type="profile",
            resource_id=profile_id,
            success=True
        )
        
        # Update profile
        profile_service.update_profile(profile_id, {
            "economic": {"annualIncome": 90000}
        })
        
        # Log update event
        audit_logger.log_event(
            event_type=AuditEventType.PROFILE_UPDATED,
            action="Profile updated",
            user_id=profile_id,
            username=test_profile["demographics"]["name"],
            resource_type="profile",
            resource_id=profile_id,
            success=True
        )
        
        # Get audit trail
        audit_trail = audit_logger.get_resource_audit_trail(
            resource_type="profile",
            resource_id=profile_id
        )
        
        # Verify consistency
        assert len(audit_trail) >= 2
        assert audit_trail[0].event_type == AuditEventType.PROFILE_CREATED
        
        # Cleanup
        profile_service.delete_profile(profile_id)


class TestPerformanceUnderLoad:
    """Test system performance under realistic load conditions"""
    
    def test_concurrent_profile_creation(self):
        """Test concurrent profile creation performance"""
        profile_service = ProfileService()
        num_profiles = 50
        
        def create_profile(index):
            profile_data = {
                "demographics": {
                    "name": f"Load Test User {index}",
                    "age": 30 + (index % 30),
                    "gender": "male" if index % 2 == 0 else "female",
                    "caste": "general",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 100000 + (index * 1000),
                    "landOwnership": index * 0.1,
                    "employmentStatus": "farmer",
                    "bankAccount": f"ACC{index:010d}"
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
            return profile_service.create_profile(profile_data)
        
        # Create profiles concurrently
        start_time = time.time()
        profile_ids = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_profile, i) for i in range(num_profiles)]
            profile_ids = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        avg_time = total_time / num_profiles
        
        # Verify performance
        assert len(profile_ids) == num_profiles
        assert avg_time < 1.0, f"Average profile creation time {avg_time}s is too slow"
        
        # Cleanup
        for profile_id in profile_ids:
            profile_service.delete_profile(profile_id)
    
    def test_concurrent_eligibility_evaluation(self):
        """Test concurrent eligibility evaluation performance (Requirement 9.1)"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        
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
        
        # Create test profiles
        num_profiles = 100
        profiles = []
        
        for i in range(num_profiles):
            profile_data = {
                "demographics": {
                    "name": f"User {i}",
                    "age": 25 + (i % 40),
                    "gender": "male" if i % 2 == 0 else "female",
                    "caste": "general",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 100000 + (i * 1000),
                    "landOwnership": i * 0.1,
                    "employmentStatus": "farmer",
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
            profiles.append(profile_data)
        
        # Evaluate eligibility concurrently
        def evaluate_eligibility(profile_data):
            start = time.time()
            schemes = eligibility_engine.evaluate_eligibility(profile_data)
            elapsed = time.time() - start
            return elapsed, len(schemes)
        
        start_time = time.time()
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(evaluate_eligibility, p) for p in profiles]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        evaluation_times = [r[0] for r in results]
        avg_time = sum(evaluation_times) / len(evaluation_times)
        max_time = max(evaluation_times)
        
        # Verify performance requirements (< 5 seconds per evaluation)
        assert avg_time < 5.0, f"Average evaluation time {avg_time}s exceeds 5s requirement"
        assert max_time < 5.0, f"Max evaluation time {max_time}s exceeds 5s requirement"
        assert all(r[1] > 0 for r in results), "All evaluations should return schemes"
    
    def test_concurrent_application_submission(self):
        """Test concurrent application submission performance"""
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        num_applications = 30
        
        # Create test profiles
        profile_ids = []
        for i in range(num_applications):
            profile_data = {
                "demographics": {
                    "name": f"App Test User {i}",
                    "age": 30,
                    "gender": "male",
                    "caste": "general",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 150000,
                    "landOwnership": 1.5,
                    "employmentStatus": "farmer",
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
            profile_ids.append((profile_id, profile_data))
        
        # Submit applications concurrently
        def submit_application(profile_tuple):
            profile_id, profile_data = profile_tuple
            result = auto_application_service.create_application(
                user_id=profile_id,
                scheme_id="PM-KISAN",
                profile_data=profile_data,
                document_data={}
            )
            return result["success"] if result else False
        
        start_time = time.time()
        success_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_application, p) for p in profile_ids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            success_count = sum(1 for r in results if r)
        
        total_time = time.time() - start_time
        
        # Verify performance and success rate
        assert success_count >= num_applications * 0.9, "At least 90% applications should succeed"
        assert total_time < 60.0, f"Total time {total_time}s is too slow for {num_applications} applications"
        
        # Cleanup
        for profile_id, _ in profile_ids:
            profile_service.delete_profile(profile_id)
    
    def test_high_volume_notification_delivery(self):
        """Test notification service under high volume"""
        profile_service = ProfileService()
        notification_service = NotificationService()
        num_notifications = 50
        
        # Create test profiles
        profile_ids = []
        for i in range(num_notifications):
            profile_data = {
                "demographics": {
                    "name": f"Notification Test {i}",
                    "age": 30,
                    "gender": "male",
                    "caste": "general",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 150000,
                    "landOwnership": 1.5,
                    "employmentStatus": "farmer",
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
                    "communicationChannel": "sms",
                    "phoneNumber": f"+9198765432{i:02d}"
                }
            }
            profile_id = profile_service.create_profile(profile_data)
            profile_ids.append(profile_id)
        
        # Send notifications concurrently
        def send_notification(profile_id):
            result = notification_service.send_notification(
                user_id=profile_id,
                channel="sms",
                message="Test notification",
                language="marathi"
            )
            return result["success"] if result else False
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(send_notification, pid) for pid in profile_ids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in results if r) / len(results)
        
        # Verify performance
        assert success_rate >= 0.85, f"Success rate {success_rate} is too low"
        assert total_time < 30.0, f"Total time {total_time}s is too slow"
        
        # Cleanup
        for profile_id in profile_ids:
            profile_service.delete_profile(profile_id)
    
    def test_database_connection_pool_under_load(self):
        """Test database connection pooling under concurrent load"""
        profile_service = ProfileService()
        num_operations = 100
        
        def perform_db_operations(index):
            # Create
            profile_data = {
                "demographics": {
                    "name": f"DB Test {index}",
                    "age": 30,
                    "gender": "male",
                    "caste": "general",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 150000,
                    "landOwnership": 1.5,
                    "employmentStatus": "farmer",
                    "bankAccount": f"ACC{index:010d}"
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
            
            # Read
            profile = profile_service.get_profile(profile_id)
            
            # Update
            profile_service.update_profile(profile_id, {
                "economic": {"annualIncome": 160000}
            })
            
            # Delete
            profile_service.delete_profile(profile_id)
            
            return profile_id is not None
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(perform_db_operations, i) for i in range(num_operations)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in results if r) / len(results)
        
        # Verify performance
        assert success_rate >= 0.95, f"Success rate {success_rate} is too low"
        assert total_time < 60.0, f"Total time {total_time}s is too slow"
    
    def test_cache_performance_under_load(self):
        """Test Redis cache performance under concurrent load"""
        profile_service = ProfileService()
        redis_client = get_redis_client()
        
        # Create test profile
        profile_data = {
            "demographics": {
                "name": "Cache Test User",
                "age": 30,
                "gender": "male",
                "caste": "general",
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
        
        # Concurrent cache reads
        def read_from_cache(index):
            profile = profile_service.get_profile(profile_id)
            return profile is not None
        
        num_reads = 200
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(read_from_cache, i) for i in range(num_reads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in results if r) / len(results)
        avg_time = total_time / num_reads
        
        # Verify cache performance
        assert success_rate >= 0.99, f"Cache success rate {success_rate} is too low"
        assert avg_time < 0.1, f"Average cache read time {avg_time}s is too slow"
        
        # Cleanup
        profile_service.delete_profile(profile_id)


class TestEndToEndIntegration:
    """End-to-end integration tests across all services"""
    
    def test_complete_user_journey_under_load(self):
        """Test complete user journey with multiple concurrent users"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        auto_application_service = AutoApplicationService()
        tracking_service = TrackingService()
        notification_service = NotificationService()
        
        # Load schemes
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
                "schemeId": "MGNREGA",
                "name": "MGNREGA",
                "benefitAmount": 25000,
                "eligibilityCriteria": {
                    "age": {"min": 18, "max": 65}
                }
            }
        ]
        eligibility_engine.load_schemes(schemes)
        
        def complete_journey(index):
            # Step 1: Create profile
            profile_data = {
                "demographics": {
                    "name": f"Journey User {index}",
                    "age": 35,
                    "gender": "male" if index % 2 == 0 else "female",
                    "caste": "obc",
                    "maritalStatus": "married"
                },
                "economic": {
                    "annualIncome": 150000,
                    "landOwnership": 1.5,
                    "employmentStatus": "farmer",
                    "bankAccount": f"ACC{index:010d}"
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
                    "phoneNumber": f"+9198765432{index:02d}"
                }
            }
            
            profile_id = profile_service.create_profile(profile_data)
            
            # Step 2: Evaluate eligibility
            eligible_schemes = eligibility_engine.evaluate_eligibility(profile_data)
            
            if len(eligible_schemes) == 0:
                profile_service.delete_profile(profile_id)
                return False
            
            # Step 3: Create application
            application_result = auto_application_service.create_application(
                user_id=profile_id,
                scheme_id=eligible_schemes[0]["schemeId"],
                profile_data=profile_data,
                document_data={}
            )
            
            if not application_result.get("success"):
                profile_service.delete_profile(profile_id)
                return False
            
            application_id = application_result["applicationId"]
            
            # Step 4: Track application
            tracking_status = tracking_service.get_application_status(application_id)
            
            # Step 5: Send notification
            notification_result = notification_service.send_notification(
                user_id=profile_id,
                channel="sms",
                message="Application submitted successfully",
                language="marathi"
            )
            
            # Cleanup
            profile_service.delete_profile(profile_id)
            
            return tracking_status is not None and notification_result.get("success", False)
        
        # Execute complete journeys concurrently
        num_users = 20
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(complete_journey, i) for i in range(num_users)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in results if r) / len(results)
        
        # Verify end-to-end performance
        assert success_rate >= 0.8, f"Success rate {success_rate} is too low"
        assert total_time < 120.0, f"Total time {total_time}s is too slow for {num_users} users"
    
    def test_government_api_integration_under_load(self):
        """Test government API integration with concurrent requests"""
        api_integration = GovernmentAPIIntegration()
        num_requests = 30
        
        def submit_to_government_api(index):
            application_data = {
                "aadhaar_number": f"12345678{index:04d}",
                "name": f"API Test User {index}",
                "bank_account": f"ACC{index:010d}",
                "bank_ifsc": "SBIN0001234",
                "land_ownership": 1.5
            }
            
            result = api_integration.submit_application(
                scheme_id="PM-KISAN",
                application_data=application_data
            )
            
            return result.get("success", False)
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_to_government_api, i) for i in range(num_requests)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_rate = sum(1 for r in results if r) / len(results)
        
        # Verify API integration performance
        assert success_rate >= 0.7, f"API success rate {success_rate} is too low"
        assert total_time < 60.0, f"Total time {total_time}s is too slow"
    
    def test_system_resilience_under_failure(self):
        """Test system resilience when services fail"""
        profile_service = ProfileService()
        auto_application_service = AutoApplicationService()
        
        # Create profile
        profile_data = {
            "demographics": {
                "name": "Resilience Test",
                "age": 30,
                "gender": "male",
                "caste": "general",
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
        
        # Test with invalid scheme (should handle gracefully)
        result = auto_application_service.create_application(
            user_id=profile_id,
            scheme_id="INVALID-SCHEME",
            profile_data=profile_data,
            document_data={}
        )
        
        # Should return error or fallback, not crash
        assert "error" in result or "fallbackMethod" in result or result.get("success") is False
        
        # Cleanup
        profile_service.delete_profile(profile_id)
    
    def test_data_integrity_across_services(self):
        """Test data integrity maintained across all services"""
        profile_service = ProfileService()
        eligibility_engine = EligibilityEngine()
        auto_application_service = AutoApplicationService()
        audit_logger = get_audit_logger()
        
        # Create profile
        profile_data = {
            "demographics": {
                "name": "Integrity Test User",
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
        
        # Log creation
        audit_logger.log_event(
            event_type=AuditEventType.PROFILE_CREATED,
            action="Profile created",
            user_id=profile_id,
            username=profile_data["demographics"]["name"],
            resource_type="profile",
            resource_id=profile_id,
            success=True
        )
        
        # Retrieve and verify
        retrieved_profile = profile_service.get_profile(profile_id)
        assert retrieved_profile["demographics"]["name"] == profile_data["demographics"]["name"]
        assert retrieved_profile["economic"]["annualIncome"] == profile_data["economic"]["annualIncome"]
        
        # Evaluate eligibility
        schemes = [
            {
                "schemeId": "PM-KISAN",
                "name": "PM-KISAN",
                "benefitAmount": 6000,
                "eligibilityCriteria": {
                    "landOwnership": {"min": 0.1, "max": 2.0},
                    "employmentStatus": ["farmer"]
                }
            }
        ]
        eligibility_engine.load_schemes(schemes)
        eligible_schemes = eligibility_engine.evaluate_eligibility(retrieved_profile)
        
        # Create application
        if len(eligible_schemes) > 0:
            application_result = auto_application_service.create_application(
                user_id=profile_id,
                scheme_id=eligible_schemes[0]["schemeId"],
                profile_data=retrieved_profile,
                document_data={}
            )
            
            # Verify data integrity
            assert application_result.get("success") is True
        
        # Verify audit trail
        audit_trail = audit_logger.get_resource_audit_trail(
            resource_type="profile",
            resource_id=profile_id
        )
        
        assert len(audit_trail) > 0
        assert audit_trail[0].resource_id == profile_id
        
        # Cleanup
        profile_service.delete_profile(profile_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
