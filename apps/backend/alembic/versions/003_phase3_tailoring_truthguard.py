"""Phase 3 Tailoring and Truth Guard Schema Migration

Revision ID: 003_phase3_tailoring_truthguard
Revises: 002_phase2_job_matching_schema
Create Date: 2026-09-30 23:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_phase3_tailoring_truthguard'
down_revision = '002_phase2_job_matching_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. resume_tailoring_jobs
    op.create_table(
        'resume_tailoring_jobs',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_description_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='TAILORING_PROMPT_V1'),
        sa.Column('model_metadata', sa.JSON(), nullable=True),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_resume_tailoring_jobs_user_id'), 'resume_tailoring_jobs', ['user_id'])
    op.create_index(op.f('ix_resume_tailoring_jobs_resume_version_id'), 'resume_tailoring_jobs', ['resume_version_id'])
    op.create_index(op.f('ix_resume_tailoring_jobs_job_description_id'), 'resume_tailoring_jobs', ['job_description_id'])
    op.create_index(op.f('ix_resume_tailoring_jobs_status'), 'resume_tailoring_jobs', ['status'])

    # 2. resume_suggestions
    op.create_table(
        'resume_suggestions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tailoring_job_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resume_tailoring_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section', sa.String(length=50), nullable=False),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False),
        sa.Column('original_content', sa.Text(), nullable=True),
        sa.Column('proposed_content', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('truth_guard_status', sa.String(length=50), nullable=False, server_default='REQUIRES_REVIEW'),
        sa.Column('truth_guard_reason', sa.Text(), nullable=True),
        sa.Column('claim_breakdown_json', sa.JSON(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_resume_suggestions_tailoring_job_id'), 'resume_suggestions', ['tailoring_job_id'])
    op.create_index(op.f('ix_resume_suggestions_resume_version_id'), 'resume_suggestions', ['resume_version_id'])
    op.create_index(op.f('ix_resume_suggestions_section'), 'resume_suggestions', ['section'])
    op.create_index(op.f('ix_resume_suggestions_suggestion_type'), 'resume_suggestions', ['suggestion_type'])
    op.create_index(op.f('ix_resume_suggestions_status'), 'resume_suggestions', ['status'])
    op.create_index(op.f('ix_resume_suggestions_truth_guard_status'), 'resume_suggestions', ['truth_guard_status'])

    # 3. suggestion_evidence
    op.create_table(
        'suggestion_evidence',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('suggestion_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resume_suggestions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evidence_type', sa.String(length=50), nullable=False),
        sa.Column('evidence_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='USER_PROVIDED'),
        sa.Column('supporting_text', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_suggestion_evidence_suggestion_id'), 'suggestion_evidence', ['suggestion_id'])
    op.create_index(op.f('ix_suggestion_evidence_evidence_type'), 'suggestion_evidence', ['evidence_type'])


def downgrade() -> None:
    op.drop_table('suggestion_evidence')
    op.drop_table('resume_suggestions')
    op.drop_table('resume_tailoring_jobs')
