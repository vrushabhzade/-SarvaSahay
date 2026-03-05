"""
SQLAlchemy database models for SarvaSahay Platform
Maps to PostgreSQL tables with proper indexing and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Index, Enum as SQLEnum, DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from shared.database.base import Base


# Enums for type safety
class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CasteEnum(str, enum.Enum):
    GENERAL = "general"
    OBC = "obc"
    SC = "sc"
    ST = "st"


class MaritalStatusEnum(str, enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    WIDOWED = "widowed"
    DIVORCED = "divorced"


class EmploymentStatusEnum(str, enum.Enum):
    FARMER = "farmer"
    LABORER = "laborer"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"


class LanguageEnum(str, enum.Enum):
    HINDI = "hindi"
    MARATHI = "marathi"
    TAMIL = "tamil"
    BENGALI = "bengali"
    TELUGU = "telugu"
    KANNADA = "kannada"


class CommunicationChannelEnum(str, enum.Enum):
    SMS = "sms"
    VOICE = "voice"
    APP = "app"
    WEB = "web"


class ApplicationStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class SchemeStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserProfileDB(Base):
    """User profile table with comprehensive demographic and economic data"""
    __tablename__ = "user_profiles"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Personal information
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(SQLEnum(GenderEnum), nullable=False)
    caste = Column(SQLEnum(CasteEnum), nullable=False)
    marital_status = Column(SQLEnum(MaritalStatusEnum), nullable=False)
    
    # Economic information
    annual_income = Column(DECIMAL(12, 2), nullable=False)
    land_ownership = Column(DECIMAL(10, 2), default=0.0)  # in acres
    employment_status = Column(SQLEnum(EmploymentStatusEnum), nullable=False)
    bank_account = Column(String(50))
    
    # Location information
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    block = Column(String(100))
    village = Column(String(100))
    pincode = Column(String(10))
    
    # Family information
    family_size = Column(Integer, default=1)
    dependents = Column(Integer, default=0)
    elderly_members = Column(Integer, default=0)
    
    # Document references (encrypted IDs)
    aadhaar_encrypted = Column(String(255))
    pan_encrypted = Column(String(255))
    
    # Preferences
    language = Column(SQLEnum(LanguageEnum), default=LanguageEnum.HINDI)
    communication_channel = Column(SQLEnum(CommunicationChannelEnum), default=CommunicationChannelEnum.SMS)
    phone_number = Column(String(15))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    applications = relationship("ApplicationDB", back_populates="user_profile", cascade="all, delete-orphan")
    documents = relationship("DocumentDB", back_populates="user_profile", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_state_district", "state", "district"),
        Index("idx_user_income", "annual_income"),
        Index("idx_user_caste", "caste"),
        Index("idx_user_phone", "phone_number"),
        Index("idx_user_created_at", "created_at"),
    )


class GovernmentSchemeDB(Base):
    """Government scheme table with eligibility criteria and benefits"""
    __tablename__ = "government_schemes"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    ministry = Column(String(255))
    launch_date = Column(DateTime)
    status = Column(SQLEnum(SchemeStatusEnum), default=SchemeStatusEnum.ACTIVE)
    
    # Eligibility criteria (stored as JSONB for flexibility)
    eligibility_criteria = Column(JSONB, nullable=False)
    # Example structure:
    # {
    #   "age_range": {"min": 18, "max": 60},
    #   "gender_restriction": "any",
    #   "caste_restriction": ["sc", "st"],
    #   "income_limit": 200000,
    #   "land_ownership_limit": 5.0,
    #   "location_restriction": ["Maharashtra", "Karnataka"]
    # }
    
    # Benefits information
    benefit_type = Column(String(50))  # cash, subsidy, loan, insurance
    benefit_amount = Column(DECIMAL(12, 2))
    benefit_frequency = Column(String(50))  # one_time, monthly, quarterly, yearly
    benefit_duration = Column(Integer)  # in months
    
    # Application details
    form_template_id = Column(String(100))
    required_documents = Column(JSONB)  # List of required document types
    api_endpoint = Column(String(500))
    processing_time_days = Column(Integer)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relationships
    applications = relationship("ApplicationDB", back_populates="scheme")
    
    # Indexes
    __table_args__ = (
        Index("idx_scheme_status", "status"),
        Index("idx_scheme_name", "name"),
        Index("idx_scheme_ministry", "ministry"),
    )


class ApplicationDB(Base):
    """Application table tracking user applications to government schemes"""
    __tablename__ = "applications"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    scheme_id = Column(UUID(as_uuid=True), ForeignKey("government_schemes.id"), nullable=False)
    
    # Application data
    form_data = Column(JSONB, nullable=False)  # Complete form submission data
    submitted_documents = Column(JSONB)  # List of document IDs
    government_ref_number = Column(String(100), unique=True)
    
    # Status tracking
    status = Column(SQLEnum(ApplicationStatusEnum), default=ApplicationStatusEnum.DRAFT)
    status_history = Column(JSONB, default=list)  # List of status changes with timestamps
    
    # Predictions and analytics
    approval_probability = Column(Float)
    expected_processing_days = Column(Integer)
    suggested_improvements = Column(JSONB)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_status_update = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_profile = relationship("UserProfileDB", back_populates="applications")
    scheme = relationship("GovernmentSchemeDB", back_populates="applications")
    tracking_events = relationship("ApplicationTrackingDB", back_populates="application", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_app_user_id", "user_id"),
        Index("idx_app_scheme_id", "scheme_id"),
        Index("idx_app_status", "status"),
        Index("idx_app_gov_ref", "government_ref_number"),
        Index("idx_app_created_at", "created_at"),
        Index("idx_app_user_scheme", "user_id", "scheme_id"),
    )


class ApplicationTrackingDB(Base):
    """Application tracking events for real-time status monitoring"""
    __tablename__ = "application_tracking"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # status_change, payment, notification
    event_data = Column(JSONB)  # Additional event-specific data
    previous_status = Column(String(50))
    new_status = Column(String(50))
    
    # Source information
    source_system = Column(String(100))  # PM-KISAN, DBT, PFMS, etc.
    source_reference = Column(String(255))
    
    # Notification tracking
    notification_sent = Column(Boolean, default=False)
    notification_channel = Column(String(50))
    notification_sent_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    application = relationship("ApplicationDB", back_populates="tracking_events")
    
    # Indexes
    __table_args__ = (
        Index("idx_tracking_app_id", "application_id"),
        Index("idx_tracking_created_at", "created_at"),
        Index("idx_tracking_event_type", "event_type"),
    )


class DocumentDB(Base):
    """Document metadata table (raw images not stored)"""
    __tablename__ = "documents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Document information
    document_type = Column(String(50), nullable=False)  # aadhaar, pan, land_records, bank_passbook
    extracted_data = Column(JSONB)  # OCR extracted data (encrypted sensitive fields)
    validation_status = Column(String(50))  # validated, pending, failed
    validation_errors = Column(JSONB)  # List of validation issues
    
    # Quality assessment
    quality_score = Column(Float)  # 0.0 to 1.0
    improvement_suggestions = Column(JSONB)
    
    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    expires_at = Column(DateTime)  # For GDPR compliance
    
    # Relationships
    user_profile = relationship("UserProfileDB", back_populates="documents")
    
    # Indexes
    __table_args__ = (
        Index("idx_doc_user_id", "user_id"),
        Index("idx_doc_type", "document_type"),
        Index("idx_doc_uploaded_at", "uploaded_at"),
        Index("idx_doc_user_type", "user_id", "document_type"),
    )


class AuditLogDB(Base):
    """Audit log table for compliance and security tracking"""
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event information
    event_type = Column(String(100), nullable=False)  # profile_created, data_accessed, etc.
    entity_type = Column(String(50))  # user_profile, application, document
    entity_id = Column(UUID(as_uuid=True))
    
    # Actor information
    actor_id = Column(String(255))  # User or system identifier
    actor_type = Column(String(50))  # user, system, admin
    
    # Action details
    action = Column(String(100), nullable=False)  # create, read, update, delete
    changes = Column(JSONB)  # Before/after values for updates
    
    # Request context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    request_id = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_actor", "actor_id"),
        Index("idx_audit_created_at", "created_at"),
        Index("idx_audit_event_type", "event_type"),
    )
