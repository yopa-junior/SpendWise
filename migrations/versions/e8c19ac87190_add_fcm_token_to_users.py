"""add fcm_token to users

Revision ID: e8c19ac87190
Revises: 49284eaca544
Create Date: 2026-08-23 23:05:03.389296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8c19ac87190'
down_revision: Union[str, Sequence[str], None] = '49284eaca544'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ✅ Ajoute la colonne fcm_token à la table users
    op.add_column('users', sa.Column('fcm_token', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # ✅ Supprime la colonne fcm_token
    op.drop_column('users', 'fcm_token')