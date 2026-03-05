"""
Government Scheme Data Models
Pydantic models for government schemes and eligibility criteria
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class SchemeType(str, Enum):
    """Government scheme types"""
    AGRICULTURE = "agriculture"
    EMPLOYMENT = "employment"
    HOUSING = "housing"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    SOCIAL_SECURITY = "social-security"
    FINANCIAL_INCLUSION = "financial-inclusion"


class SchemeStatus(str, Enum):
    """Scheme status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DISCONTINUED = "discontinued"


class EligibilityCategory(str, Enum):
    """Eligibility assessment categories"""
    DEFINITELY_ELIGIBLE = "Definitely Eligible"
    LIKELY_ELIGIBLE = "Likely Eligible"
    CONDITIONAL = "Conditional"
    NOT_ELIGIBLE = "Not Eligible"


class NumericCriteria(BaseModel):
    """Numeric range criteria (age, income, land, etc.)"""
    min_value: Optional[float] = Field(None, description="Minimum value (inclusive)")
    max_value: Optional[float] = Field(None, description="Maximum value (inclusive)")
    
    @validator('max_value')
    def validate_range(cls, v, values):
        if v is not None and 'min_value' in values and values['min_value'] is not None:
            if v < values['min_value']:
                raise ValueError('max_value cannot be less than min_value')
        return v


class EligibilityCriteria(BaseModel):
    """Comprehensive eligibility criteria for a scheme"""
    # Demographic criteria
    age: Optional[NumericCriteria] = Field(None, description="Age requirements")
    gender: Optional[List[str]] = Field(None, description="Allowed genders")
    caste: Optional[List[str]] = Field(None, description="Allowed caste categories")
    marital_status: Optional[List[str]] = Field(None, description="Allowed marital statuses")
    
    # Economic criteria
    annual_income: Optional[NumericCriteria] = Field(None, description="Income requirements")
    land_ownership: Optional[NumericCriteria] = Field(None, description="Land ownership requirements")
    employment_status: Optional[List[str]] = Field(None, description="Allowed employment statuses")
    
    # Location criteria
    states: Optional[List[str]] = Field(None, description="Eligible states")
    rural_only: Optional[bool] = Field(None, description="Rural areas only")
    
    # Family criteria
    family_size: Optional[NumericCriteria] = Field(None, description="Family size requirements")
    dependents: Optional[NumericCriteria] = Field(None, description="Dependents requirements")
    
    # Additional criteria
    custom_criteria: Optional[Dict[str, Any]] = Field(None, description="Custom scheme-specific criteria")


class GovernmentScheme(BaseModel):
    """Government scheme model"""
    scheme_id: str = Field(..., description="Unique scheme identifier")
    name: str = Field(..., min_length=5, max_length=200, description="Scheme name")
    description: str = Field(..., min_length=10, max_length=1000, description="Scheme description")
    scheme_type: SchemeType = Field(..., description="Type of scheme")
    
    # Financial details
    benefit_amount: int = Field(..., gt=0, description="Benefit amount in INR")
    benefit_frequency: str = Field(..., description="Benefit frequency (annual, monthly, one-time)")
    
    # Eligibility
    eligibility_criteria: EligibilityCriteria = Field(..., description="Eligibility requirements")
    
    # Administrative details
    implementing_agency: str = Field(..., description="Government agency implementing the scheme")
    application_process: str = Field(..., description="How to apply for the scheme")
    required_documents: List[str] = Field(..., description="Required documents for application")
    
    # Status and metadata
    status: SchemeStatus = Field(default=SchemeStatus.ACTIVE, description="Current scheme status")
    launch_date: Optional[datetime] = Field(None, description="Scheme launch date")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # API integration details
    api_endpoint: Optional[str] = Field(None, description="Government API endpoint for applications")
    api_version: Optional[str] = Field(None, description="API version")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "scheme_id": "PM-KISAN",
                "name": "Pradhan Mantri Kisan Samman Nidhi",
                "description": "Income support scheme for farmers providing ₹6000 per year",
                "scheme_type": "agriculture",
                "benefit_amount": 6000,
                "benefit_frequency": "annual",
                "eligibility_criteria": {
                    "land_ownership": {"min_value": 0.1, "max_value": 2.0},
                    "employment_status": ["farmer"],
                    "annual_income": {"max_value": 200000},
                    "rural_only": True
                },
                "implementing_agency": "Ministry of Agriculture and Farmers Welfare",
                "application_process": "Online application through PM-KISAN portal",
                "required_documents": ["Aadhaar Card", "Bank Account Details", "Land Records"],
                "status": "active",
                "api_endpoint": "https://api.pmkisan.gov.in/v1/applications",
                "api_version": "1.0"
            }
        }


class EligibilityResult(BaseModel):
    """Result of eligibility evaluation for a scheme"""
    scheme_id: str = Field(..., description="Scheme identifier")
    scheme_name: str = Field(..., description="Scheme name")
    benefit_amount: int = Field(..., description="Benefit amount")
    eligibility_score: float = Field(..., ge=0, le=1, description="Eligibility confidence score (0-1)")
    category: EligibilityCategory = Field(..., description="Eligibility category")
    reasons: List[str] = Field(default_factory=list, description="Reasons for eligibility/ineligibility")
    required_actions: List[str] = Field(default_factory=list, description="Actions needed to become eligible")
    
    class Config:
        use_enum_values = True


class EligibilityEvaluation(BaseModel):
    """Complete eligibility evaluation result"""
    profile_id: str = Field(..., description="User profile ID")
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Evaluation timestamp")
    total_schemes_evaluated: int = Field(..., description="Total number of schemes evaluated")
    eligible_schemes: List[EligibilityResult] = Field(..., description="List of eligible schemes")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "profile_id": "user-123",
                "total_schemes_evaluated": 30,
                "eligible_schemes": [
                    {
                        "scheme_id": "PM-KISAN",
                        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi",
                        "benefit_amount": 6000,
                        "eligibility_score": 0.95,
                        "category": "Definitely Eligible",
                        "reasons": ["Meets income criteria", "Valid farmer status", "Land ownership within limits"],
                        "required_actions": []
                    }
                ],
                "processing_time_seconds": 2.3
            }
        }