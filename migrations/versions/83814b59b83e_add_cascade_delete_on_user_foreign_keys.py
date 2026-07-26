"""add cascade delete on user foreign keys

Revision ID: 83814b59b83e
Revises: a1b2c3d4e5f6
Create Date: 2026-07-24 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '83814b59b83e'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('refresh_tokens_user_id_fkey', 'refresh_tokens', type_='foreignkey')
    op.create_foreign_key(
        'refresh_tokens_user_id_fkey', 'refresh_tokens', 'users',
        ['user_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_constraint('email_verifications_user_id_fkey', 'email_verifications', type_='foreignkey')
    op.create_foreign_key(
        'email_verifications_user_id_fkey', 'email_verifications', 'users',
        ['user_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('email_verifications_user_id_fkey', 'email_verifications', type_='foreignkey')
    op.create_foreign_key(
        'email_verifications_user_id_fkey', 'email_verifications', 'users',
        ['user_id'], ['id']
    )
    op.drop_constraint('refresh_tokens_user_id_fkey', 'refresh_tokens', type_='foreignkey')
    op.create_foreign_key(
        'refresh_tokens_user_id_fkey', 'refresh_tokens', 'users',
        ['user_id'], ['id']
    )
