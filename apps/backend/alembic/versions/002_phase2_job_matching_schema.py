"""Phase 2 Job Intelligence and Matching Schema Migration

Revision ID: 002_phase2_job_matching_schema
Revises: 001_phase1_core_schema
Create Date: 2026-09-30 22:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_phase2_job_matching_schema'
down_revision = '001_phase1_core_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. job_descriptions
    op.create_table(
        'job_descriptions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_job_descriptions_user_id'), 'job_descriptions', ['user_id'])
    op.create_index(op.f('ix_job_descriptions_status'), 'job_descriptions', ['status'])

    # 2. job_analyses
    op.create_table(
        'job_analyses',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('job_description_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_summary', sa.Text(), nullable=True),
        sa.Column('seniority_level', sa.String(length=100), nullable=True),
        sa.Column('years_experience_required', sa.Float(), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('responsibilities_json', sa.JSON(), nullable=True),
        sa.Column('qualifications_json', sa.JSON(), nullable=True),
        sa.Column('benefits_json', sa.JSON(), nullable=True),
        sa.Column('constraints_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_job_analyses_job_description_id'), 'job_analyses', ['job_description_id'], unique=True)

    # 3. job_requirements
    op.create_table(
        'job_requirements',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('job_description_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_job_requirements_job_description_id'), 'job_requirements', ['job_description_id'])
    op.create_index(op.f('ix_job_requirements_category'), 'job_requirements', ['category'])
    op.create_index(op.f('ix_job_requirements_requirement_type'), 'job_requirements', ['requirement_type'])

    # 4. job_skill_requirements
    op.create_table(
        'job_skill_requirements',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('job_description_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_requirement_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_requirements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('skill_name', sa.String(length=100), nullable=False),
        sa.Column('normalized_name', sa.String(length=100), nullable=False),
        sa.Column('skill_category', sa.String(length=50), nullable=True),
        sa.Column('requirement_type', sa.String(length=50), nullable=False, server_default='REQUIRED'),
        sa.Column('min_years_experience', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_job_skill_requirements_job_description_id'), 'job_skill_requirements', ['job_description_id'])
    op.create_index(op.f('ix_job_skill_requirements_normalized_name'), 'job_skill_requirements', ['normalized_name'])

    # 5. job_matches
    op.create_table(
        'job_matches',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('job_description_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_version_id', sa.Uuid(as_uuid=True), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('required_skills_score', sa.Float(), nullable=False),
        sa.Column('preferred_skills_score', sa.Float(), nullable=False),
        sa.Column('experience_score', sa.Float(), nullable=False),
        sa.Column('project_score', sa.Float(), nullable=False),
        sa.Column('semantic_score', sa.Float(), nullable=False),
        sa.Column('breakdown_json', sa.JSON(), nullable=True),
        sa.Column('matched_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missing_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('partial_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_job_matches_job_description_id'), 'job_matches', ['job_description_id'])
    op.create_index(op.f('ix_job_matches_resume_version_id'), 'job_matches', ['resume_version_id'])

    # 6. job_match_items
    op.create_table(
        'job_match_items',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('job_match_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_requirement_id', sa.Uuid(as_uuid=True), sa.ForeignKey('job_requirements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('candidate_source', sa.String(length=100), nullable=True),
        sa.Column('candidate_source_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_job_match_items_job_match_id'), 'job_match_items', ['job_match_id'])

    # 7. embedding_records
    op.create_table(
        'embedding_records',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_embedding_records_entity_type'), 'embedding_records', ['entity_type'])
    op.create_index(op.f('ix_embedding_records_entity_id'), 'embedding_records', ['entity_id'])


def downgrade() -> None:
    op.drop_table('embedding_records')
    op.drop_table('job_match_items')
    op.drop_table('job_matches')
    op.drop_table('job_skill_requirements')
    op.drop_table('job_requirements')
    op.drop_table('job_analyses')
    op.drop_table('job_descriptions')

