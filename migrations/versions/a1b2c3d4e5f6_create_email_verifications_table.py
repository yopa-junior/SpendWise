"""create email_verifications table

Revision ID: a1b2c3d4e5f6
Revises: f664f3588098
Create Date: 2026-07-24 22:48:10.190020

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f664f3588098'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('email_verifications',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('otp_code', sa.String(length=6), nullable=False),
    sa.Column('purpose', sa.Enum('EMAIL_VERIFICATION', 'PASSWORD_RESET', 'EMAIL_CHANGE', name='otppurpose'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_email_verifications_otp_code', 'email_verifications', ['otp_code'])
    op.create_index('ix_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('ix_email_verifications_user_purpose', 'email_verifications', ['user_id', 'purpose'])


def downgrade() -> None:
    op.drop_index('ix_email_verifications_user_purpose', table_name='email_verifications')
    op.drop_index('ix_email_verifications_user_id', table_name='email_verifications')
    op.drop_index('ix_email_verifications_otp_code', table_name='email_verifications')
    op.drop_table('email_verifications')
