"""
Property-Based Tests for Auto-Application Workflow Completeness
Feature: sarvasahay-platform, Property 4: Auto-Application Workflow Completeness

This test validates that for any selected government scheme, the system:
1. Pre-fills forms using profile and document data
2. Presents forms for user review
3. Submits via official APIs upon approval
4. Provides reference numbers with confirmation details

Validates: Requirements 4.1, 4.2, 4.3, 4.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.auto_application_service import AutoApplicationService
from services.form_template_manager import FormTemplateManager
from shared.models.application import ApplicationStatus


# Strategy for generating valid user profiles for application testing
@st.composite
def application_user_profile_strategy(draw):
    """Generate valid user profiles for application workflow"""
    aadhaar = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)])
    
    pan_letters1 = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(5)])
    pan_digits = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(4)])
    pan_letter2 = draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    pan = f"{pan_letters1}{pan_digits}{pan_letter2}"
    
    ifsc_letters = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(4)])
    ifsc_suffix = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')) for _ in range(6)])
    ifsc = f"{ifsc_letters}0{ifsc_suffix}"
    
    return {
        'demographics': {
            'name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'age': draw(st.integers(min_value=18, max_value=100)),
            'gender': draw(st.sampled_from(['male', 'female', 'other'])),
            'caste': draw(st.sampled_from(['general', 'obc', 'sc', 'st'])),
            'maritalStatus': draw(st.sampled_from(['single', 'married', 'widowed', 'divorced']))
        },
        'economic': {
            'annualIncome': draw(st.integers(min_value=0, max_value=1000000)),
            'landOwnership': draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)),
            'employmentStatus': draw(st.sampled_from(['farmer', 'laborer', 'self_employed', 'unemployed']))
        },
        'location': {
            'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat', 'Uttar Pradesh'])),
            'district': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'block': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'village': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'pincode': draw(st.from_regex(r'^\d{6}$', fullmatch=True))
        },
        'family': {
            'size': draw(st.integers(min_value=1, max_value=15)),
            'dependents': draw(st.integers(min_value=0, max_value=10)),
            'elderlyMembers': draw(st.integers(min_value=0, max_value=5)),
            'children': draw(st.integers(min_value=0, max_value=8))
        },
        'documents': {
            'aadhaar': aadhaar,
            'pan': pan,
            'bankAccount': draw(st.text(min_size=9, max_size=18, alphabet=st.characters(whitelist_categories=('Nd',)))),
            'bankIfsc': ifsc,
            'landRecords': draw(st.text(min_size=5, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))),
            'rationCard': draw(st.text(min_size=5, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))))
        }
    }


# Strategy for generating document data
@st.composite
def document_data_strategy(draw):
    """Generate document data for applications"""
    return {
        'documentIds': draw(st.lists(
            st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-')),
            min_size=1,
            max_size=5
        )),
        'documents': {
            'aadhaar': ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)]),
            'bankAccount': draw(st.text(min_size=9, max_size=18, alphabet=st.characters(whitelist_categories=('Nd',)))),
            'bankIfsc': draw(st.from_regex(r'^[A-Z]{4}0[A-Z0-9]{6}$', fullmatch=True))
        }
    }


class TestAutoApplicationWorkflowProperty:
    """
    Property 4: Auto-Application Workflow Completeness
    
    For any selected government scheme, the system should:
    1. Pre-fill forms using profile and document data
    2. Present forms for user review
    3. Submit via official APIs upon approval
    4. Provide reference numbers with confirmation details
    """
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_form_auto_population_completeness(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Forms must be auto-populated using profile and document data
        
        Validates Requirement 4.1: Pre-fill all required forms using profile and document data
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application with auto-population
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        # Verify application was created
        assert 'applicationId' in result
        assert result['schemeId'] == scheme_id
        assert result['status'] == 'draft'
        
        # Verify form data was populated
        assert 'formData' in result
        form_data = result['formData']
        
        # Verify key fields were auto-populated from profile
        if 'applicant_name' in form_data:
            assert form_data['applicant_name'] is not None
        
        if 'age' in form_data:
            assert form_data['age'] == user_profile['demographics']['age']
        
        if 'gender' in form_data:
            assert form_data['gender'] == user_profile['demographics']['gender']
        
        if 'land_ownership' in form_data:
            assert form_data['land_ownership'] == user_profile['economic']['landOwnership']
        
        # Verify document data was populated (from either profile or document_data)
        # The system prioritizes document_data over profile for document fields
        if 'aadhaar_number' in form_data:
            expected_aadhaar = document_data.get('documents', {}).get('aadhaar') or user_profile['documents']['aadhaar']
            assert form_data['aadhaar_number'] == expected_aadhaar
        
        if 'bank_account' in form_data:
            expected_bank = document_data.get('documents', {}).get('bankAccount') or user_profile['documents']['bankAccount']
            assert form_data['bank_account'] == expected_bank
        
        if 'bank_ifsc' in form_data:
            expected_ifsc = document_data.get('documents', {}).get('bankIfsc') or user_profile['documents']['bankIfsc']
            assert form_data['bank_ifsc'] == expected_ifsc
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_application_preview_generation(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: System must present forms for user review before submission
        
        Validates Requirement 4.2: Present forms for user review and approval
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Generate preview
        preview = service.preview_application(application_id)
        
        # Verify preview structure
        assert 'applicationId' in preview
        assert preview['applicationId'] == application_id
        assert 'schemeId' in preview
        assert 'schemeName' in preview
        assert 'sections' in preview
        assert isinstance(preview['sections'], list)
        
        # Verify sections contain field data
        for section in preview['sections']:
            assert 'title' in section
            assert 'fields' in section
            assert isinstance(section['fields'], list)
            
            for field in section['fields']:
                assert 'label' in field
                assert 'value' in field
                assert 'fieldType' in field
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_form_validation_before_submission(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Forms must be validated before submission
        
        Validates Requirement 4.2: Validation ensures data quality
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Validate application
        validation = service.validate_application(application_id)
        
        # Verify validation structure
        assert 'isValid' in validation
        assert isinstance(validation['isValid'], bool)
        assert 'errors' in validation
        assert isinstance(validation['errors'], list)
        assert 'warnings' in validation
        assert isinstance(validation['warnings'], list)
        assert 'validatedAt' in validation
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_application_submission_workflow(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Applications must be submitted via official APIs with proper handling
        
        Validates Requirement 4.3: Submit forms directly to government portals via APIs
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Submit application
        submission_result = service.submit_application(
            application_id=application_id,
            user_approval=True
        )
        
        # Verify submission result structure
        assert 'applicationId' in submission_result
        assert submission_result['applicationId'] == application_id
        assert 'status' in submission_result
        
        # Status should be either submitted or submission_failed
        assert submission_result['status'] in ['submitted', 'submission_failed']
        
        # If submitted successfully, should have reference number
        if submission_result['status'] == 'submitted':
            assert 'governmentRefNumber' in submission_result
            assert submission_result['governmentRefNumber'] is not None
            assert 'submittedAt' in submission_result
            assert 'message' in submission_result
        
        # If submission failed, should have fallback information
        if submission_result['status'] == 'submission_failed':
            assert 'error' in submission_result
            assert 'fallbackMethod' in submission_result
            assert 'instructions' in submission_result
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_reference_number_generation(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Submitted applications must receive reference numbers
        
        Validates Requirement 4.5: Provide reference numbers and confirmation details
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create and submit application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        submission_result = service.submit_application(application_id, user_approval=True)
        
        # If submission was successful, verify reference number
        if submission_result['status'] == 'submitted':
            # Get application details
            app_details = service.get_application(application_id)
            
            # Verify reference number is stored
            assert 'governmentRefNumber' in app_details
            assert app_details['governmentRefNumber'] is not None
            assert len(app_details['governmentRefNumber']) > 0
            
            # Verify submission timestamp
            assert 'submittedAt' in app_details
            assert app_details['submittedAt'] is not None
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_application_status_tracking(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Application status must be tracked throughout workflow
        
        Validates Requirement 4.5: Maintain status history and tracking
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Get application details
        app_details = service.get_application(application_id)
        
        # Verify status tracking
        assert 'status' in app_details
        assert app_details['status'] in ['draft', 'submitted', 'under_review', 'approved', 'rejected']
        
        # Verify status history
        assert 'statusHistory' in app_details
        assert isinstance(app_details['statusHistory'], list)
        assert len(app_details['statusHistory']) > 0
        
        # Verify each status history entry
        for history_entry in app_details['statusHistory']:
            assert 'status' in history_entry
            assert 'timestamp' in history_entry
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy(),
        form_updates=st.dictionaries(
            keys=st.sampled_from(['applicant_name', 'land_ownership', 'village']),
            values=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' .'))
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_application_update_before_submission(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any],
        form_updates: Dict[str, Any]
    ):
        """
        Property: Draft applications must be updatable before submission
        
        Validates Requirement 4.2: Allow user review and modification
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        assume(len(form_updates) > 0)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Update application
        update_result = service.update_application(
            application_id=application_id,
            form_data=form_updates
        )
        
        # Verify update was successful
        assert 'applicationId' in update_result
        assert update_result['applicationId'] == application_id
        assert 'formData' in update_result
        assert 'updatedAt' in update_result
        
        # Verify updates were applied
        for key, value in form_updates.items():
            if key in update_result['formData']:
                assert update_result['formData'][key] == value
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_approval_requirement(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Applications must not be submitted without user approval
        
        Validates Requirement 4.2: User approval required for submission
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Attempt submission without approval
        with pytest.raises(ValueError) as exc_info:
            service.submit_application(application_id, user_approval=False)
        
        assert "approval required" in str(exc_info.value).lower()
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_fallback_mechanism_on_api_failure(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: System must provide fallback methods when API submission fails
        
        Validates Requirement 4.4: Provide alternative submission methods on API failure
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = result['applicationId']
        
        # Submit application
        submission_result = service.submit_application(application_id, user_approval=True)
        
        # If submission failed, verify fallback information is provided
        if submission_result['status'] == 'submission_failed':
            assert 'fallbackMethod' in submission_result
            assert submission_result['fallbackMethod'] in ['manual', 'offline', 'retry']
            
            assert 'instructions' in submission_result
            assert isinstance(submission_result['instructions'], str)
            assert len(submission_result['instructions']) > 0
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_bulk_application_creation(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: System must support creating multiple applications at once
        
        Validates Requirement 4.1: Efficient application creation for multiple schemes
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_ids = ["PM-KISAN"]  # Only one scheme available in test
        
        # Create multiple applications
        results = service.bulk_create_applications(
            user_id=user_id,
            scheme_ids=scheme_ids,
            user_profile=user_profile,
            document_data=document_data
        )
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == len(scheme_ids)
        
        for result in results:
            if 'error' not in result:
                assert 'applicationId' in result
                assert 'schemeId' in result
                assert 'formData' in result
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_application_retrieval_consistency(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Retrieved applications must match created applications
        
        Validates Requirement 4.5: Data consistency throughout workflow
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-123"
        scheme_id = "PM-KISAN"
        
        # Create application
        create_result = service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        application_id = create_result['applicationId']
        
        # Retrieve application
        retrieved = service.get_application(application_id)
        
        # Verify consistency
        assert retrieved['applicationId'] == application_id
        assert retrieved['userId'] == user_id
        assert retrieved['schemeId'] == scheme_id
        assert retrieved['formData'] == create_result['formData']
    
    @given(
        user_profile=application_user_profile_strategy(),
        document_data=document_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_user_application_listing(
        self,
        user_profile: Dict[str, Any],
        document_data: Dict[str, Any]
    ):
        """
        Property: Users must be able to list all their applications
        
        Validates Requirement 4.5: Application management and tracking
        """
        # Ensure family constraints are valid
        if user_profile['family']['dependents'] >= user_profile['family']['size']:
            user_profile['family']['dependents'] = max(0, user_profile['family']['size'] - 1)
        
        service = AutoApplicationService()
        user_id = "test-user-456"
        scheme_id = "PM-KISAN"
        
        # Create application
        service.create_application(
            user_id=user_id,
            scheme_id=scheme_id,
            user_profile=user_profile,
            document_data=document_data
        )
        
        # List user applications
        applications = service.list_user_applications(user_id)
        
        # Verify listing
        assert isinstance(applications, list)
        assert len(applications) > 0
        
        for app in applications:
            assert 'applicationId' in app
            assert 'schemeId' in app
            assert 'status' in app
            assert 'createdAt' in app
    
    @given(
        user_profile=application_user_profile_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_form_template_availability(
        self,
        user_profile: Dict[str, Any]
    ):
        """
        Property: Form templates must be available for all supported schemes
        
        Validates Requirement 4.1: Template management for 30+ schemes
        """
        form_manager = FormTemplateManager()
        
        # List available templates
        templates = form_manager.list_templates()
        
        # Verify templates exist
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Verify template structure
        for template in templates:
            assert 'templateId' in template
            assert 'schemeId' in template
            assert 'schemeName' in template
            assert 'version' in template
            assert 'fieldCount' in template
            assert template['fieldCount'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
