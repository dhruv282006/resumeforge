"""User Auth and Onboarding Schema Migration

Revision ID: 005_user_auth_schema
Revises: 004_applications_schema
Create Date: 2026-10-06 17:55:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_user_auth_schema'
down_revision = '004_applications_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'onboarding_completed')
    op.drop_column('users', 'hashed_password')
