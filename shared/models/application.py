"""
Application Data Models
Pydantic models for government scheme applications and tracking
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ApplicationStatus(str, Enum):
    """Application status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ApplicationPriority(str, Enum):
    """Application priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class StatusHistory(BaseModel):
    """Application status change history"""
    status: ApplicationStatus = Field(..., description="Status value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When status changed")
    reason: Optional[str] = Field(None, description="Reason for status change")
    updated_by: Optional[str] = Field(None, description="Who updated the status")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        use_enum_values = True


class ApplicationPredictions(BaseModel):
    """AI predictions for application outcome"""
    approval_probability: float = Field(..., ge=0, le=1, description="Probability of approval (0-1)")
    expected_processing_days: int = Field(..., ge=0, description="Expected processing time in days")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in predictions (0-1)")
    suggested_improvements: List[str] = Field(default_factory=list, description="Suggestions to improve approval chances")
    risk_factors: List[str] = Field(default_factory=list, description="Factors that may lead to rejection")
    
    @validator('approval_probability', 'confidence_score')
    def validate_probability(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Probability values must be between 0 and 1')
        return v


class PaymentDetails(BaseModel):
    """Payment and disbursement details"""
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="Payment status")
    expected_amount: Optional[float] = Field(None, ge=0, description="Expected benefit amount")
    actual_amount: Optional[float] = Field(None, ge=0, description="Actual amount received")
    payment_date: Optional[datetime] = Field(None, description="Date of payment")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    payment_method: Optional[str] = Field(None, description="Payment method (DBT, cheque, etc.)")
    bank_account: Optional[str] = Field(None, description="Bank account for payment")
    
    class Config:
        use_enum_values = True


class Application(BaseModel):
    """Government scheme application model"""
    application_id: Optional[str] = Field(None, description="Unique application identifier")
    
    # References
    user_id: str = Field(..., description="User profile ID")
    scheme_id: str = Field(..., description="Government scheme ID")
    
    # Application data
    form_data: Dict[str, Any] = Field(..., description="Filled form data")
    submitted_documents: List[str] = Field(default_factory=list, description="List of submitted document IDs")
    government_ref_number: Optional[str] = Field(None, description="Government reference/acknowledgment number")
    
    # Status tracking
    status: ApplicationStatus = Field(default=ApplicationStatus.DRAFT, description="Current application status")
    status_history: List[StatusHistory] = Field(default_factory=list, description="Status change history")
    last_status_update: datetime = Field(default_factory=datetime.utcnow, description="Last status update timestamp")
    
    # AI predictions
    predictions: Optional[ApplicationPredictions] = Field(None, description="AI-generated predictions")
    
    # Payment information
    payment: Optional[PaymentDetails] = Field(None, description="Payment and disbursement details")
    
    # Priority and tracking
    priority: ApplicationPriority = Field(default=ApplicationPriority.MEDIUM, description="Application priority")
    follow_up_date: Optional[datetime] = Field(None, description="Date for follow-up action")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Application creation timestamp")
    submitted_at: Optional[datetime] = Field(None, description="Application submission timestamp")
    completed_at: Optional[datetime] = Field(None, description="Application completion timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Additional tracking
    retry_count: int = Field(default=0, ge=0, description="Number of submission retries")
    error_messages: List[str] = Field(default_factory=list, description="Error messages if any")
    
    @validator('status_history', always=True)
    def ensure_status_history(cls, v, values):
        """Ensure status history includes current status"""
        if not v and 'status' in values:
            return [StatusHistory(
                status=values['status'],
                timestamp=datetime.utcnow(),
                reason="Initial status"
            )]
        return v
    
    def add_status_change(self, new_status: ApplicationStatus, reason: Optional[str] = None, 
                         updated_by: Optional[str] = None, notes: Optional[str] = None):
        """Add a status change to history"""
        self.status = new_status
        self.last_status_update = datetime.utcnow()
        self.status_history.append(StatusHistory(
            status=new_status,
            timestamp=self.last_status_update,
            reason=reason,
            updated_by=updated_by,
            notes=notes
        ))
        self.updated_at = datetime.utcnow()
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "scheme_id": "PM-KISAN",
                "form_data": {
                    "farmer_name": "Ramesh Kumar",
                    "land_area": "2.5",
                    "bank_account": "1234567890"
                },
                "submitted_documents": ["doc-001", "doc-002"],
                "government_ref_number": "PMKISAN2024001234",
                "status": "submitted",
                "predictions": {
                    "approval_probability": 0.85,
                    "expected_processing_days": 30,
                    "confidence_score": 0.92,
                    "suggested_improvements": [],
                    "risk_factors": []
                }
            }
        }


class ApplicationCreate(BaseModel):
    """Model for creating a new application"""
    user_id: str
    scheme_id: str
    form_data: Dict[str, Any]
    submitted_documents: Optional[List[str]] = None
    priority: Optional[ApplicationPriority] = ApplicationPriority.MEDIUM


class ApplicationUpdate(BaseModel):
    """Model for updating an application"""
    form_data: Optional[Dict[str, Any]] = None
    submitted_documents: Optional[List[str]] = None
    status: Optional[ApplicationStatus] = None
    government_ref_number: Optional[str] = None
    predictions: Optional[ApplicationPredictions] = None
    payment: Optional[PaymentDetails] = None
    priority: Optional[ApplicationPriority] = None
    follow_up_date: Optional[datetime] = None


class ApplicationResponse(BaseModel):
    """Model for application API responses"""
    application_id: str
    user_id: str
    scheme_id: str
    form_data: Dict[str, Any]
    submitted_documents: List[str]
    government_ref_number: Optional[str]
    status: ApplicationStatus
    status_history: List[StatusHistory]
    last_status_update: datetime
    predictions: Optional[ApplicationPredictions]
    payment: Optional[PaymentDetails]
    priority: ApplicationPriority
    created_at: datetime
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime


class ApplicationSummary(BaseModel):
    """Lightweight application summary for listings"""
    application_id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    status: ApplicationStatus
    benefit_amount: Optional[float] = None
    submitted_at: Optional[datetime]
    last_status_update: datetime
    approval_probability: Optional[float] = None
    
    class Config:
        use_enum_values = True
