"""
Unit Tests for Enhanced Services with Error Handling
Tests enhanced document processor, auto-application, and tracking services
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.enhanced_document_processor import EnhancedDocumentProcessor
from services.enhanced_auto_application import EnhancedAutoApplicationService
from services.enhanced_tracking_service import EnhancedTrackingService
from services.document_processor import DocumentType, DocumentQuality
from shared.models.application import Application, ApplicationStatus
from shared.utils.error_handling import DocumentProcessingError, APIIntegrationError


class TestEnhancedDocumentProcessor:
    """Test enhanced document processor with error handling"""
    
    def test_process_document_with_empty_image(self):
        """Test processing with empty image data"""
        processor = EnhancedDocumentProcessor()
        
        empty_image = np.array([])
        result = processor.process_document_safe(
            empty_image,
            DocumentType.AADHAAR,
            language="en"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["fallbackAvailable"] is True
        assert result["error"]["fallbackMethod"] == "manual_entry"
    
    def test_process_document_with_poor_quality(self):
        """Test processing document with poor quality"""
        processor = EnhancedDocumentProcessor()
        
        # Create a low quality image (very dark)
        poor_image = np.ones((100, 100), dtype=np.uint8) * 10
        
        with patch.object(processor, 'process_document') as mock_process:
            mock_process.return_value = {
                "document_id": "test123",
                "quality_level": DocumentQuality.POOR,
                "quality_score": 0.3,
                "improvement_suggestions": ["Better lighting needed"],
                "validation_results": {"is_valid": True}
            }
            
            result = processor.process_document_safe(
                poor_image,
                DocumentType.AADHAAR,
                language="en"
            )
            
            assert result["success"] is True
            assert "warning" in result
            assert result["warning"]["fallbackAvailable"] is True
    
    def test_process_document_with_unreadable_quality(self):
        """Test processing unreadable document"""
        processor = EnhancedDocumentProcessor()
        
        unreadable_image = np.ones((100, 100), dtype=np.uint8) * 5
        
        with patch.object(processor, 'process_document') as mock_process:
            mock_process.return_value = {
                "document_id": "test123",
                "quality_level": DocumentQuality.UNREADABLE,
                "quality_score": 0.1,
                "improvement_suggestions": ["Image is unreadable"],
                "validation_results": {"is_valid": False}
            }
            
            result = processor.process_document_safe(
                unreadable_image,
                DocumentType.AADHAAR,
                language="en"
            )
            
            assert result["success"] is True
            assert result["requiresManualReview"] is True
            assert len(processor.manual_review_queue) == 1
    
    def test_get_manual_entry_form(self):
        """Test getting manual entry form for fallback"""
        processor = EnhancedDocumentProcessor()
        
        form = processor.get_manual_entry_form(DocumentType.AADHAAR)
        
        assert "fields" in form
        assert len(form["fields"]) > 0
        assert any(field["name"] == "aadhaar_number" for field in form["fields"])
    
    def test_fallback_mode(self):
        """Test enabling and disabling fallback mode"""
        processor = EnhancedDocumentProcessor()
        
        assert processor.fallback_mode is False
        
        processor.enable_fallback_mode()
        assert processor.fallback_mode is True
        
        processor.disable_fallback_mode()
        assert processor.fallback_mode is False
    
    def test_manual_review_queue(self):
        """Test manual review queue management"""
        processor = EnhancedDocumentProcessor()
        
        assert len(processor.get_manual_review_queue()) == 0
        
        # Queue a document
        processor._queue_for_manual_review(
            {"document_id": "test123", "document_type": "aadhaar"},
            {"profileId": "user123"}
        )
        
        queue = processor.get_manual_review_queue()
        assert len(queue) == 1
        assert queue[0]["documentId"] == "test123"


class TestEnhancedAutoApplicationService:
    """Test enhanced auto-application service with error handling"""
    
    def test_submit_application_with_validation_error(self):
        """Test submission with validation errors"""
        service = EnhancedAutoApplicationService()
        
        # Mock form manager to avoid template errors
        with patch.object(service.form_manager, 'auto_populate_form') as mock_populate:
            mock_populate.return_value = {
                "schemeName": "PM-KISAN",
                "formData": {"test": "data"},
                "populatedAt": datetime.utcnow().isoformat()
            }
            
            # Create a test application
            app_data = service.create_application(
                user_id="user123",
                scheme_id="pm_kisan",
                user_profile={"name": "Test User"},
                document_data={}
            )
            
            app_id = app_data["applicationId"]
        
        # Mock validation to fail
        with patch.object(service, 'validate_application') as mock_validate:
            mock_validate.return_value = {
                "isValid": False,
                "errors": ["Missing required field"]
            }
            
            result = service.submit_application_safe(app_id, language="en")
            
            assert result["success"] is False
            assert "error" in result
    
    def test_submit_application_with_api_failure(self):
        """Test submission with API failure and fallback"""
        service = EnhancedAutoApplicationService()
        
        # Mock form manager to avoid template errors
        with patch.object(service.form_manager, 'auto_populate_form') as mock_populate:
            mock_populate.return_value = {
                "schemeName": "PM-KISAN",
                "formData": {"test": "data"},
                "populatedAt": datetime.utcnow().isoformat()
            }
            
            # Create application
            app_data = service.create_application(
                user_id="user123",
                scheme_id="pm_kisan",
                user_profile={"name": "Test User"},
                document_data={}
            )
            
            app_id = app_data["applicationId"]
        
        # Mock validation to pass but submission to fail
        with patch.object(service, 'validate_application') as mock_validate, \
             patch.object(service, 'submit_application') as mock_submit:
            
            mock_validate.return_value = {"isValid": True}
            mock_submit.return_value = {
                "status": "submission_failed",
                "error": "API unavailable"
            }
            
            result = service.submit_application_safe(app_id, language="en")
            
            assert "fallback" in result
            assert result["queuedForRetry"] is True
            assert len(service.offline_queue) == 1
    
    def test_get_fallback_instructions(self):
        """Test getting fallback instructions"""
        service = EnhancedAutoApplicationService()
        
        instructions = service._get_fallback_instructions("pm_kisan", "en")
        
        assert "office" in instructions
        assert "website" in instructions
        assert "helpline" in instructions
        assert "requiredDocuments" in instructions
        assert len(instructions["instructions"]) > 0
    
    def test_offline_queue_processing(self):
        """Test processing offline submission queue"""
        service = EnhancedAutoApplicationService()
        
        # Mock form manager to avoid template errors
        with patch.object(service.form_manager, 'auto_populate_form') as mock_populate:
            mock_populate.return_value = {
                "schemeName": "PM-KISAN",
                "formData": {"test": "data"},
                "populatedAt": datetime.utcnow().isoformat()
            }
            
            # Create and queue an application
            app_data = service.create_application(
                user_id="user123",
                scheme_id="pm_kisan",
                user_profile={"name": "Test User"},
                document_data={}
            )
            
            app_id = app_data["applicationId"]
            application = service.applications[app_id]
        
        service._queue_offline_submission(app_id, application)
        
        assert len(service.offline_queue) == 1
        
        # Mock successful submission
        with patch.object(service, 'submit_application') as mock_submit:
            mock_submit.return_value = {
                "status": "submitted",
                "governmentRefNumber": "REF123"
            }
            
            results = service.process_offline_queue()
            
            assert results["processed"] == 1
            assert results["successful"] == 1
            assert results["failed"] == 0
            assert len(service.offline_queue) == 0
    
    def test_get_offline_queue_status(self):
        """Test getting offline queue status"""
        service = EnhancedAutoApplicationService()
        
        status = service.get_offline_queue_status()
        assert status["queueLength"] == 0
        assert len(status["applications"]) == 0
    
    def test_api_health_check_with_degraded_service(self):
        """Test API health check with degraded services"""
        service = EnhancedAutoApplicationService()
        
        with patch.object(service, 'get_api_health') as mock_health:
            mock_health.return_value = {
                "pm_kisan": {"status": "degraded"},
                "dbt": {"status": "healthy"}
            }
            
            health = service.get_api_health_safe(language="en")
            
            assert "warning" in health
            assert len(health["warning"]["degradedServices"]) > 0


class TestEnhancedTrackingService:
    """Test enhanced tracking service with error handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_gov_api = Mock()
        self.service = EnhancedTrackingService(self.mock_gov_api)
    
    def test_poll_application_not_registered(self):
        """Test polling unregistered application"""
        result = self.service.poll_application_safe("unknown_id", language="en")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_poll_application_with_cached_fallback(self):
        """Test polling with cached status fallback"""
        # Create and register a mock application
        mock_app = Mock(spec=Application)
        mock_app.application_id = "app123"
        mock_app.scheme_id = "pm_kisan"
        mock_app.government_ref_number = "REF123"
        mock_app.status = ApplicationStatus.SUBMITTED
        mock_app.submitted_at = datetime.utcnow()
        mock_app.predictions = None
        mock_app.status_history = []
        
        self.service.register_application(mock_app)
        
        # Cache a status
        cached_data = {
            "success": True,
            "currentStatus": "submitted",
            "lastUpdated": datetime.utcnow().isoformat()
        }
        self.service._cache_status("app123", cached_data)
        
        # Mock polling to fail
        with patch.object(self.service, '_poll_with_fallback') as mock_poll:
            mock_poll.return_value = {"success": False, "error": "API unavailable"}
            
            result = self.service.poll_application_safe("app123", language="en")
            
            assert result["success"] is True
            assert result["source"] == "cached"
            assert "warning" in result
    
    def test_get_status_with_guidance(self):
        """Test getting status with user guidance"""
        # Create and register a mock application
        mock_app = Mock(spec=Application)
        mock_app.application_id = "app123"
        mock_app.scheme_id = "pm_kisan"
        mock_app.government_ref_number = "REF123"
        mock_app.status = ApplicationStatus.APPROVED
        mock_app.submitted_at = datetime.utcnow()
        mock_app.predictions = None
        mock_app.status_history = []
        
        self.service.register_application(mock_app)
        
        result = self.service.get_status_with_guidance("app123", language="en")
        
        assert result["success"] is True
        assert "guidance" in result
        assert "message" in result["guidance"]
        assert "nextSteps" in result["guidance"]
    
    def test_get_manual_check_instructions(self):
        """Test getting manual check instructions"""
        # Create and register a mock application
        mock_app = Mock(spec=Application)
        mock_app.application_id = "app123"
        mock_app.scheme_id = "pm_kisan"
        mock_app.government_ref_number = "REF123"
        
        self.service.register_application(mock_app)
        
        instructions = self.service.get_manual_check_instructions("app123", language="en")
        
        assert "title" in instructions
        assert "steps" in instructions
        assert "referenceNumber" in instructions
        assert len(instructions["steps"]) > 0
    
    def test_cache_expiration(self):
        """Test cached status expiration"""
        # Cache a status
        cached_data = {"test": "data"}
        self.service._cache_status("app123", cached_data)
        
        # Should be available immediately
        result = self.service._get_cached_status("app123")
        assert result is not None
        
        # Manually expire the cache
        self.service.cached_statuses["app123"]["expiresAt"] = datetime.utcnow()
        
        # Should be None after expiration
        result = self.service._get_cached_status("app123")
        assert result is None
    
    def test_status_guidance_for_different_statuses(self):
        """Test status guidance for different application statuses"""
        statuses = ["submitted", "under_review", "approved", "rejected"]
        
        for status in statuses:
            guidance = self.service._get_status_guidance(status, "en")
            
            assert "message" in guidance
            assert "nextSteps" in guidance
            assert len(guidance["nextSteps"]) > 0


class TestErrorHandlingIntegration:
    """Integration tests for error handling across services"""
    
    def test_document_to_application_error_flow(self):
        """Test error flow from document processing to application"""
        doc_processor = EnhancedDocumentProcessor()
        app_service = EnhancedAutoApplicationService()
        
        # Process a poor quality document
        poor_image = np.ones((100, 100), dtype=np.uint8) * 10
        
        with patch.object(doc_processor, 'process_document') as mock_process:
            mock_process.return_value = {
                "document_id": "doc123",
                "quality_level": DocumentQuality.POOR,
                "quality_score": 0.3,
                "improvement_suggestions": ["Better lighting"],
                "validation_results": {"is_valid": True},
                "parsed_data": {}
            }
            
            doc_result = doc_processor.process_document_safe(
                poor_image,
                DocumentType.AADHAAR
            )
            
            # Should have warning but still succeed
            assert doc_result["success"] is True
            assert "warning" in doc_result
    
    def test_end_to_end_error_recovery(self):
        """Test end-to-end error recovery with fallbacks"""
        app_service = EnhancedAutoApplicationService()
        
        # Mock form manager to avoid template errors
        with patch.object(app_service.form_manager, 'auto_populate_form') as mock_populate:
            mock_populate.return_value = {
                "schemeName": "PM-KISAN",
                "formData": {"test": "data"},
                "populatedAt": datetime.utcnow().isoformat()
            }
            
            # Create application
            app_data = app_service.create_application(
                user_id="user123",
                scheme_id="pm_kisan",
                user_profile={"name": "Test User"},
                document_data={}
            )
            
            app_id = app_data["applicationId"]
        
        # Simulate API failure with fallback
        with patch.object(app_service, 'validate_application') as mock_validate, \
             patch.object(app_service, 'submit_application') as mock_submit:
            
            mock_validate.return_value = {"isValid": True}
            mock_submit.return_value = {
                "status": "submission_failed",
                "error": "API unavailable"
            }
            
            result = app_service.submit_application_safe(app_id)
            
            # Should provide fallback instructions
            assert "fallback" in result
            assert "instructions" in result["fallback"]
            assert result["queuedForRetry"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
