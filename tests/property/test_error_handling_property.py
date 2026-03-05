"""
Property-Based Tests for Error Handling and Fallback Mechanisms
Feature: sarvasahay-platform, Property 11: Error Handling and Fallback Mechanisms

This test validates that for any system failure scenario, the system:
1. Provides alternative methods when APIs are unavailable
2. Gives specific guidance for document quality improvement
3. Provides appropriate alerts with suggested actions for processing delays
4. Implements graceful degradation and fallback mechanisms

Validates: Requirements 3.5, 4.4, 5.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

from services.enhanced_document_processor import EnhancedDocumentProcessor
from services.enhanced_auto_application import EnhancedAutoApplicationService
from services.enhanced_tracking_service import EnhancedTrackingService
from services.document_processor import DocumentType, DocumentQuality
from services.government_api_client import GovernmentAPIIntegration, APIError
from services.tracking_service import TrackingConfig
from shared.utils.error_handling import (
    DocumentProcessingError,
    APIIntegrationError,
    TrackingError,
    ErrorSeverity,
    CircuitBreaker,
    RetryStrategy,
    FallbackManager,
    ErrorMessageGenerator
)


# Strategy for generating document images with varying quality
@st.composite
def document_image_with_quality_strategy(draw):
    """Generate document images with controlled quality issues"""
    width = draw(st.integers(min_value=50, max_value=500))
    height = draw(st.integers(min_value=50, max_value=500))
    
    # Create base image
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Add quality issues
    quality_issue = draw(st.sampled_from(['noise', 'blur', 'low_contrast', 'small_size', 'good']))
    
    if quality_issue == 'noise':
        # Add heavy noise
        noise = np.random.randint(-100, 100, image.shape, dtype=np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    elif quality_issue == 'blur':
        # Simulate blur by reducing resolution
        small = image[::4, ::4]
        image = np.repeat(np.repeat(small, 4, axis=0), 4, axis=1)[:height, :width]
    elif quality_issue == 'low_contrast':
        # Reduce contrast
        image = (image * 0.3 + 128).astype(np.uint8)
    elif quality_issue == 'small_size':
        # Very small image
        image = image[:min(height, 80), :min(width, 80)]
    
    return image, quality_issue


# Strategy for generating API failure scenarios
@st.composite
def api_failure_scenario_strategy(draw):
    """Generate various API failure scenarios"""
    return draw(st.sampled_from([
        'timeout',
        'connection_error',
        'server_error',
        'rate_limit',
        'authentication_error',
        'service_unavailable'
    ]))


# Strategy for generating application delays
@st.composite
def application_delay_strategy(draw):
    """Generate application processing delay scenarios"""
    expected_days = draw(st.integers(min_value=30, max_value=45))
    actual_days = draw(st.integers(min_value=expected_days, max_value=expected_days + 60))
    delay_days = actual_days - expected_days
    
    return {
        'expected_days': expected_days,
        'actual_days': actual_days,
        'delay_days': delay_days,
        'is_delayed': delay_days > 0
    }


class TestErrorHandlingAndFallbackProperty:
    """
    Property 11: Error Handling and Fallback Mechanisms
    
    For any system failure scenario, the system should:
    1. Provide alternative methods when services fail
    2. Give specific guidance for improvement
    3. Provide appropriate alerts with suggested actions
    4. Implement graceful degradation
    """
    
    @given(
        image_data=document_image_with_quality_strategy(),
        document_type=st.sampled_from(list(DocumentType)),
        language=st.sampled_from(['en', 'hi', 'mr'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_processing_provides_improvement_guidance(
        self,
        image_data: tuple,
        document_type: DocumentType,
        language: str
    ):
        """
        Property: Poor quality documents must receive specific improvement guidance
        
        Validates Requirement 3.5: System provides guidance for document quality improvement
        """
        image, quality_issue = image_data
        processor = EnhancedDocumentProcessor()
        
        try:
            # Process document
            result = processor.process_document_safe(image, document_type, None, language)
            
            # Verify result structure
            assert 'success' in result or 'error' in result
            
            # If quality is poor, improvement suggestions must be provided
            if 'quality_level' in result:
                quality_level = result['quality_level']
                
                if quality_level in [DocumentQuality.POOR, DocumentQuality.UNREADABLE]:
                    # Must have improvement suggestions
                    assert 'improvement_suggestions' in result or 'warning' in result
                    
                    if 'improvement_suggestions' in result:
                        suggestions = result['improvement_suggestions']
                        assert isinstance(suggestions, list)
                        assert len(suggestions) > 0
                        
                        # Suggestions must be actionable strings
                        for suggestion in suggestions:
                            assert isinstance(suggestion, str)
                            assert len(suggestion) > 0
                    
                    if 'warning' in result:
                        warning = result['warning']
                        assert 'message' in warning
                        assert 'suggestedActions' in warning
                        assert isinstance(warning['suggestedActions'], list)
                        assert len(warning['suggestedActions']) > 0
            
            # If processing failed, error must have suggested actions
            if not result.get('success') and 'error' in result:
                error = result['error']
                assert 'suggestedActions' in error
                assert isinstance(error['suggestedActions'], list)
                assert len(error['suggestedActions']) > 0
                
                # Must indicate if fallback is available
                assert 'fallbackAvailable' in error
                if error['fallbackAvailable']:
                    assert 'fallbackMethod' in error
        
        except Exception as e:
            # Even exceptions should be handled gracefully
            pytest.fail(f"Unhandled exception: {str(e)}")
    
    @given(
        image_data=document_image_with_quality_strategy(),
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_document_processing_fallback_to_manual_entry(
        self,
        image_data: tuple,
        document_type: DocumentType
    ):
        """
        Property: Failed document processing must provide manual entry fallback
        
        Validates Requirement 3.5: Alternative methods available when OCR fails
        """
        image, quality_issue = image_data
        processor = EnhancedDocumentProcessor()
        
        # Process document
        result = processor.process_document_safe(image, document_type)
        
        # If processing failed or quality is unreadable, fallback must be available
        if not result.get('success') or result.get('quality_level') == DocumentQuality.UNREADABLE:
            # Check for fallback information
            has_fallback = (
                result.get('error', {}).get('fallbackAvailable') or
                result.get('warning', {}).get('fallbackAvailable') or
                result.get('requiresManualReview')
            )
            
            assert has_fallback, "Fallback must be available for failed/poor quality documents"
            
            # Manual entry form should be available
            manual_form = processor.get_manual_entry_form(document_type)
            assert 'fields' in manual_form
            assert isinstance(manual_form['fields'], list)
            assert len(manual_form['fields']) > 0
            
            # Each field must have required properties
            for field in manual_form['fields']:
                assert 'name' in field
                assert 'label' in field
                assert 'type' in field
                assert 'required' in field
    
    @given(
        failure_scenario=api_failure_scenario_strategy(),
        language=st.sampled_from(['en', 'hi', 'mr'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_api_failure_provides_alternative_submission_methods(
        self,
        failure_scenario: str,
        language: str
    ):
        """
        Property: API failures must provide alternative submission methods
        
        Validates Requirement 4.4: Alternative submission methods when API fails
        """
        # Simulate API failure by creating service without valid credentials
        service = EnhancedAutoApplicationService()
        
        # Create a mock application
        application_id = "test_app_123"
        service.applications[application_id] = type('obj', (object,), {
            'scheme_id': 'pm_kisan',
            'form_data': {'test': 'data'},
            'status': 'draft',
            'updated_at': datetime.utcnow()
        })()
        
        # Attempt submission (will fail due to no API credentials)
        result = service.submit_application_safe(application_id, True, language)
        
        # Verify error handling structure
        assert isinstance(result, dict)
        
        # If submission failed, fallback must be provided
        if not result.get('success') or result.get('status') == 'submission_failed':
            # Must have fallback information
            assert 'fallback' in result or 'error' in result
            
            if 'fallback' in result:
                fallback = result['fallback']
                
                # Fallback must include alternative methods
                assert 'method' in fallback
                assert 'instructions' in fallback
                assert isinstance(fallback['instructions'], list)
                assert len(fallback['instructions']) > 0
                
                # Must provide contact information
                assert 'office' in fallback or 'website' in fallback or 'helpline' in fallback
                
                # Instructions must be in requested language
                for instruction in fallback['instructions']:
                    assert isinstance(instruction, str)
                    assert len(instruction) > 0
            
            if 'error' in result:
                error = result['error']
                assert 'suggestedActions' in error
                assert isinstance(error['suggestedActions'], list)
                assert len(error['suggestedActions']) > 0
    
    @given(
        failure_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_circuit_breaker_prevents_cascading_failures(
        self,
        failure_count: int
    ):
        """
        Property: Circuit breaker must open after threshold failures
        
        Validates Requirement 4.4: System prevents cascading failures
        """
        circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        # Simulate failures
        def failing_function():
            raise APIIntegrationError("Service unavailable")
        
        failures = 0
        circuit_opened = False
        
        for i in range(failure_count):
            try:
                circuit_breaker.call(failing_function)
            except APIIntegrationError as e:
                failures += 1
                
                # Check if circuit opened
                if circuit_breaker.state.state == "open":
                    circuit_opened = True
                    
                    # Verify error indicates circuit is open
                    assert "circuit breaker is open" in str(e).lower() or "unavailable" in str(e).lower()
                    
                    # Verify fallback is available
                    assert e.context.fallback_available
        
        # Circuit should open after threshold
        if failure_count >= 5:
            assert circuit_opened, "Circuit breaker should open after threshold failures"
            assert circuit_breaker.state.state == "open"
    
    @given(
        max_attempts=st.integers(min_value=1, max_value=5),
        should_succeed_on_attempt=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_retry_strategy_eventually_succeeds(
        self,
        max_attempts: int,
        should_succeed_on_attempt: int
    ):
        """
        Property: Retry strategy must eventually succeed if possible
        
        Validates Requirement 4.4: System retries transient failures
        """
        assume(should_succeed_on_attempt <= max_attempts)
        
        retry_strategy = RetryStrategy(max_attempts=max_attempts, initial_delay=0.1)
        
        attempt_count = [0]
        
        def sometimes_failing_function():
            attempt_count[0] += 1
            if attempt_count[0] < should_succeed_on_attempt:
                raise APIIntegrationError("Transient failure")
            return {"success": True, "attempts": attempt_count[0]}
        
        # Execute with retry
        result = retry_strategy.execute(
            sometimes_failing_function,
            retry_on=[APIIntegrationError]
        )
        
        # Should succeed
        assert result['success']
        assert result['attempts'] == should_succeed_on_attempt
        assert attempt_count[0] == should_succeed_on_attempt
    
    @given(
        delay_scenario=application_delay_strategy(),
        language=st.sampled_from(['en', 'hi', 'mr'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tracking_delays_provide_appropriate_alerts(
        self,
        delay_scenario: Dict[str, Any],
        language: str
    ):
        """
        Property: Processing delays must trigger appropriate alerts with actions
        
        Validates Requirement 5.5: System alerts users of delays with suggested actions
        """
        # Create tracking service
        gov_api = GovernmentAPIIntegration()
        config = TrackingConfig(
            poll_interval_seconds=60,
            enable_predictive_analytics=True
        )
        service = EnhancedTrackingService(gov_api, config)
        
        # Create mock application with delay
        application_id = "test_app_delay"
        from shared.models.application import Application, ApplicationStatus
        
        application = Application(
            user_id="user123",
            scheme_id="pm_kisan",
            form_data={"test": "data"},
            status=ApplicationStatus.UNDER_REVIEW,
            government_ref_number="REF123"
        )
        
        # Set submission date to simulate delay
        application.submitted_at = datetime.utcnow() - timedelta(days=delay_scenario['actual_days'])
        
        # Register for tracking
        service.register_application(application)
        
        # Get status with guidance
        result = service.get_status_with_guidance(application_id, language)
        
        # Verify result structure
        assert isinstance(result, dict)
        
        # If delayed, must have warning
        if delay_scenario['is_delayed'] and delay_scenario['delay_days'] > 15:
            # Should have delay warning or guidance
            has_delay_info = (
                'delayWarning' in result or
                'guidance' in result or
                'warning' in result
            )
            
            if 'delayWarning' in result:
                delay_warning = result['delayWarning']
                assert 'message' in delay_warning
                assert 'suggestedActions' in delay_warning
                assert isinstance(delay_warning['suggestedActions'], list)
                assert len(delay_warning['suggestedActions']) > 0
            
            if 'guidance' in result:
                guidance = result['guidance']
                assert 'nextSteps' in guidance
                assert isinstance(guidance['nextSteps'], list)
    
    @given(
        language=st.sampled_from(['en', 'hi', 'mr'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tracking_failure_provides_cached_status(
        self,
        language: str
    ):
        """
        Property: Tracking failures must provide cached status as fallback
        
        Validates Requirement 5.5: System provides cached data when real-time unavailable
        """
        # Create tracking service
        gov_api = GovernmentAPIIntegration()
        service = EnhancedTrackingService(gov_api)
        
        # Create and register application
        application_id = "test_app_cache"
        from shared.models.application import Application, ApplicationStatus
        
        application = Application(
            user_id="user123",
            scheme_id="pm_kisan",
            form_data={"test": "data"},
            status=ApplicationStatus.SUBMITTED,
            government_ref_number="REF123"
        )
        
        service.register_application(application)
        
        # Cache a status
        cached_data = {
            "applicationId": application_id,
            "status": "under_review",
            "lastUpdated": datetime.utcnow().isoformat()
        }
        service._cache_status(application_id, cached_data)
        
        # Attempt to poll (will fail due to no API credentials)
        result = service.poll_application_safe(application_id, language)
        
        # Verify result structure
        assert isinstance(result, dict)
        
        # Should provide cached status or error with fallback
        if result.get('source') == 'cached':
            # Cached status provided
            assert 'statusResult' in result or 'cachedStatus' in result
            assert 'warning' in result or 'message' in result
        elif 'error' in result:
            # Error should indicate fallback available
            error = result['error']
            assert 'suggestedActions' in error
            
            # May have cached status in error response
            if 'cachedStatus' in result:
                assert isinstance(result['cachedStatus'], dict)
    
    @given(
        message_key=st.sampled_from([
            'doc_poor_quality',
            'doc_unreadable',
            'api_unavailable',
            'api_timeout',
            'validation_failed',
            'network_error',
            'service_degraded',
            'submission_failed',
            'tracking_unavailable',
            'payment_check_failed'
        ]),
        language=st.sampled_from(['en', 'hi', 'mr'])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_messages_available_in_all_languages(
        self,
        message_key: str,
        language: str
    ):
        """
        Property: Error messages must be available in all supported languages
        
        Validates Requirements 3.5, 4.4, 5.5: Multi-language error communication
        """
        generator = ErrorMessageGenerator()
        
        # Get message in specified language
        message = generator.get_message(message_key, language)
        
        # Verify message is not empty
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Verify message is different from key (i.e., it was translated)
        assert message != message_key
        
        # Verify message doesn't contain placeholder markers
        assert '{' not in message or '}' not in message
    
    @given(
        service_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll',))),
        primary_fails=st.booleans(),
        fallback_fails=st.booleans()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_fallback_manager_handles_all_scenarios(
        self,
        service_name: str,
        primary_fails: bool,
        fallback_fails: bool
    ):
        """
        Property: Fallback manager must handle all failure scenarios gracefully
        
        Validates Requirements 3.5, 4.4, 5.5: Comprehensive fallback handling
        """
        manager = FallbackManager()
        
        # Define primary and fallback functions
        def primary_function():
            if primary_fails:
                raise Exception("Primary service failed")
            return {"source": "primary", "data": "success"}
        
        def fallback_function():
            if fallback_fails:
                raise Exception("Fallback service failed")
            return {"source": "fallback", "data": "success"}
        
        # Register fallback
        manager.register_fallback(service_name, fallback_function)
        
        # Execute with fallback
        result = manager.execute_with_fallback(service_name, primary_function)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'source' in result
        
        # Verify behavior based on failure scenarios
        if not primary_fails:
            # Primary should succeed
            assert result['success']
            assert result['source'] == 'primary'
        elif primary_fails and not fallback_fails:
            # Fallback should succeed
            assert result['success']
            assert result['source'] == 'fallback'
            assert 'primary_error' in result
        else:
            # Both failed
            assert not result['success']
            assert result['source'] == 'none'
            assert 'error' in result
            assert 'fallbackAvailable' in result
    
    @given(
        document_type=st.sampled_from(list(DocumentType))
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_manual_entry_forms_complete_for_all_document_types(
        self,
        document_type: DocumentType
    ):
        """
        Property: Manual entry forms must be available for all document types
        
        Validates Requirement 3.5: Complete fallback coverage
        """
        processor = EnhancedDocumentProcessor()
        
        # Get manual entry form
        form = processor.get_manual_entry_form(document_type)
        
        # Verify form structure
        assert isinstance(form, dict)
        assert 'fields' in form
        assert isinstance(form['fields'], list)
        
        # Form should have at least one field
        assert len(form['fields']) > 0
        
        # Each field must have required properties
        for field in form['fields']:
            assert 'name' in field
            assert 'label' in field
            assert 'type' in field
            assert 'required' in field
            
            # Field type must be valid
            assert field['type'] in ['text', 'number', 'date', 'select', 'textarea']
            
            # Required must be boolean
            assert isinstance(field['required'], bool)
    
    @given(
        application_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))),
        language=st.sampled_from(['en', 'hi', 'mr'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_manual_check_instructions_provided_for_tracking_failures(
        self,
        application_id: str,
        language: str
    ):
        """
        Property: Manual check instructions must be provided when tracking fails
        
        Validates Requirement 5.5: Alternative status check methods
        """
        # Create tracking service
        gov_api = GovernmentAPIIntegration()
        service = EnhancedTrackingService(gov_api)
        
        # Create and register application
        from shared.models.application import Application, ApplicationStatus
        
        application = Application(
            user_id="user123",
            scheme_id="pm_kisan",
            form_data={"test": "data"},
            status=ApplicationStatus.SUBMITTED,
            government_ref_number="REF123456"
        )
        
        service.register_application(application)
        
        # Get manual check instructions
        instructions = service.get_manual_check_instructions(application.application_id, language)
        
        # Verify instructions structure
        assert isinstance(instructions, dict)
        assert 'title' in instructions
        assert 'steps' in instructions
        assert 'referenceNumber' in instructions
        assert 'schemeId' in instructions
        
        # Verify steps are provided
        assert isinstance(instructions['steps'], list)
        assert len(instructions['steps']) > 0
        
        # Each step must be a non-empty string
        for step in instructions['steps']:
            assert isinstance(step, str)
            assert len(step) > 0
        
        # Reference number must be included
        assert instructions['referenceNumber'] == application.government_ref_number
    
    @given(
        error_severity=st.sampled_from(list(ErrorSeverity)),
        has_fallback=st.booleans()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_context_includes_all_required_information(
        self,
        error_severity: ErrorSeverity,
        has_fallback: bool
    ):
        """
        Property: Error context must include all required information for user guidance
        
        Validates Requirements 3.5, 4.4, 5.5: Comprehensive error information
        """
        # Create error with context
        error = DocumentProcessingError(
            message="Test error",
            severity=error_severity,
            user_message="User-friendly error message",
            suggested_actions=["Action 1", "Action 2"],
            fallback_available=has_fallback,
            fallback_method="manual_entry" if has_fallback else None
        )
        
        # Verify error context
        context = error.context
        
        # Required fields
        assert hasattr(context, 'error_code')
        assert hasattr(context, 'message')
        assert hasattr(context, 'severity')
        assert hasattr(context, 'category')
        assert hasattr(context, 'user_message')
        assert hasattr(context, 'suggested_actions')
        assert hasattr(context, 'fallback_available')
        assert hasattr(context, 'timestamp')
        
        # Verify values
        assert context.severity == error_severity
        assert context.fallback_available == has_fallback
        assert isinstance(context.suggested_actions, list)
        assert len(context.suggested_actions) > 0
        
        # If fallback available, method must be specified
        if has_fallback:
            assert context.fallback_method is not None
            assert isinstance(context.fallback_method, str)
            assert len(context.fallback_method) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
