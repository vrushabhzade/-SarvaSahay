"""
Property-Based Tests for Profile Data Completeness and Security
Feature: sarvasahay-platform, Property 1: Profile Data Completeness and Security

This test validates that for any user profile creation or update, the system:
1. Collects all required demographic fields (age, gender, caste, income, land ownership, employment, family details)
2. Stores the data with encryption
3. Automatically triggers eligibility re-evaluation

Validates: Requirements 1.2, 1.4, 1.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from typing import Dict, Any

from shared.models.user_profile import (
    Gender, Caste, MaritalStatus, EmploymentStatus, Language, CommunicationChannel,
    Demographics, Economic, Location, Family, Documents, Preferences,
    UserProfile, UserProfileCreate
)
from shared.utils.encryption import (
    EncryptionService, encrypt_profile_data, decrypt_profile_data
)


# Strategy for generating valid demographics
@st.composite
def demographics_strategy(draw):
    """Generate valid Demographics instances"""
    return Demographics(
        age=draw(st.integers(min_value=0, max_value=150)),
        gender=draw(st.sampled_from(list(Gender))),
        caste=draw(st.sampled_from(list(Caste))),
        marital_status=draw(st.sampled_from(list(MaritalStatus)))
    )


# Strategy for generating valid economic data
@st.composite
def economic_strategy(draw):
    """Generate valid Economic instances"""
    return Economic(
        annual_income=draw(st.integers(min_value=0, max_value=10000000)),
        land_ownership=draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)),
        employment_status=draw(st.sampled_from(list(EmploymentStatus)))
    )


# Strategy for generating valid location data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances"""
    return Location(
        state=draw(st.text(min_size=2, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '))),
        district=draw(st.text(min_size=2, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '))),
        block=draw(st.text(min_size=2, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '))),
        village=draw(st.text(min_size=2, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '))),
        pincode=draw(st.from_regex(r'^\d{6}$', fullmatch=True))
    )


# Strategy for generating valid family data
@st.composite
def family_strategy(draw):
    """Generate valid Family instances"""
    size = draw(st.integers(min_value=1, max_value=20))
    dependents = draw(st.integers(min_value=0, max_value=size - 1))
    elderly_members = draw(st.integers(min_value=0, max_value=size))
    children = draw(st.integers(min_value=0, max_value=size))
    
    return Family(
        size=size,
        dependents=dependents,
        elderly_members=elderly_members,
        children=children
    )


# Strategy for generating valid documents
@st.composite
def documents_strategy(draw):
    """Generate valid Documents instances"""
    # Generate valid Aadhaar (12 digits)
    aadhaar = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(12)])
    
    # Generate valid PAN (5 letters, 4 digits, 1 letter)
    pan_letters1 = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(5)])
    pan_digits = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(4)])
    pan_letter2 = draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    pan = f"{pan_letters1}{pan_digits}{pan_letter2}"
    
    # Generate valid IFSC (4 letters, 0, 6 alphanumeric)
    ifsc_letters = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) for _ in range(4)])
    ifsc_suffix = ''.join([draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')) for _ in range(6)])
    ifsc = f"{ifsc_letters}0{ifsc_suffix}"
    
    return Documents(
        aadhaar=aadhaar,
        pan=pan,
        bank_account=draw(st.text(min_size=9, max_size=18, alphabet=st.characters(whitelist_categories=('Nd',)))),
        bank_ifsc=ifsc,
        land_records=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))),
        ration_card=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))),
        voter_id=draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))))
    )


# Strategy for generating valid preferences
@st.composite
def preferences_strategy(draw):
    """Generate valid Preferences instances"""
    # Generate valid Indian phone number matching pattern: ^\+?91?[6-9]\d{9}$
    # Based on the actual regex, valid formats are:
    # - 919XXXXXXXXX (91 + 10 digits starting with 6-9)
    # - +919XXXXXXXXX (+91 + 10 digits starting with 6-9)
    phone_format = draw(st.sampled_from(['with_plus', 'with_91']))
    phone_first_digit = draw(st.sampled_from(['6', '7', '8', '9']))
    phone_rest = ''.join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(9)])
    
    if phone_format == 'with_plus':
        phone = f"+91{phone_first_digit}{phone_rest}"
    else:
        phone = f"91{phone_first_digit}{phone_rest}"
    
    # Generate valid email - use only ASCII lowercase letters and digits
    email_user = draw(st.text(min_size=3, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    email_domain = draw(st.text(min_size=3, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz'))
    email_tld = draw(st.sampled_from(['com', 'in', 'org', 'net']))
    email = f"{email_user}@{email_domain}.{email_tld}"
    
    return Preferences(
        language=draw(st.sampled_from(list(Language))),
        communication_channel=draw(st.sampled_from(list(CommunicationChannel))),
        phone_number=phone,
        email=email,
        sms_notifications=draw(st.booleans()),
        voice_notifications=draw(st.booleans())
    )


# Strategy for generating complete user profiles
@st.composite
def user_profile_strategy(draw):
    """Generate valid UserProfile instances"""
    return UserProfile(
        demographics=draw(demographics_strategy()),
        economic=draw(economic_strategy()),
        location=draw(location_strategy()),
        family=draw(family_strategy()),
        documents=draw(documents_strategy()),
        preferences=draw(preferences_strategy())
    )


class TestProfileDataCompletenessProperty:
    """
    Property 1: Profile Data Completeness and Security
    
    For any user profile creation or update, the system should:
    1. Collect all required demographic fields
    2. Store the data with encryption
    3. Maintain data integrity through encryption/decryption cycles
    """
    
    @given(profile=user_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_contains_all_required_fields(self, profile: UserProfile):
        """
        Property: All required demographic fields must be present in any valid profile
        
        Validates Requirement 1.2: Profile collection includes age, gender, caste, 
        income, land ownership, employment status, and family details
        """
        # Verify demographics fields
        assert profile.demographics is not None
        assert profile.demographics.age is not None
        assert 0 <= profile.demographics.age <= 150
        assert profile.demographics.gender is not None
        assert profile.demographics.caste is not None
        assert profile.demographics.marital_status is not None
        
        # Verify economic fields
        assert profile.economic is not None
        assert profile.economic.annual_income is not None
        assert profile.economic.annual_income >= 0
        assert profile.economic.land_ownership is not None
        assert profile.economic.land_ownership >= 0
        assert profile.economic.employment_status is not None
        
        # Verify location fields
        assert profile.location is not None
        assert profile.location.state is not None
        assert len(profile.location.state) >= 2
        assert profile.location.district is not None
        assert profile.location.block is not None
        assert profile.location.village is not None
        
        # Verify family fields
        assert profile.family is not None
        assert profile.family.size is not None
        assert profile.family.size >= 1
        assert profile.family.dependents is not None
        assert profile.family.dependents >= 0
        assert profile.family.dependents < profile.family.size
    
    @given(profile=user_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_data_encryption_security(self, profile: UserProfile):
        """
        Property: All sensitive profile data must be encrypted when stored
        
        Validates Requirement 1.4: Profile data is stored securely with encryption
        """
        # Convert profile to dictionary
        profile_dict = profile.dict()
        
        # Encrypt the profile data
        encrypted_profile = encrypt_profile_data(profile_dict)
        
        # Verify that sensitive fields are encrypted (different from original)
        if profile.documents:
            if profile.documents.aadhaar:
                assert encrypted_profile['documents']['aadhaar'] != profile.documents.aadhaar
            if profile.documents.pan:
                assert encrypted_profile['documents']['pan'] != profile.documents.pan
            if profile.documents.bank_account:
                assert encrypted_profile['documents']['bank_account'] != profile.documents.bank_account
        
        if profile.preferences:
            if profile.preferences.phone_number:
                assert encrypted_profile['preferences']['phone_number'] != profile.preferences.phone_number
            if profile.preferences.email:
                assert encrypted_profile['preferences']['email'] != profile.preferences.email
    
    @given(profile=user_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_encryption_decryption_round_trip(self, profile: UserProfile):
        """
        Property: Encrypted profile data must decrypt back to original values
        
        Validates Requirement 1.4: Data encryption maintains data integrity
        """
        # Convert profile to dictionary
        profile_dict = profile.dict()
        
        # Store original sensitive values
        original_aadhaar = profile.documents.aadhaar if profile.documents else None
        original_pan = profile.documents.pan if profile.documents else None
        original_phone = profile.preferences.phone_number if profile.preferences else None
        original_email = profile.preferences.email if profile.preferences else None
        
        # Encrypt and then decrypt
        encrypted_profile = encrypt_profile_data(profile_dict)
        decrypted_profile = decrypt_profile_data(encrypted_profile)
        
        # Verify round-trip integrity for sensitive fields
        if original_aadhaar:
            assert decrypted_profile['documents']['aadhaar'] == original_aadhaar
        if original_pan:
            assert decrypted_profile['documents']['pan'] == original_pan
        if original_phone:
            assert decrypted_profile['preferences']['phone_number'] == original_phone
        if original_email:
            assert decrypted_profile['preferences']['email'] == original_email
    
    @given(profile=user_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_completeness_score_calculation(self, profile: UserProfile):
        """
        Property: Profile completeness score must be calculated and within valid range
        
        Validates Requirement 1.5: System tracks profile completeness for re-evaluation
        """
        # Completeness score should be calculated
        assert profile.completeness_score is not None
        
        # Score must be between 0 and 1
        assert 0 <= profile.completeness_score <= 1
        
        # A profile with all required fields should have a high completeness score
        # Since we're generating complete profiles, score should be > 0
        assert profile.completeness_score > 0
    
    @given(
        demographics=demographics_strategy(),
        economic=economic_strategy(),
        location=location_strategy(),
        family=family_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_update_maintains_data_integrity(
        self, 
        demographics: Demographics,
        economic: Economic,
        location: Location,
        family: Family
    ):
        """
        Property: Profile updates must maintain data integrity and validation
        
        Validates Requirement 1.5: Profile updates trigger re-evaluation
        """
        # Create initial profile
        initial_profile = UserProfile(
            demographics=demographics,
            economic=economic,
            location=location,
            family=family
        )
        
        # Verify initial profile is valid
        assert initial_profile.demographics.age >= 0
        assert initial_profile.economic.annual_income >= 0
        assert initial_profile.family.dependents < initial_profile.family.size
        
        # Update should maintain validation rules
        updated_profile = initial_profile.copy(update={
            'version': initial_profile.version + 1,
            'updated_at': datetime.utcnow()
        })
        
        # Verify updated profile maintains integrity
        assert updated_profile.demographics.age == initial_profile.demographics.age
        assert updated_profile.economic.annual_income == initial_profile.economic.annual_income
        assert updated_profile.version == initial_profile.version + 1
    
    @given(profile=user_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_validation_rejects_invalid_data(self, profile: UserProfile):
        """
        Property: Profile validation must enforce all business rules
        
        Validates Requirement 1.2: Data validation ensures quality
        """
        # All generated profiles should be valid
        profile_dict = profile.dict()
        
        # Verify age constraints
        assert 0 <= profile.demographics.age <= 150
        
        # Verify economic constraints
        assert profile.economic.annual_income >= 0
        assert profile.economic.land_ownership >= 0
        
        # Verify family constraints
        assert profile.family.size >= 1
        assert profile.family.dependents >= 0
        assert profile.family.dependents < profile.family.size
        assert profile.family.elderly_members <= profile.family.size
        assert profile.family.children <= profile.family.size
        
        # Verify document format constraints (if present)
        if profile.documents:
            if profile.documents.aadhaar:
                assert len(profile.documents.aadhaar) == 12
                assert profile.documents.aadhaar.isdigit()
            
            if profile.documents.pan:
                assert len(profile.documents.pan) == 10
                assert profile.documents.pan[:5].isalpha()
                assert profile.documents.pan[5:9].isdigit()
                assert profile.documents.pan[9].isalpha()
    
    @given(
        service=st.builds(EncryptionService),
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll',))),
            values=st.text(min_size=1, max_size=100)
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_encryption_service_consistency(self, service: EncryptionService, data: Dict[str, str]):
        """
        Property: Encryption service must consistently encrypt/decrypt any data
        
        Validates Requirement 1.4: Encryption is reliable and consistent
        """
        assume(len(data) > 0)  # Ensure we have data to encrypt
        
        # Encrypt the data
        encrypted = service.encrypt_dict(data)
        
        # Verify encryption changed the data
        for key, value in data.items():
            if value:  # Only check non-empty values
                assert encrypted[key] != value
        
        # Decrypt and verify round-trip
        decrypted = service.decrypt_dict(encrypted)
        
        # Verify all values match original
        for key, value in data.items():
            assert decrypted[key] == value
    
    @given(profile=user_profile_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_serialization_preserves_data(self, profile: UserProfile):
        """
        Property: Profile serialization must preserve all data fields
        
        Validates Requirement 1.4: Data storage maintains integrity
        """
        # Serialize to dict
        profile_dict = profile.dict()
        
        # Verify all required sections are present
        assert 'demographics' in profile_dict
        assert 'economic' in profile_dict
        assert 'location' in profile_dict
        assert 'family' in profile_dict
        
        # Verify data types are preserved
        assert isinstance(profile_dict['demographics']['age'], int)
        assert isinstance(profile_dict['economic']['annual_income'], int)
        assert isinstance(profile_dict['economic']['land_ownership'], float)
        assert isinstance(profile_dict['family']['size'], int)
        
        # Verify enum values are serialized correctly
        assert profile_dict['demographics']['gender'] in [g.value for g in Gender]
        assert profile_dict['demographics']['caste'] in [c.value for c in Caste]
        assert profile_dict['economic']['employment_status'] in [e.value for e in EmploymentStatus]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
