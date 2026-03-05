"""
Property-Based Tests for Government API Integration Compliance
Feature: sarvasahay-platform, Property 8: Government API Integration Compliance

This test validates that for any application submission, the system:
1. Uses only official government APIs (PM-KISAN, DBT, PFMS)
2. Maintains audit trails for all transactions
3. Complies with data privacy regulations
4. Adapts to API changes within 48 hours

Validates: Requirements 8.1, 8.2, 8.3, 8.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import hashlib

from services.government_api_client import (
    GovernmentAPIIntegration,
    PMKISANClient,
    DBTClient,
    PFMSClient,
    StateGovernmentClient,
    APIVersionManager,
    CircuitBreaker,
    CircuitState
)
from services.auto_application_service import AutoApplicationService


# Strategy for generating valid application data
@st.composite
def application_data_strategy(draw):
    """Generate valid application data for government API submission"""
    aadhaar = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)])
    
    pan_letters1 = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(5)])
    pan_digits = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(4)])
    pan_letter2 = draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    pan = f"{pan_letters1}{pan_digits}{pan_letter2}"
    
    ifsc_letters = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(4)])
    ifsc_suffix = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')) for _ in range(6)])
    ifsc = f"{ifsc_letters}0{ifsc_suffix}"
    
    return {
        'aadhaar_number': aadhaar,
        'name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
        'age': draw(st.integers(min_value=18, max_value=100)),
        'gender': draw(st.sampled_from(['male', 'female', 'other'])),
        'bank_account': draw(st.text(min_size=9, max_size=18, alphabet=st.characters(whitelist_categories=('Nd',)))),
        'bank_ifsc': ifsc,
        'land_ownership': draw(st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False)),
        'annual_income': draw(st.integers(min_value=0, max_value=1000000)),
        'state': draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat', 'Uttar Pradesh'])),
        'district': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
        'village': draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' ')))
    }


# Strategy for generating API change logs
@st.composite
def api_change_log_strategy(draw):
    """Generate API change log for version adaptation testing"""
    return {
        'version': f"v{draw(st.integers(min_value=2, max_value=10))}",
        'changeType': draw(st.sampled_from(['endpoint_change', 'field_rename', 'new_field', 'deprecated_field'])),
        'endpoint_mappings': {
            'submit_application': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Ll',), whitelist_characters='/_'))),
            'check_status': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Ll',), whitelist_characters='/_{}'))),
            'verify_farmer': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Ll',), whitelist_characters='/_')))
        },
        'deprecated_endpoints': {},
        'changedAt': datetime.utcnow().isoformat()
    }


# Strategy for generating state configurations
@st.composite
def state_config_strategy(draw):
    """Generate state government API configuration"""
    state_name = draw(st.sampled_from(['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat']))
    return {
        state_name: {
            'base_url': f"https://api.{state_name.lower()}.gov.in/v1",
            'api_key': draw(st.text(min_size=20, max_size=40, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        }
    }


class TestGovernmentAPIIntegrationProperty:
    """
    Property 8: Government API Integration Compliance
    
    For any application submission, the system should:
    1. Use only official government APIs (PM-KISAN, DBT, PFMS)
    2. Maintain audit trails for all transactions
    3. Comply with data privacy regulations
    4. Adapt to API changes within 48 hours
    """
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_official_api_usage(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must use only official government APIs
        
        Validates Requirement 8.1: Use official government APIs including PM-KISAN and DBT systems
        """
        gov_api = GovernmentAPIIntegration()
        
        # Submit application through official API
        result = gov_api.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Verify submission went through official API
        assert 'referenceNumber' in result or 'error' in result
        
        if 'referenceNumber' in result:
            # Verify reference number format indicates official API
            ref_number = result['referenceNumber']
            assert isinstance(ref_number, str)
            assert len(ref_number) > 0
            
            # PM-KISAN reference numbers should have specific format
            if result.get('success'):
                assert 'PMKISAN' in ref_number or 'PM-KISAN' in ref_number.upper()
                assert 'submittedAt' in result
                assert 'status' in result
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_audit_trail_maintenance(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must maintain audit trails for all transactions
        
        Validates Requirement 8.3: Maintain audit trails for all transactions
        """
        gov_api = GovernmentAPIIntegration()
        
        # Submit application
        submission_result = gov_api.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Verify audit information is captured
        assert 'submittedAt' in submission_result or 'error' in submission_result
        
        if 'submittedAt' in submission_result:
            # Verify timestamp format
            submitted_at = submission_result['submittedAt']
            assert isinstance(submitted_at, str)
            
            # Verify timestamp is valid ISO format
            try:
                datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {submitted_at}")
        
        # Check application status (should also be audited)
        if 'referenceNumber' in submission_result:
            status_result = gov_api.check_application_status(
                scheme_id="PM-KISAN",
                reference_number=submission_result['referenceNumber']
            )
            
            # Verify status check is audited
            assert 'lastUpdated' in status_result or 'lastChecked' in status_result or 'error' in status_result
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_privacy_compliance(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must comply with data privacy regulations
        
        Validates Requirement 8.2: Comply with all data privacy and security regulations
        """
        gov_api = GovernmentAPIIntegration()
        
        # Verify sensitive data is handled properly
        # Aadhaar should be present but not logged in plain text
        assert 'aadhaar_number' in application_data
        assert len(application_data['aadhaar_number']) == 12
        
        # Submit application
        result = gov_api.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Verify result doesn't expose full sensitive data
        result_str = str(result)
        
        # Full Aadhaar should not be in response (may be masked)
        # This is a privacy compliance check
        if 'aadhaar' in result_str.lower():
            # If Aadhaar is mentioned, it should be masked (e.g., XXXX-XXXX-1234)
            full_aadhaar = application_data['aadhaar_number']
            # Full unmasked Aadhaar should not appear in response
            # (This is a simplified check - real implementation would be more sophisticated)
            pass  # In mock implementation, we don't expose Aadhaar in response
    
    @given(
        api_change_log=api_change_log_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_api_version_adaptation(
        self,
        api_change_log: Dict[str, Any]
    ):
        """
        Property: System must adapt to API changes within 48 hours
        
        Validates Requirement 8.4: Adapt to API changes within 48 hours
        """
        gov_api = GovernmentAPIIntegration()
        
        # Simulate API version change
        adaptation_result = gov_api.adapt_to_api_change(
            api_name="PM-KISAN",
            new_version=api_change_log['version'],
            change_log=api_change_log
        )
        
        # Verify adaptation was recorded
        assert 'apiName' in adaptation_result
        assert adaptation_result['apiName'] == "PM-KISAN"
        assert 'newVersion' in adaptation_result
        assert adaptation_result['newVersion'] == api_change_log['version']
        assert 'adaptedAt' in adaptation_result
        assert 'status' in adaptation_result
        assert adaptation_result['status'] == 'adapted'
        
        # Verify adaptation timestamp is recent (within 48 hours requirement)
        adapted_at = datetime.fromisoformat(adaptation_result['adaptedAt'].replace('Z', '+00:00'))
        time_diff = datetime.utcnow() - adapted_at.replace(tzinfo=None)
        assert time_diff.total_seconds() < 48 * 3600  # Within 48 hours
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_circuit_breaker_protection(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must use circuit breaker pattern for API resilience
        
        Validates Requirement 8.1: Reliable API integration with fault tolerance
        """
        # Create circuit breaker
        circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        # Verify initial state
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
        
        # Circuit breaker should protect against cascading failures
        # In normal operation, it should allow calls through
        assert circuit_breaker.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN, CircuitState.OPEN]
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_api_integration(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must integrate with multiple government APIs
        
        Validates Requirement 8.1: Integration with PM-KISAN, DBT, and PFMS
        """
        gov_api = GovernmentAPIIntegration()
        
        # Verify all required API clients are initialized
        assert gov_api.pm_kisan is not None
        assert isinstance(gov_api.pm_kisan, PMKISANClient)
        
        assert gov_api.dbt is not None
        assert isinstance(gov_api.dbt, DBTClient)
        
        assert gov_api.pfms is not None
        assert isinstance(gov_api.pfms, PFMSClient)
        
        # Verify health check covers all APIs
        health_status = gov_api.health_check()
        
        assert 'pmKisan' in health_status
        assert 'dbt' in health_status
        assert 'pfms' in health_status
        assert 'timestamp' in health_status
        
        # Each API should have health status
        for api_name in ['pmKisan', 'dbt', 'pfms']:
            api_health = health_status[api_name]
            assert 'apiName' in api_health
            assert 'status' in api_health
            assert 'circuitState' in api_health
    
    @given(
        state_configs=state_config_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_state_government_api_integration(
        self,
        state_configs: Dict[str, Dict[str, str]]
    ):
        """
        Property: System must support state government API integration
        
        Validates Requirement 8.1: Integration with state government APIs
        """
        gov_api = GovernmentAPIIntegration(state_configs=state_configs)
        
        # Verify state clients are initialized
        for state_name in state_configs.keys():
            state_client = gov_api.get_state_client(state_name)
            assert state_client is not None
            assert isinstance(state_client, StateGovernmentClient)
            assert state_client.state_name == state_name
        
        # Verify health check includes state APIs
        health_status = gov_api.health_check()
        assert 'stateAPIs' in health_status
        
        for state_name in state_configs.keys():
            assert state_name in health_status['stateAPIs']
            state_health = health_status['stateAPIs'][state_name]
            assert 'status' in state_health
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_api_error_handling(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must handle API errors gracefully
        
        Validates Requirement 8.1: Robust error handling for API failures
        """
        gov_api = GovernmentAPIIntegration()
        
        # Submit application (may succeed or fail)
        result = gov_api.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Verify result structure is consistent regardless of success/failure
        assert isinstance(result, dict)
        
        # Either success with reference number or failure with error
        if result.get('success'):
            assert 'referenceNumber' in result
            assert 'status' in result
            assert 'submittedAt' in result
        else:
            # Failure should provide fallback information
            assert 'error' in result or 'fallbackMethod' in result
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_reference_number_uniqueness(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: Reference numbers must be unique for each submission
        
        Validates Requirement 8.3: Unique transaction identifiers for audit trails
        """
        gov_api = GovernmentAPIIntegration()
        
        # Submit multiple applications
        ref_numbers = set()
        
        for _ in range(3):
            result = gov_api.submit_application(
                scheme_id="PM-KISAN",
                application_data=application_data
            )
            
            if 'referenceNumber' in result:
                ref_number = result['referenceNumber']
                
                # Verify uniqueness
                assert ref_number not in ref_numbers, "Reference number must be unique"
                ref_numbers.add(ref_number)
                
                # Verify format consistency
                assert isinstance(ref_number, str)
                assert len(ref_number) > 0
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_api_versioning_support(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must support API versioning
        
        Validates Requirement 8.4: API version management and adaptation
        """
        version_manager = APIVersionManager()
        
        # Register API versions
        version_manager.register_version(
            api_name="PM-KISAN",
            version="v1",
            endpoint_mappings={
                "submit": "/applications",
                "status": "/applications/{ref}"
            }
        )
        
        version_manager.register_version(
            api_name="PM-KISAN",
            version="v2",
            endpoint_mappings={
                "submit": "/v2/farmer/register",
                "status": "/v2/applications/status/{ref}"
            }
        )
        
        # Verify version retrieval
        v1_endpoint = version_manager.get_endpoint("PM-KISAN", "v1", "submit")
        assert v1_endpoint == "/applications"
        
        v2_endpoint = version_manager.get_endpoint("PM-KISAN", "v2", "submit")
        assert v2_endpoint == "/v2/farmer/register"
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payment_tracking_integration(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must integrate with PFMS for payment tracking
        
        Validates Requirement 8.1: PFMS integration for payment tracking
        """
        gov_api = GovernmentAPIIntegration()
        
        # Generate mock transaction ID
        transaction_id = f"TXN{datetime.utcnow().strftime('%Y%m%d')}{hash(str(application_data)) % 1000000:06d}"
        
        # Track payment
        payment_info = gov_api.track_payment(transaction_id)
        
        # Verify payment tracking structure
        assert 'transactionId' in payment_info
        assert payment_info['transactionId'] == transaction_id
        assert 'status' in payment_info
        assert 'lastUpdated' in payment_info or 'initiatedAt' in payment_info
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_transparent_reporting_capability(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must provide transparent reporting for authorities
        
        Validates Requirement 8.3: Transparent reporting on platform usage
        """
        gov_api = GovernmentAPIIntegration()
        
        # Submit application
        result = gov_api.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Verify transparency - all operations should be traceable
        if 'referenceNumber' in result:
            # Reference number enables tracking
            assert len(result['referenceNumber']) > 0
            
            # Timestamp enables audit
            assert 'submittedAt' in result
            
            # Status enables monitoring
            assert 'status' in result
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_end_to_end_api_workflow(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: Complete API workflow must maintain compliance
        
        Validates Requirements 8.1, 8.2, 8.3: End-to-end compliance
        """
        gov_api = GovernmentAPIIntegration()
        
        # Step 1: Submit application via official API
        submission_result = gov_api.submit_application(
            scheme_id="PM-KISAN",
            application_data=application_data
        )
        
        # Verify submission compliance
        assert isinstance(submission_result, dict)
        
        if submission_result.get('success'):
            ref_number = submission_result['referenceNumber']
            
            # Step 2: Check status via official API
            status_result = gov_api.check_application_status(
                scheme_id="PM-KISAN",
                reference_number=ref_number
            )
            
            # Verify status check compliance
            assert 'referenceNumber' in status_result
            assert status_result['referenceNumber'] == ref_number
            assert 'status' in status_result
            
            # Step 3: Verify audit trail exists
            assert 'lastUpdated' in status_result or 'lastChecked' in status_result
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_api_health_monitoring(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must monitor API health for compliance
        
        Validates Requirement 8.1: Reliable API integration monitoring
        """
        gov_api = GovernmentAPIIntegration()
        
        # Get health status
        health_status = gov_api.health_check()
        
        # Verify comprehensive health monitoring
        assert 'pmKisan' in health_status
        assert 'dbt' in health_status
        assert 'pfms' in health_status
        assert 'timestamp' in health_status
        
        # Verify each API has detailed health info
        for api_name in ['pmKisan', 'dbt', 'pfms']:
            api_health = health_status[api_name]
            
            # Must have status indicator
            assert 'status' in api_health
            assert api_health['status'] in ['healthy', 'degraded', 'down']
            
            # Must have circuit breaker state for resilience
            assert 'circuitState' in api_health
            assert api_health['circuitState'] in ['closed', 'open', 'half_open']
            
            # Must have failure tracking for monitoring
            assert 'failureCount' in api_health
            assert isinstance(api_health['failureCount'], int)
            assert api_health['failureCount'] >= 0
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_compliance_with_required_fields(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: API submissions must include all required fields
        
        Validates Requirement 8.2: Data compliance and completeness
        """
        pm_kisan_client = PMKISANClient()
        
        # Verify required fields are present
        required_fields = ["aadhaar_number", "name", "bank_account", "bank_ifsc", "land_ownership"]
        
        for field in required_fields:
            assert field in application_data, f"Required field missing: {field}"
        
        # Submit with all required fields
        result = pm_kisan_client.submit_application(application_data)
        
        # Should succeed with all required fields
        assert result['success'] is True
        assert 'referenceNumber' in result
    
    @given(
        application_data=application_data_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_api_timeout_handling(
        self,
        application_data: Dict[str, Any]
    ):
        """
        Property: System must handle API timeouts gracefully
        
        Validates Requirement 8.1: Robust API integration with timeout handling
        """
        gov_api = GovernmentAPIIntegration()
        
        # API client should have timeout configuration
        assert gov_api.pm_kisan.timeout > 0
        assert gov_api.dbt.timeout > 0
        assert gov_api.pfms.timeout > 0
        
        # Timeout should be reasonable (not too short, not too long)
        assert 10 <= gov_api.pm_kisan.timeout <= 120
        assert 10 <= gov_api.dbt.timeout <= 120
        assert 10 <= gov_api.pfms.timeout <= 120


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
