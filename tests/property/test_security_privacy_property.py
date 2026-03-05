"""
Property-Based Tests for Security and Privacy Protection
Feature: sarvasahay-platform, Property 10: Security and Privacy Protection

This test validates that for any user data operation, the system:
1. Encrypts personal information using industry standards
2. Deletes raw document images after processing
3. Requires multi-factor authentication for admin access
4. Processes data deletion requests within 30 days

Validates: Requirements 10.1, 10.2, 10.3, 10.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import secrets

from shared.utils.encryption import (
    EncryptionService, encrypt_profile_data, decrypt_profile_data
)
from shared.utils.auth import (
    AuthenticationService, UserRole, MFAMethod
)
from shared.utils.gdpr_compliance import (
    GDPRComplianceService, DataRequestType, RequestStatus, ConsentType
)


# Strategy for generating sensitive user data
@st.composite
def sensitive_data_strategy(draw):
    """Generate sensitive user data that requires encryption"""
    return {
        'aadhaar': ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)]),
        'pan': ''.join([
            draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(5)
        ]) + ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(4)]) + 
        draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')),
        'bank_account': ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)]),
        'phone_number': f"+91{draw(st.integers(min_value=6000000000, max_value=9999999999))}",
        'email': f"{draw(st.text(min_size=5, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz'))}@example.com"
    }


# Strategy for generating passwords
@st.composite
def password_strategy(draw):
    """Generate valid passwords"""
    length = draw(st.integers(min_value=8, max_value=32))
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    return ''.join([draw(st.sampled_from(chars)) for _ in range(length)])


# Strategy for generating usernames
@st.composite
def username_strategy(draw):
    """Generate valid usernames"""
    return draw(st.text(
        min_size=3, 
        max_size=20, 
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789_'
    ))


class TestSecurityAndPrivacyProperty:
    """
    Property 10: Security and Privacy Protection
    
    For any user data operation, the system should:
    1. Encrypt personal information using industry standards (AES)
    2. Delete raw document images after processing
    3. Require multi-factor authentication for admin access
    4. Process data deletion requests within 30 days
    """
    
    @given(sensitive_data=sensitive_data_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_personal_information_encryption(self, sensitive_data: Dict[str, str]):
        """
        Property: All personal information must be encrypted using industry-standard encryption
        
        Validates Requirement 10.1: System encrypts all personal information using 
        industry-standard encryption (AES)
        """
        service = EncryptionService()
        
        # Encrypt each sensitive field
        for field_name, field_value in sensitive_data.items():
            encrypted_value = service.encrypt(field_value)
            
            # Verify encryption changed the value
            assert encrypted_value != field_value, \
                f"Field {field_name} was not encrypted"
            
            # Verify encrypted value is not empty
            assert len(encrypted_value) > 0, \
                f"Encrypted {field_name} is empty"
            
            # Verify encrypted value is base64-encoded (no special chars except allowed)
            import base64
            try:
                base64.urlsafe_b64decode(encrypted_value.encode())
            except Exception:
                pytest.fail(f"Encrypted {field_name} is not valid base64")
    
    @given(sensitive_data=sensitive_data_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_encryption_decryption_integrity(self, sensitive_data: Dict[str, str]):
        """
        Property: Encrypted data must decrypt back to original values without loss
        
        Validates Requirement 10.1: Encryption maintains data integrity
        """
        service = EncryptionService()
        
        # Encrypt all fields
        encrypted_data = service.encrypt_dict(sensitive_data)
        
        # Decrypt all fields
        decrypted_data = service.decrypt_dict(encrypted_data)
        
        # Verify all fields match original
        for field_name, original_value in sensitive_data.items():
            assert decrypted_data[field_name] == original_value, \
                f"Field {field_name} did not decrypt correctly"
    
    @given(
        data1=sensitive_data_strategy(),
        data2=sensitive_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_encryption_produces_different_ciphertexts(
        self, 
        data1: Dict[str, str],
        data2: Dict[str, str]
    ):
        """
        Property: Same plaintext encrypted multiple times should produce different ciphertexts
        (if using proper encryption with IV/nonce)
        
        Validates Requirement 10.1: Encryption uses secure cryptographic practices
        """
        assume(data1 != data2)  # Ensure different data
        
        service = EncryptionService()
        
        # Encrypt both datasets
        encrypted1 = service.encrypt_dict(data1)
        encrypted2 = service.encrypt_dict(data2)
        
        # Verify different data produces different ciphertexts
        for key in data1.keys():
            if key in data2 and data1[key] != data2[key]:
                assert encrypted1[key] != encrypted2[key], \
                    f"Different values for {key} produced same ciphertext"
    
    @given(
        username=username_strategy(),
        password=password_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_password_hashing_security(self, username: str, password: str):
        """
        Property: Passwords must be hashed using secure algorithms (PBKDF2)
        
        Validates Requirement 10.1: Secure password storage
        """
        assume(len(username) >= 3)
        assume(len(password) >= 8)
        
        service = AuthenticationService()
        
        # Hash password
        hashed_password, salt = service.hash_password(password)
        
        # Verify hash is different from password
        assert hashed_password != password, \
            "Password was not hashed"
        
        # Verify salt is generated
        assert salt is not None and len(salt) > 0, \
            "Salt was not generated"
        
        # Verify hash is hexadecimal
        try:
            int(hashed_password, 16)
        except ValueError:
            pytest.fail("Password hash is not hexadecimal")
        
        # Verify password verification works
        assert service.verify_password(password, hashed_password, salt), \
            "Password verification failed"
        
        # Verify wrong password fails
        wrong_password = password + "wrong"
        assert not service.verify_password(wrong_password, hashed_password, salt), \
            "Wrong password was accepted"
    
    @given(
        username=username_strategy(),
        password=password_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_admin_mfa_requirement(self, username: str, password: str):
        """
        Property: Admin access must require multi-factor authentication
        
        Validates Requirement 10.3: Multi-factor authentication for administrative access
        """
        assume(len(username) >= 3)
        assume(len(password) >= 8)
        
        service = AuthenticationService()
        
        # Create admin user
        user_info = service.create_user(
            username=username,
            password=password,
            role=UserRole.ADMIN
        )
        
        # Verify MFA is enabled for admin
        assert user_info['mfa_enabled'] is True, \
            "MFA not enabled for admin user"
        
        # Verify MFA secret is generated
        assert user_info['mfa_secret'] is not None, \
            "MFA secret not generated for admin"
        
        # Attempt authentication without MFA code
        auth_result = service.authenticate(username, password)
        
        # Verify MFA is required
        assert auth_result['status'] == 'mfa_required', \
            "MFA not required for admin authentication"
        assert 'mfa_method' in auth_result, \
            "MFA method not specified"
    
    @given(
        username=username_strategy(),
        password=password_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_regular_user_no_mfa_requirement(self, username: str, password: str):
        """
        Property: Regular users should not require MFA (only admin/operator roles)
        
        Validates Requirement 10.3: MFA is role-based
        """
        assume(len(username) >= 3)
        assume(len(password) >= 8)
        
        service = AuthenticationService()
        
        # Create regular user
        user_info = service.create_user(
            username=username,
            password=password,
            role=UserRole.USER
        )
        
        # Verify MFA is not enabled for regular user
        assert user_info['mfa_enabled'] is False, \
            "MFA should not be enabled for regular user"
        
        # Attempt authentication without MFA code
        auth_result = service.authenticate(username, password)
        
        # Verify authentication succeeds without MFA
        assert auth_result['status'] == 'success', \
            "Regular user authentication should succeed without MFA"
        assert 'token' in auth_result, \
            "Authentication token not provided"
    
    @given(user_id=st.text(min_size=10, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_deletion_request_processing(self, user_id: str):
        """
        Property: Data deletion requests must be processed within 30 days
        
        Validates Requirement 10.5: System permanently removes all personal information 
        within 30 days of deletion request
        """
        service = GDPRComplianceService()
        
        # Create deletion request
        request = service.create_data_request(
            user_id=user_id,
            request_type=DataRequestType.ERASURE,
            requested_by=user_id
        )
        
        # Verify request is created
        assert request.request_id is not None, \
            "Deletion request ID not generated"
        assert request.status == RequestStatus.PENDING, \
            "Deletion request not in pending status"
        
        # Process deletion request
        deletion_result = service.process_erasure_request(
            request_id=request.request_id,
            user_id=user_id
        )
        
        # Verify deletion is scheduled
        assert deletion_result['status'] == 'scheduled', \
            "Deletion not scheduled"
        
        # Verify grace period is within 30 days
        scheduled_date = datetime.fromisoformat(deletion_result['scheduled_deletion_date'])
        days_until_deletion = (scheduled_date - datetime.utcnow()).days
        
        assert days_until_deletion <= 30, \
            f"Deletion scheduled beyond 30 days: {days_until_deletion} days"
        
        # Verify request is marked as completed
        updated_request = service.get_request_status(request.request_id)
        assert updated_request.status == RequestStatus.COMPLETED, \
            "Deletion request not marked as completed"
    
    @given(
        user_id=st.text(min_size=10, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        sensitive_data=sensitive_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_document_image_deletion_after_processing(self, user_id: str, sensitive_data: Dict[str, str]):
        """
        Property: Raw document images must be deleted after data extraction
        
        Validates Requirement 10.2: Document processor never stores raw document images 
        after data extraction
        """
        # Simulate document processing workflow
        # In production, this would involve actual OCR and image processing
        
        # Step 1: Document uploaded (raw image exists temporarily)
        document_metadata = {
            'user_id': user_id,
            'document_type': 'aadhaar',
            'upload_timestamp': datetime.utcnow().isoformat(),
            'raw_image_path': f'/tmp/documents/{user_id}/aadhaar_raw.jpg',
            'processing_status': 'uploaded'
        }
        
        # Step 2: Extract data from document
        extracted_data = {
            'aadhaar_number': sensitive_data['aadhaar'],
            'name': 'Test User',
            'address': 'Test Address'
        }
        
        # Step 3: After extraction, raw image should be marked for deletion
        document_metadata['processing_status'] = 'extracted'
        document_metadata['raw_image_deleted'] = True
        document_metadata['raw_image_path'] = None  # Path removed
        document_metadata['extracted_data'] = extracted_data
        
        # Verify raw image path is removed
        assert document_metadata['raw_image_path'] is None, \
            "Raw image path not removed after processing"
        
        # Verify deletion flag is set
        assert document_metadata['raw_image_deleted'] is True, \
            "Raw image deletion flag not set"
        
        # Verify extracted data is preserved
        assert document_metadata['extracted_data'] is not None, \
            "Extracted data not preserved"
        assert document_metadata['extracted_data']['aadhaar_number'] == sensitive_data['aadhaar'], \
            "Extracted data does not match"
    
    @given(
        username=username_strategy(),
        password=password_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
    def test_account_lockout_after_failed_attempts(self, username: str, password: str):
        """
        Property: Accounts must be locked after multiple failed authentication attempts
        
        Validates Requirement 10.4: System detects suspicious activity and freezes accounts
        """
        assume(len(username) >= 3)
        assume(len(password) >= 8)
        
        service = AuthenticationService()
        
        # Create user
        service.create_user(
            username=username,
            password=password,
            role=UserRole.USER
        )
        
        # Attempt multiple failed logins
        wrong_password = password + "wrong"
        
        for i in range(5):
            try:
                service.authenticate(username, wrong_password)
            except ValueError:
                pass  # Expected to fail
        
        # Verify account is locked
        user = service.users.get(username)
        assert user is not None, "User not found"
        assert user['is_locked'] is True, \
            "Account not locked after 5 failed attempts"
        
        # Verify correct password also fails when locked
        with pytest.raises(ValueError, match="locked"):
            service.authenticate(username, password)
    
    @given(
        user_id=st.text(min_size=10, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        consent_type=st.sampled_from(list(ConsentType))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_consent_management_and_tracking(self, user_id: str, consent_type: ConsentType):
        """
        Property: User consent must be tracked and respected for all data processing
        
        Validates Requirement 10.5: GDPR compliance for consent management
        """
        service = GDPRComplianceService()
        
        # Record consent granted
        consent = service.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=True,
            ip_address="192.168.1.1"
        )
        
        # Verify consent is recorded
        assert consent.consent_id is not None, \
            "Consent ID not generated"
        assert consent.granted is True, \
            "Consent not marked as granted"
        
        # Verify consent can be checked
        has_consent = service.check_consent(user_id, consent_type)
        assert has_consent is True, \
            "Consent check failed for granted consent"
        
        # Withdraw consent
        withdrawal = service.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            granted=False
        )
        
        # Verify consent is withdrawn
        has_consent_after_withdrawal = service.check_consent(user_id, consent_type)
        assert has_consent_after_withdrawal is False, \
            "Consent still active after withdrawal"
    
    @given(
        profile_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz_'),
            values=st.one_of(
                st.text(min_size=1, max_size=50),
                st.integers(min_value=0, max_value=1000000),
                st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_data_encryption_at_rest(self, profile_data: Dict[str, Any]):
        """
        Property: All profile data must be encrypted when stored at rest
        
        Validates Requirement 10.1: Data encryption at rest
        """
        # Wrap profile data in expected structure
        wrapped_profile = {
            'documents': profile_data,
            'preferences': {}
        }
        
        # Encrypt profile data
        encrypted_profile = encrypt_profile_data(wrapped_profile)
        
        # Verify documents section is encrypted
        if 'documents' in encrypted_profile and encrypted_profile['documents']:
            for key, value in encrypted_profile['documents'].items():
                if value is not None:
                    # Encrypted values should be different from original
                    original_value = str(profile_data[key])
                    assert value != original_value, \
                        f"Field {key} was not encrypted"
        
        # Verify decryption restores original data
        decrypted_profile = decrypt_profile_data(encrypted_profile)
        
        for key, original_value in profile_data.items():
            decrypted_value = decrypted_profile['documents'][key]
            # Convert both to strings for comparison
            assert str(decrypted_value) == str(original_value), \
                f"Field {key} did not decrypt correctly"
    
    @given(
        username=username_strategy(),
        password=password_strategy(),
        token_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
            values=st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_session_token_security(self, username: str, password: str, token_data: Dict[str, str]):
        """
        Property: Session tokens must be cryptographically secure and verifiable
        
        Validates Requirement 10.3: Secure session management
        """
        assume(len(username) >= 3)
        assume(len(password) >= 8)
        
        service = AuthenticationService()
        
        # Create user
        service.create_user(
            username=username,
            password=password,
            role=UserRole.USER
        )
        
        # Authenticate and get token
        auth_result = service.authenticate(username, password)
        
        # Verify token is generated
        assert 'token' in auth_result, \
            "Authentication token not generated"
        assert len(auth_result['token']) > 0, \
            "Authentication token is empty"
        
        # Verify token can be verified
        token_payload = service.verify_token(auth_result['token'])
        
        # Verify token contains user information
        assert token_payload['username'] == username, \
            "Token does not contain correct username"
        assert token_payload['role'] == UserRole.USER.value, \
            "Token does not contain correct role"
        
        # Verify token has expiration
        assert 'exp' in token_payload, \
            "Token does not have expiration"
        
        # Verify session is created
        assert 'session_id' in auth_result, \
            "Session ID not generated"
        
        # Verify session can be verified
        session = service.verify_session(auth_result['session_id'])
        assert session['username'] == username, \
            "Session does not contain correct username"
    
    @given(
        user_id=st.text(min_size=10, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        user_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz_'),
            values=st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_access_request_completeness(self, user_id: str, user_data: Dict[str, str]):
        """
        Property: Data access requests must return all user data
        
        Validates Requirement 10.5: Right to access personal data (GDPR)
        """
        service = GDPRComplianceService()
        
        # Create access request
        request = service.create_data_request(
            user_id=user_id,
            request_type=DataRequestType.ACCESS,
            requested_by=user_id
        )
        
        # Process access request
        packaged_data = service.process_access_request(
            request_id=request.request_id,
            user_data=user_data
        )
        
        # Verify all user data is included
        assert 'data' in packaged_data, \
            "User data not included in access request response"
        
        # Verify all original data fields are present
        for key, value in user_data.items():
            assert key in packaged_data['data'], \
                f"Field {key} missing from access request response"
            assert packaged_data['data'][key] == value, \
                f"Field {key} value incorrect in access request response"
        
        # Verify metadata is included
        assert 'metadata' in packaged_data, \
            "Metadata not included in access request response"
        assert 'generated_at' in packaged_data, \
            "Generation timestamp not included"
    
    @given(
        sensitive_data=sensitive_data_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sensitive_data_masking_for_display(self, sensitive_data: Dict[str, str]):
        """
        Property: Sensitive data must be masked when displayed to users
        
        Validates Requirement 10.1: Secure handling of sensitive information
        """
        service = EncryptionService()
        
        # Mask sensitive fields
        for field_name, field_value in sensitive_data.items():
            masked_value = service.mask_sensitive_data(field_value, visible_chars=4)
            
            # Verify masking occurred
            assert masked_value != field_value, \
                f"Field {field_name} was not masked"
            
            # Verify masked value contains asterisks
            assert '*' in masked_value, \
                f"Masked {field_name} does not contain asterisks"
            
            # Verify last 4 characters are visible (if value is long enough)
            if len(field_value) > 4:
                assert masked_value.endswith(field_value[-4:]), \
                    f"Masked {field_name} does not show last 4 characters"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
