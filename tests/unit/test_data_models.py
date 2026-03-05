"""
Unit tests for data models and validation
Tests comprehensive validation rules, encryption, and serialization
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models.user_profile import (
    Gender, Caste, MaritalStatus, EmploymentStatus, Language, CommunicationChannel,
    Demographics, Economic, Location, Family, Documents, Preferences,
    UserProfile, UserProfileCreate, UserProfileUpdate
)
from shared.models.government_scheme import (
    SchemeType, SchemeStatus, EligibilityCategory, NumericCriteria,
    EligibilityCriteria, GovernmentScheme, EligibilityResult
)
from shared.models.application import (
    ApplicationStatus, PaymentStatus, ApplicationPriority,
    StatusHistory, ApplicationPredictions, PaymentDetails, Application
)
from shared.utils.encryption import EncryptionService, encrypt_profile_data, decrypt_profile_data
from shared.utils.serialization import (
    ModelSerializer, SecureSerializer, mask_sensitive_fields,
    serialize_profile, deserialize_profile, profile_to_dict
)


class TestDemographics:
    """Test Demographics model validation"""
    
    def test_valid_demographics(self):
        """Test creating valid demographics"""
        demo = Demographics(
            age=35,
            gender=Gender.FEMALE,
            caste=Caste.SC,
            marital_status=MaritalStatus.MARRIED
        )
        assert demo.age == 35
        assert demo.gender == Gender.FEMALE
    
    def test_age_validation_negative(self):
        """Test age validation rejects negative values"""
        with pytest.raises(ValidationError):
            Demographics(
                age=-5,
                gender=Gender.MALE,
                caste=Caste.GENERAL,
                marital_status=MaritalStatus.SINGLE
            )
    
    def test_age_validation_too_high(self):
        """Test age validation rejects values over 150"""
        with pytest.raises(ValidationError):
            Demographics(
                age=200,
                gender=Gender.MALE,
                caste=Caste.GENERAL,
                marital_status=MaritalStatus.SINGLE
            )


class TestEconomic:
    """Test Economic model validation"""
    
    def test_valid_economic(self):
        """Test creating valid economic data"""
        econ = Economic(
            annual_income=120000,
            land_ownership=2.5,
            employment_status=EmploymentStatus.FARMER
        )
        assert econ.annual_income == 120000
        assert econ.land_ownership == 2.5
    
    def test_negative_income_rejected(self):
        """Test negative income is rejected"""
        with pytest.raises(ValidationError):
            Economic(
                annual_income=-1000,
                land_ownership=2.5,
                employment_status=EmploymentStatus.FARMER
            )
    
    def test_negative_land_rejected(self):
        """Test negative land ownership is rejected"""
        with pytest.raises(ValidationError):
            Economic(
                annual_income=120000,
                land_ownership=-1.0,
                employment_status=EmploymentStatus.FARMER
            )


class TestDocuments:
    """Test Documents model validation"""
    
    def test_valid_aadhaar(self):
        """Test valid Aadhaar number"""
        docs = Documents(aadhaar="123456789012")
        assert docs.aadhaar == "123456789012"
    
    def test_invalid_aadhaar_length(self):
        """Test invalid Aadhaar length is rejected"""
        with pytest.raises(ValidationError):
            Documents(aadhaar="12345")
    
    def test_valid_pan(self):
        """Test valid PAN format"""
        docs = Documents(pan="ABCDE1234F")
        assert docs.pan == "ABCDE1234F"
    
    def test_invalid_pan_format(self):
        """Test invalid PAN format is rejected"""
        with pytest.raises(ValidationError):
            Documents(pan="INVALID123")
    
    def test_valid_ifsc(self):
        """Test valid IFSC code"""
        docs = Documents(bank_ifsc="SBIN0001234")
        assert docs.bank_ifsc == "SBIN0001234"
    
    def test_invalid_ifsc_format(self):
        """Test invalid IFSC format is rejected"""
        with pytest.raises(ValidationError):
            Documents(bank_ifsc="INVALID")


class TestPreferences:
    """Test Preferences model validation"""
    
    def test_valid_phone_number(self):
        """Test valid Indian phone number"""
        prefs = Preferences(
            language=Language.HINDI,
            communication_channel=CommunicationChannel.SMS,
            phone_number="+919876543210"
        )
        assert prefs.phone_number == "+919876543210"
    
    def test_invalid_phone_number(self):
        """Test invalid phone number is rejected"""
        with pytest.raises(ValidationError):
            Preferences(
                language=Language.HINDI,
                communication_channel=CommunicationChannel.SMS,
                phone_number="123"
            )
    
    def test_valid_email(self):
        """Test valid email format"""
        prefs = Preferences(
            language=Language.ENGLISH,
            communication_channel=CommunicationChannel.EMAIL,
            email="user@example.com"
        )
        assert prefs.email == "user@example.com"
    
    def test_invalid_email(self):
        """Test invalid email format is rejected"""
        with pytest.raises(ValidationError):
            Preferences(
                language=Language.ENGLISH,
                communication_channel=CommunicationChannel.EMAIL,
                email="invalid-email"
            )


class TestFamily:
    """Test Family model validation"""
    
    def test_valid_family(self):
        """Test valid family data"""
        family = Family(
            size=4,
            dependents=2,
            elderly_members=1,
            children=2
        )
        assert family.size == 4
        assert family.dependents == 2
    
    def test_dependents_exceed_size(self):
        """Test dependents cannot exceed family size"""
        with pytest.raises(ValidationError):
            Family(size=4, dependents=5)
    
    def test_elderly_exceed_size(self):
        """Test elderly members cannot exceed family size"""
        with pytest.raises(ValidationError):
            Family(size=4, dependents=2, elderly_members=6)


class TestUserProfile:
    """Test UserProfile model"""
    
    def test_create_complete_profile(self):
        """Test creating a complete user profile"""
        profile = UserProfile(
            demographics=Demographics(
                age=35,
                gender=Gender.FEMALE,
                caste=Caste.SC,
                marital_status=MaritalStatus.MARRIED
            ),
            economic=Economic(
                annual_income=120000,
                land_ownership=2.5,
                employment_status=EmploymentStatus.FARMER
            ),
            location=Location(
                state="Maharashtra",
                district="Pune",
                block="Haveli",
                village="Pirangut",
                pincode="412108"
            ),
            family=Family(
                size=4,
                dependents=2,
                elderly_members=1,
                children=2
            ),
            documents=Documents(
                aadhaar="123456789012",
                pan="ABCDE1234F",
                bank_account="1234567890",
                bank_ifsc="SBIN0001234"
            ),
            preferences=Preferences(
                language=Language.MARATHI,
                communication_channel=CommunicationChannel.SMS,
                phone_number="+919876543210"
            )
        )
        
        assert profile.demographics.age == 35
        assert profile.economic.annual_income == 120000
        assert profile.completeness_score is not None
        assert profile.completeness_score > 0
    
    def test_profile_completeness_calculation(self):
        """Test profile completeness score calculation"""
        profile = UserProfile(
            demographics=Demographics(
                age=35,
                gender=Gender.MALE,
                caste=Caste.GENERAL,
                marital_status=MaritalStatus.SINGLE
            ),
            economic=Economic(
                annual_income=100000,
                land_ownership=1.0,
                employment_status=EmploymentStatus.FARMER
            ),
            location=Location(
                state="Karnataka",
                district="Bangalore",
                block="North",
                village="Test"
            ),
            family=Family(size=1, dependents=0)
        )
        
        # Should have some completeness score
        assert profile.completeness_score is not None
        assert 0 <= profile.completeness_score <= 1


class TestGovernmentScheme:
    """Test GovernmentScheme model"""
    
    def test_create_scheme(self):
        """Test creating a government scheme"""
        scheme = GovernmentScheme(
            scheme_id="PM-KISAN",
            name="Pradhan Mantri Kisan Samman Nidhi",
            description="Income support for farmers",
            scheme_type=SchemeType.AGRICULTURE,
            benefit_amount=6000,
            benefit_frequency="annual",
            eligibility_criteria=EligibilityCriteria(
                land_ownership=NumericCriteria(min_value=0.1, max_value=2.0),
                employment_status=["farmer"],
                annual_income=NumericCriteria(max_value=200000)
            ),
            implementing_agency="Ministry of Agriculture",
            application_process="Online application",
            required_documents=["Aadhaar", "Bank Account", "Land Records"]
        )
        
        assert scheme.scheme_id == "PM-KISAN"
        assert scheme.benefit_amount == 6000
        assert scheme.status == SchemeStatus.ACTIVE


class TestApplication:
    """Test Application model"""
    
    def test_create_application(self):
        """Test creating an application"""
        app = Application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            form_data={"farmer_name": "Test User", "land_area": "2.5"},
            submitted_documents=["doc-001", "doc-002"]
        )
        
        assert app.user_id == "user-123"
        assert app.status == ApplicationStatus.DRAFT
        assert len(app.status_history) > 0
    
    def test_add_status_change(self):
        """Test adding status change to application"""
        app = Application(
            user_id="user-123",
            scheme_id="PM-KISAN",
            form_data={"test": "data"}
        )
        
        initial_history_len = len(app.status_history)
        app.add_status_change(
            ApplicationStatus.SUBMITTED,
            reason="User submitted application",
            updated_by="system"
        )
        
        assert app.status == ApplicationStatus.SUBMITTED
        assert len(app.status_history) == initial_history_len + 1
        assert app.status_history[-1].status == ApplicationStatus.SUBMITTED


class TestEncryption:
    """Test encryption utilities"""
    
    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption"""
        service = EncryptionService()
        original = "sensitive data"
        
        encrypted = service.encrypt(original)
        decrypted = service.decrypt(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption"""
        service = EncryptionService()
        original = {
            "aadhaar": "123456789012",
            "pan": "ABCDE1234F",
            "bank_account": "1234567890"
        }
        
        encrypted = service.encrypt_dict(original)
        decrypted = service.decrypt_dict(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_mask_sensitive_data(self):
        """Test masking sensitive data"""
        service = EncryptionService()
        aadhaar = "123456789012"
        
        masked = service.mask_sensitive_data(aadhaar, 4)
        
        assert masked == "********9012"
        assert len(masked) == len(aadhaar)
    
    def test_encrypt_profile_data(self):
        """Test encrypting profile data"""
        profile_dict = {
            "demographics": {"age": 35, "gender": "male"},
            "documents": {
                "aadhaar": "123456789012",
                "pan": "ABCDE1234F"
            },
            "preferences": {
                "phone_number": "+919876543210",
                "email": "test@example.com"
            }
        }
        
        encrypted = encrypt_profile_data(profile_dict)
        
        # Documents should be encrypted
        assert encrypted["documents"]["aadhaar"] != "123456789012"
        assert encrypted["preferences"]["phone_number"] != "+919876543210"
        
        # Decrypt and verify
        decrypted = decrypt_profile_data(encrypted)
        assert decrypted["documents"]["aadhaar"] == "123456789012"
        assert decrypted["preferences"]["phone_number"] == "+919876543210"


class TestSerialization:
    """Test serialization utilities"""
    
    def test_serialize_deserialize_profile(self):
        """Test profile serialization and deserialization"""
        profile = UserProfile(
            demographics=Demographics(
                age=35,
                gender=Gender.MALE,
                caste=Caste.GENERAL,
                marital_status=MaritalStatus.SINGLE
            ),
            economic=Economic(
                annual_income=100000,
                land_ownership=1.0,
                employment_status=EmploymentStatus.FARMER
            ),
            location=Location(
                state="Karnataka",
                district="Bangalore",
                block="North",
                village="Test"
            ),
            family=Family(size=1, dependents=0)
        )
        
        # Serialize without encryption
        serialized = serialize_profile(profile, secure=False)
        deserialized = deserialize_profile(serialized, UserProfile, secure=False)
        
        assert deserialized.demographics.age == profile.demographics.age
        assert deserialized.economic.annual_income == profile.economic.annual_income
    
    def test_mask_sensitive_fields(self):
        """Test masking sensitive fields in dictionary"""
        profile_dict = {
            "documents": {
                "aadhaar": "123456789012",
                "pan": "ABCDE1234F",
                "bank_account": "1234567890"
            },
            "preferences": {
                "phone_number": "+919876543210",
                "email": "user@example.com"
            }
        }
        
        masked = mask_sensitive_fields(profile_dict)
        
        # Check that sensitive fields are masked
        assert masked["documents"]["aadhaar"] != "123456789012"
        assert "9012" in masked["documents"]["aadhaar"]
        assert masked["preferences"]["phone_number"] != "+919876543210"
        assert "@example.com" in masked["preferences"]["email"]
    
    def test_profile_to_dict_with_masking(self):
        """Test converting profile to dict with masking"""
        profile = UserProfile(
            demographics=Demographics(
                age=35,
                gender=Gender.MALE,
                caste=Caste.GENERAL,
                marital_status=MaritalStatus.SINGLE
            ),
            economic=Economic(
                annual_income=100000,
                land_ownership=1.0,
                employment_status=EmploymentStatus.FARMER
            ),
            location=Location(
                state="Karnataka",
                district="Bangalore",
                block="North",
                village="Test"
            ),
            family=Family(size=1, dependents=0),
            documents=Documents(
                aadhaar="123456789012",
                pan="ABCDE1234F"
            )
        )
        
        masked_dict = profile_to_dict(profile, mask_sensitive=True)
        
        # Sensitive fields should be masked
        assert masked_dict["documents"]["aadhaar"] != "123456789012"
        assert "9012" in masked_dict["documents"]["aadhaar"]


class TestNumericCriteria:
    """Test NumericCriteria validation"""
    
    def test_valid_range(self):
        """Test valid numeric range"""
        criteria = NumericCriteria(min_value=0, max_value=100)
        assert criteria.min_value == 0
        assert criteria.max_value == 100
    
    def test_invalid_range(self):
        """Test invalid range (max < min) is rejected"""
        with pytest.raises(ValidationError):
            NumericCriteria(min_value=100, max_value=50)


class TestApplicationPredictions:
    """Test ApplicationPredictions validation"""
    
    def test_valid_predictions(self):
        """Test valid prediction values"""
        pred = ApplicationPredictions(
            approval_probability=0.85,
            expected_processing_days=30,
            confidence_score=0.92,
            suggested_improvements=[],
            risk_factors=[]
        )
        assert pred.approval_probability == 0.85
        assert pred.confidence_score == 0.92
    
    def test_invalid_probability(self):
        """Test invalid probability values are rejected"""
        with pytest.raises(ValidationError):
            ApplicationPredictions(
                approval_probability=1.5,  # Invalid: > 1
                expected_processing_days=30,
                confidence_score=0.92
            )
