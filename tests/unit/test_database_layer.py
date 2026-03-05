"""
Unit tests for database layer
Tests database models, connections, and basic CRUD operations
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database.base import Base
from shared.database.models import (
    UserProfileDB,
    GovernmentSchemeDB,
    ApplicationDB,
    ApplicationTrackingDB,
    DocumentDB,
    AuditLogDB,
    GenderEnum,
    CasteEnum,
    MaritalStatusEnum,
    EmploymentStatusEnum,
    LanguageEnum,
    CommunicationChannelEnum,
    ApplicationStatusEnum,
    SchemeStatusEnum,
)


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB
    
    # Replace JSONB with JSON for SQLite compatibility
    engine = create_engine("sqlite:///:memory:")
    
    # Monkey patch JSONB to JSON for SQLite
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
    
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_create_user_profile(test_db):
    """Test creating a user profile"""
    profile = UserProfileDB(
        id=uuid4(),
        name="Test User",
        age=35,
        gender=GenderEnum.MALE,
        caste=CasteEnum.OBC,
        marital_status=MaritalStatusEnum.MARRIED,
        annual_income=150000.00,
        land_ownership=2.5,
        employment_status=EmploymentStatusEnum.FARMER,
        state="Maharashtra",
        district="Pune",
        village="Test Village",
        family_size=4,
        dependents=2,
        language=LanguageEnum.MARATHI,
        communication_channel=CommunicationChannelEnum.SMS,
        phone_number="9876543210",
    )
    
    test_db.add(profile)
    test_db.commit()
    
    # Verify profile was created
    retrieved = test_db.query(UserProfileDB).filter_by(name="Test User").first()
    assert retrieved is not None
    assert retrieved.age == 35
    assert retrieved.annual_income == 150000.00
    assert retrieved.state == "Maharashtra"


def test_create_government_scheme(test_db):
    """Test creating a government scheme"""
    scheme = GovernmentSchemeDB(
        id=uuid4(),
        name="PM-KISAN",
        description="Direct income support to farmers",
        ministry="Ministry of Agriculture",
        status=SchemeStatusEnum.ACTIVE,
        eligibility_criteria={
            "age_range": {"min": 18, "max": 70},
            "land_ownership_limit": 5.0,
            "income_limit": 200000,
        },
        benefit_type="cash",
        benefit_amount=6000.00,
        benefit_frequency="yearly",
        processing_time_days=30,
    )
    
    test_db.add(scheme)
    test_db.commit()
    
    # Verify scheme was created
    retrieved = test_db.query(GovernmentSchemeDB).filter_by(name="PM-KISAN").first()
    assert retrieved is not None
    assert retrieved.benefit_amount == 6000.00
    assert retrieved.status == SchemeStatusEnum.ACTIVE


def test_create_application_with_relationships(test_db):
    """Test creating an application with user and scheme relationships"""
    # Create user profile
    user = UserProfileDB(
        id=uuid4(),
        name="Applicant User",
        age=40,
        gender=GenderEnum.FEMALE,
        caste=CasteEnum.SC,
        marital_status=MaritalStatusEnum.MARRIED,
        annual_income=100000.00,
        employment_status=EmploymentStatusEnum.LABORER,
        state="Karnataka",
        district="Bangalore",
    )
    test_db.add(user)
    
    # Create scheme
    scheme = GovernmentSchemeDB(
        id=uuid4(),
        name="Test Scheme",
        status=SchemeStatusEnum.ACTIVE,
        eligibility_criteria={"income_limit": 200000},
        benefit_amount=5000.00,
    )
    test_db.add(scheme)
    test_db.commit()
    
    # Create application
    application = ApplicationDB(
        id=uuid4(),
        user_id=user.id,
        scheme_id=scheme.id,
        form_data={"field1": "value1"},
        status=ApplicationStatusEnum.SUBMITTED,
        approval_probability=0.85,
    )
    test_db.add(application)
    test_db.commit()
    
    # Verify relationships
    retrieved = test_db.query(ApplicationDB).first()
    assert retrieved is not None
    assert retrieved.user_profile.name == "Applicant User"
    assert retrieved.scheme.name == "Test Scheme"
    assert retrieved.approval_probability == 0.85


def test_create_document(test_db):
    """Test creating a document record"""
    # Create user first
    user = UserProfileDB(
        id=uuid4(),
        name="Document Owner",
        age=30,
        gender=GenderEnum.MALE,
        caste=CasteEnum.GENERAL,
        marital_status=MaritalStatusEnum.SINGLE,
        annual_income=200000.00,
        employment_status=EmploymentStatusEnum.SELF_EMPLOYED,
        state="Tamil Nadu",
        district="Chennai",
    )
    test_db.add(user)
    test_db.commit()
    
    # Create document
    document = DocumentDB(
        id=uuid4(),
        user_id=user.id,
        document_type="aadhaar",
        extracted_data={"number": "XXXX-XXXX-1234", "name": "Document Owner"},
        validation_status="validated",
        quality_score=0.95,
    )
    test_db.add(document)
    test_db.commit()
    
    # Verify document
    retrieved = test_db.query(DocumentDB).filter_by(document_type="aadhaar").first()
    assert retrieved is not None
    assert retrieved.quality_score == 0.95
    assert retrieved.user_profile.name == "Document Owner"


def test_create_tracking_event(test_db):
    """Test creating an application tracking event"""
    # Create necessary records
    user = UserProfileDB(
        id=uuid4(),
        name="Tracked User",
        age=35,
        gender=GenderEnum.MALE,
        caste=CasteEnum.OBC,
        marital_status=MaritalStatusEnum.MARRIED,
        annual_income=150000.00,
        employment_status=EmploymentStatusEnum.FARMER,
        state="Maharashtra",
        district="Pune",
    )
    test_db.add(user)
    
    scheme = GovernmentSchemeDB(
        id=uuid4(),
        name="Tracked Scheme",
        status=SchemeStatusEnum.ACTIVE,
        eligibility_criteria={},
        benefit_amount=3000.00,
    )
    test_db.add(scheme)
    
    application = ApplicationDB(
        id=uuid4(),
        user_id=user.id,
        scheme_id=scheme.id,
        form_data={},
        status=ApplicationStatusEnum.SUBMITTED,
    )
    test_db.add(application)
    test_db.commit()
    
    # Create tracking event
    tracking = ApplicationTrackingDB(
        id=uuid4(),
        application_id=application.id,
        event_type="status_change",
        previous_status="draft",
        new_status="submitted",
        source_system="PM-KISAN",
        notification_sent=True,
        notification_channel="sms",
    )
    test_db.add(tracking)
    test_db.commit()
    
    # Verify tracking event
    retrieved = test_db.query(ApplicationTrackingDB).first()
    assert retrieved is not None
    assert retrieved.event_type == "status_change"
    assert retrieved.new_status == "submitted"
    assert retrieved.notification_sent is True


def test_create_audit_log(test_db):
    """Test creating an audit log entry"""
    audit = AuditLogDB(
        id=uuid4(),
        event_type="profile_created",
        entity_type="user_profile",
        entity_id=uuid4(),
        actor_id="user123",
        actor_type="user",
        action="create",
        changes={"field": "value"},
        ip_address="192.168.1.1",
    )
    
    test_db.add(audit)
    test_db.commit()
    
    # Verify audit log
    retrieved = test_db.query(AuditLogDB).filter_by(event_type="profile_created").first()
    assert retrieved is not None
    assert retrieved.action == "create"
    assert retrieved.ip_address == "192.168.1.1"


def test_cascade_delete_user_profile(test_db):
    """Test that deleting a user profile cascades to related records"""
    # Create user with related records
    user = UserProfileDB(
        id=uuid4(),
        name="Delete Test User",
        age=30,
        gender=GenderEnum.MALE,
        caste=CasteEnum.GENERAL,
        marital_status=MaritalStatusEnum.SINGLE,
        annual_income=150000.00,
        employment_status=EmploymentStatusEnum.FARMER,
        state="Test State",
        district="Test District",
    )
    test_db.add(user)
    
    document = DocumentDB(
        id=uuid4(),
        user_id=user.id,
        document_type="pan",
        extracted_data={},
        validation_status="pending",
    )
    test_db.add(document)
    test_db.commit()
    
    # Verify records exist
    assert test_db.query(UserProfileDB).filter_by(name="Delete Test User").first() is not None
    assert test_db.query(DocumentDB).filter_by(user_id=user.id).first() is not None
    
    # Delete user
    test_db.delete(user)
    test_db.commit()
    
    # Verify cascade delete
    assert test_db.query(UserProfileDB).filter_by(name="Delete Test User").first() is None
    assert test_db.query(DocumentDB).filter_by(user_id=user.id).first() is None


def test_jsonb_field_storage(test_db):
    """Test JSONB field storage and retrieval"""
    scheme = GovernmentSchemeDB(
        id=uuid4(),
        name="JSONB Test Scheme",
        status=SchemeStatusEnum.ACTIVE,
        eligibility_criteria={
            "age_range": {"min": 18, "max": 60},
            "caste_restriction": ["sc", "st"],
            "income_limit": 200000,
            "location_restriction": ["Maharashtra", "Karnataka"],
        },
        required_documents=["aadhaar", "pan", "bank_passbook"],
        benefit_amount=10000.00,
    )
    
    test_db.add(scheme)
    test_db.commit()
    
    # Retrieve and verify JSONB data
    retrieved = test_db.query(GovernmentSchemeDB).filter_by(name="JSONB Test Scheme").first()
    assert retrieved is not None
    assert retrieved.eligibility_criteria["age_range"]["min"] == 18
    assert "sc" in retrieved.eligibility_criteria["caste_restriction"]
    assert "aadhaar" in retrieved.required_documents
