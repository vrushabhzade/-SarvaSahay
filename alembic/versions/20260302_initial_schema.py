"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('gender', sa.Enum('MALE', 'FEMALE', 'OTHER', name='genderenum'), nullable=False),
        sa.Column('caste', sa.Enum('GENERAL', 'OBC', 'SC', 'ST', name='casteenum'), nullable=False),
        sa.Column('marital_status', sa.Enum('SINGLE', 'MARRIED', 'WIDOWED', 'DIVORCED', name='maritalstatusenum'), nullable=False),
        sa.Column('annual_income', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('land_ownership', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('employment_status', sa.Enum('FARMER', 'LABORER', 'SELF_EMPLOYED', 'UNEMPLOYED', name='employmentstatusenum'), nullable=False),
        sa.Column('bank_account', sa.String(length=50), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('block', sa.String(length=100), nullable=True),
        sa.Column('village', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('family_size', sa.Integer(), nullable=True),
        sa.Column('dependents', sa.Integer(), nullable=True),
        sa.Column('elderly_members', sa.Integer(), nullable=True),
        sa.Column('aadhaar_encrypted', sa.String(length=255), nullable=True),
        sa.Column('pan_encrypted', sa.String(length=255), nullable=True),
        sa.Column('language', sa.Enum('HINDI', 'MARATHI', 'TAMIL', 'BENGALI', 'TELUGU', 'KANNADA', name='languageenum'), nullable=True),
        sa.Column('communication_channel', sa.Enum('SMS', 'VOICE', 'APP', 'WEB', name='communicationchannelenum'), nullable=True),
        sa.Column('phone_number', sa.String(length=15), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_caste', 'user_profiles', ['caste'])
    op.create_index('idx_user_created_at', 'user_profiles', ['created_at'])
    op.create_index('idx_user_income', 'user_profiles', ['annual_income'])
    op.create_index('idx_user_phone', 'user_profiles', ['phone_number'])
    op.create_index('idx_user_state_district', 'user_profiles', ['state', 'district'])

    # Create government_schemes table
    op.create_table(
        'government_schemes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ministry', sa.String(length=255), nullable=True),
        sa.Column('launch_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', name='schemestatusenum'), nullable=True),
        sa.Column('eligibility_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('benefit_type', sa.String(length=50), nullable=True),
        sa.Column('benefit_amount', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('benefit_frequency', sa.String(length=50), nullable=True),
        sa.Column('benefit_duration', sa.Integer(), nullable=True),
        sa.Column('form_template_id', sa.String(length=100), nullable=True),
        sa.Column('required_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('processing_time_days', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_scheme_ministry', 'government_schemes', ['ministry'])
    op.create_index('idx_scheme_name', 'government_schemes', ['name'])
    op.create_index('idx_scheme_status', 'government_schemes', ['status'])

    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheme_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('submitted_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('government_ref_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'PAID', name='applicationstatusenum'), nullable=True),
        sa.Column('status_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('approval_probability', sa.Float(), nullable=True),
        sa.Column('expected_processing_days', sa.Integer(), nullable=True),
        sa.Column('suggested_improvements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_status_update', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['government_schemes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('government_ref_number')
    )
    op.create_index('idx_app_created_at', 'applications', ['created_at'])
    op.create_index('idx_app_gov_ref', 'applications', ['government_ref_number'])
    op.create_index('idx_app_scheme_id', 'applications', ['scheme_id'])
    op.create_index('idx_app_status', 'applications', ['status'])
    op.create_index('idx_app_user_id', 'applications', ['user_id'])
    op.create_index('idx_app_user_scheme', 'applications', ['user_id', 'scheme_id'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=True),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('improvement_suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_doc_type', 'documents', ['document_type'])
    op.create_index('idx_doc_uploaded_at', 'documents', ['uploaded_at'])
    op.create_index('idx_doc_user_id', 'documents', ['user_id'])
    op.create_index('idx_doc_user_type', 'documents', ['user_id', 'document_type'])

    # Create application_tracking table
    op.create_table(
        'application_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.Column('source_system', sa.String(length=100), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True),
        sa.Column('notification_channel', sa.String(length=50), nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tracking_app_id', 'application_tracking', ['application_id'])
    op.create_index('idx_tracking_created_at', 'application_tracking', ['created_at'])
    op.create_index('idx_tracking_event_type', 'application_tracking', ['event_type'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_id', sa.String(length=255), nullable=True),
        sa.Column('actor_type', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_actor', 'audit_logs', ['actor_id'])
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_event_type', 'audit_logs', ['event_type'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_audit_event_type', table_name='audit_logs')
    op.drop_index('idx_audit_entity', table_name='audit_logs')
    op.drop_index('idx_audit_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_actor', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_tracking_event_type', table_name='application_tracking')
    op.drop_index('idx_tracking_created_at', table_name='application_tracking')
    op.drop_index('idx_tracking_app_id', table_name='application_tracking')
    op.drop_table('application_tracking')
    
    op.drop_index('idx_doc_user_type', table_name='documents')
    op.drop_index('idx_doc_user_id', table_name='documents')
    op.drop_index('idx_doc_uploaded_at', table_name='documents')
    op.drop_index('idx_doc_type', table_name='documents')
    op.drop_table('documents')
    
    op.drop_index('idx_app_user_scheme', table_name='applications')
    op.drop_index('idx_app_user_id', table_name='applications')
    op.drop_index('idx_app_status', table_name='applications')
    op.drop_index('idx_app_scheme_id', table_name='applications')
    op.drop_index('idx_app_gov_ref', table_name='applications')
    op.drop_index('idx_app_created_at', table_name='applications')
    op.drop_table('applications')
    
    op.drop_index('idx_scheme_status', table_name='government_schemes')
    op.drop_index('idx_scheme_name', table_name='government_schemes')
    op.drop_index('idx_scheme_ministry', table_name='government_schemes')
    op.drop_table('government_schemes')
    
    op.drop_index('idx_user_state_district', table_name='user_profiles')
    op.drop_index('idx_user_phone', table_name='user_profiles')
    op.drop_index('idx_user_income', table_name='user_profiles')
    op.drop_index('idx_user_created_at', table_name='user_profiles')
    op.drop_index('idx_user_caste', table_name='user_profiles')
    op.drop_table('user_profiles')
    
    # Drop enums
    sa.Enum(name='communicationchannelenum').drop(op.get_bind())
    sa.Enum(name='languageenum').drop(op.get_bind())
    sa.Enum(name='employmentstatusenum').drop(op.get_bind())
    sa.Enum(name='maritalstatusenum').drop(op.get_bind())
    sa.Enum(name='casteenum').drop(op.get_bind())
    sa.Enum(name='genderenum').drop(op.get_bind())
    sa.Enum(name='schemestatusenum').drop(op.get_bind())
    sa.Enum(name='applicationstatusenum').drop(op.get_bind())
