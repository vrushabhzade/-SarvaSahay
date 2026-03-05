"""
User Profile Data Models
Pydantic models for user profile management with validation
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, field_validator
from enum import Enum
import re


class Gender(str, Enum):
    """Gender enumeration"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Caste(str, Enum):
    """Caste category enumeration"""
    GENERAL = "General"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"


class MaritalStatus(str, Enum):
    """Marital status enumeration"""
    SINGLE = "single"
    MARRIED = "married"
    WIDOWED = "widowed"
    DIVORCED = "divorced"


class EmploymentStatus(str, Enum):
    """Employment status enumeration"""
    FARMER = "farmer"
    LABORER = "laborer"
    SELF_EMPLOYED = "self-employed"
    UNEMPLOYED = "unemployed"
    GOVERNMENT_EMPLOYEE = "government-employee"
    PRIVATE_EMPLOYEE = "private-employee"


class Demographics(BaseModel):
    """User demographic information"""
    age: int = Field(..., ge=0, le=150, description="Age in years")
    gender: Gender = Field(..., description="Gender")
    caste: Caste = Field(..., description="Caste category")
    marital_status: MaritalStatus = Field(..., description="Marital status")
    
    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v


class Economic(BaseModel):
    """User economic information"""
    annual_income: int = Field(..., ge=0, description="Annual income in INR")
    land_ownership: float = Field(..., ge=0, description="Land ownership in acres")
    employment_status: EmploymentStatus = Field(..., description="Employment status")
    
    @validator('annual_income')
    def validate_income(cls, v):
        if v < 0:
            raise ValueError('Annual income cannot be negative')
        return v
    
    @validator('land_ownership')
    def validate_land(cls, v):
        if v < 0:
            raise ValueError('Land ownership cannot be negative')
        return v


class Language(str, Enum):
    """Supported languages"""
    HINDI = "hindi"
    MARATHI = "marathi"
    TAMIL = "tamil"
    BENGALI = "bengali"
    TELUGU = "telugu"
    KANNADA = "kannada"
    GUJARATI = "gujarati"
    MALAYALAM = "malayalam"
    PUNJABI = "punjabi"
    ENGLISH = "english"


class CommunicationChannel(str, Enum):
    """Communication channel preferences"""
    SMS = "sms"
    VOICE = "voice"
    APP = "app"
    EMAIL = "email"


class Location(BaseModel):
    """User location information"""
    state: str = Field(..., min_length=2, max_length=50, description="State name")
    district: str = Field(..., min_length=2, max_length=50, description="District name")
    block: str = Field(..., min_length=2, max_length=50, description="Block name")
    village: str = Field(..., min_length=2, max_length=50, description="Village name")
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$', description="6-digit pincode")


class Family(BaseModel):
    """User family information"""
    size: int = Field(..., ge=1, le=20, description="Family size")
    dependents: int = Field(..., ge=0, description="Number of dependents")
    
    @validator('dependents')
    def validate_dependents(cls, v, values):
        if 'size' in values and v >= values['size']:
            raise ValueError('Dependents cannot be greater than or equal to family size')
        return v


class Family(BaseModel):
    """User family information"""
    size: int = Field(..., ge=1, le=20, description="Family size")
    dependents: int = Field(..., ge=0, description="Number of dependents")
    elderly_members: int = Field(default=0, ge=0, description="Number of elderly members (60+)")
    children: int = Field(default=0, ge=0, description="Number of children under 18")
    
    @validator('dependents')
    def validate_dependents(cls, v, values):
        if 'size' in values and v >= values['size']:
            raise ValueError('Dependents cannot be greater than or equal to family size')
        return v
    
    @validator('elderly_members', 'children')
    def validate_family_members(cls, v, values):
        if 'size' in values and v > values['size']:
            raise ValueError('Family member count cannot exceed family size')
        return v


class Documents(BaseModel):
    """User document information (encrypted storage)"""
    aadhaar: Optional[str] = Field(None, pattern=r'^\d{12}$', description="12-digit Aadhaar number")
    pan: Optional[str] = Field(None, pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', description="PAN card number")
    bank_account: Optional[str] = Field(None, min_length=9, max_length=18, description="Bank account number")
    bank_ifsc: Optional[str] = Field(None, pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$', description="Bank IFSC code")
    land_records: Optional[str] = Field(None, description="Land record reference number")
    ration_card: Optional[str] = Field(None, description="Ration card number")
    voter_id: Optional[str] = Field(None, description="Voter ID number")
    
    @validator('aadhaar')
    def validate_aadhaar(cls, v):
        if v and not re.match(r'^\d{12}$', v):
            raise ValueError('Aadhaar must be exactly 12 digits')
        return v
    
    @validator('pan')
    def validate_pan(cls, v):
        if v and not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', v):
            raise ValueError('Invalid PAN format. Expected: ABCDE1234F')
        return v
    
    @validator('bank_ifsc')
    def validate_ifsc(cls, v):
        if v and not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', v):
            raise ValueError('Invalid IFSC code format')
        return v


class Preferences(BaseModel):
    """User communication preferences"""
    language: Language = Field(default=Language.HINDI, description="Preferred language")
    communication_channel: CommunicationChannel = Field(default=CommunicationChannel.SMS, description="Preferred communication channel")
    phone_number: Optional[str] = Field(None, pattern=r'^\+?91?[6-9]\d{9}$', description="Indian mobile number")
    email: Optional[str] = Field(None, description="Email address")
    sms_notifications: bool = Field(default=True, description="Enable SMS notifications")
    voice_notifications: bool = Field(default=False, description="Enable voice call notifications")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            # Remove spaces and dashes
            cleaned = re.sub(r'[\s\-]', '', v)
            # Check if it matches Indian mobile pattern
            if not re.match(r'^\+?91?[6-9]\d{9}$', cleaned):
                raise ValueError('Invalid Indian mobile number format')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v


class UserProfile(BaseModel):
    """Complete user profile model"""
    profile_id: Optional[str] = Field(None, description="Unique profile identifier")
    
    # Core information sections
    demographics: Demographics = Field(..., description="Demographic information")
    economic: Economic = Field(..., description="Economic information")
    location: Location = Field(..., description="Location information")
    family: Family = Field(..., description="Family information")
    documents: Optional[Documents] = Field(None, description="Document information (encrypted)")
    preferences: Preferences = Field(default_factory=Preferences, description="User preferences")
    
    # Metadata
    created_at: Optional[datetime] = Field(None, description="Profile creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Profile update timestamp")
    version: int = Field(default=1, description="Profile version for audit trail")
    is_verified: bool = Field(default=False, description="Profile verification status")
    verification_date: Optional[datetime] = Field(None, description="Date of profile verification")
    
    # Data quality and completeness
    completeness_score: Optional[float] = Field(None, ge=0, le=1, description="Profile completeness score (0-1)")
    
    @validator('completeness_score', always=True)
    def calculate_completeness(cls, v, values):
        """Calculate profile completeness based on filled fields"""
        if v is not None:
            return v
        
        total_fields = 0
        filled_fields = 0
        
        # Check required sections
        for section in ['demographics', 'economic', 'location', 'family']:
            if section in values and values[section]:
                section_data = values[section]
                if hasattr(section_data, 'dict'):
                    section_dict = section_data.dict()
                    total_fields += len(section_dict)
                    filled_fields += sum(1 for val in section_dict.values() if val is not None)
        
        # Check optional sections
        if 'documents' in values and values['documents']:
            doc_data = values['documents'].dict()
            total_fields += len(doc_data)
            filled_fields += sum(1 for val in doc_data.values() if val is not None)
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Prevent extra fields
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "demographics": {
                    "age": 35,
                    "gender": "female",
                    "caste": "SC",
                    "marital_status": "married"
                },
                "economic": {
                    "annual_income": 120000,
                    "land_ownership": 2.5,
                    "employment_status": "farmer"
                },
                "location": {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "block": "Haveli",
                    "village": "Pirangut",
                    "pincode": "412108"
                },
                "family": {
                    "size": 4,
                    "dependents": 2,
                    "elderly_members": 1,
                    "children": 2
                },
                "documents": {
                    "aadhaar": "123456789012",
                    "pan": "ABCDE1234F",
                    "bank_account": "1234567890",
                    "bank_ifsc": "SBIN0001234"
                },
                "preferences": {
                    "language": "marathi",
                    "communication_channel": "sms",
                    "phone_number": "+919876543210",
                    "sms_notifications": True
                }
            }
        }


class UserProfileCreate(BaseModel):
    """Model for creating a new user profile"""
    demographics: Demographics
    economic: Economic
    location: Location
    family: Family
    documents: Optional[Documents] = None
    preferences: Optional[Preferences] = None


class UserProfileUpdate(BaseModel):
    """Model for updating user profile (partial updates allowed)"""
    demographics: Optional[Demographics] = None
    economic: Optional[Economic] = None
    location: Optional[Location] = None
    family: Optional[Family] = None
    documents: Optional[Documents] = None
    preferences: Optional[Preferences] = None


class UserProfileResponse(BaseModel):
    """Model for user profile API responses"""
    profile_id: str
    demographics: Demographics
    economic: Economic
    location: Location
    family: Family
    documents: Optional[Documents] = None  # Sensitive data may be masked
    preferences: Preferences
    created_at: datetime
    updated_at: datetime
    version: int
    is_verified: bool
    completeness_score: float