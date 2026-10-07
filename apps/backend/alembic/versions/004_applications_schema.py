"""Phase 4 Applications Schema Migration

Revision ID: 004_applications_schema
Revises: 003_phase3_tailoring_truthguard
Create Date: 2026-10-05 20:50:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_applications_schema'
down_revision = '003_phase3_tailoring_truthguard'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'applications',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resume_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resume_version_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='APPLIED'),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('salary_range', sa.String(length=100), nullable=True),
        sa.Column('job_url', sa.Text(), nullable=True),
        sa.Column('applied_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_applications_user_id', 'applications', ['user_id'])
    op.create_index('ix_applications_job_id', 'applications', ['job_id'])
    op.create_index('ix_applications_status', 'applications', ['status'])


def downgrade() -> None:
    op.drop_index('ix_applications_status', table_name='applications')
    op.drop_index('ix_applications_job_id', table_name='applications')
    op.drop_index('ix_applications_user_id', table_name='applications')
    op.drop_table('applications')
