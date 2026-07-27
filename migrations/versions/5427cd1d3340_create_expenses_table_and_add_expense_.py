"""create expenses table and add expense_id to wallet_transactions

Revision ID: 5427cd1d3340
Revises: 7982b67ad04a
Create Date: 2026-07-27 23:32:45.562409

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5427cd1d3340'
down_revision: Union[str, Sequence[str], None] = '7982b67ad04a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('expenses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('wallet_id', sa.UUID(), nullable=False),
    sa.Column('category_id', sa.UUID(), nullable=False),
    sa.Column('montant', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('devise', sa.String(length=3), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('date_depense', sa.Date(), nullable=False),
    sa.Column('source', sa.Enum('MANUELLE', 'IA', name='expensesource'), nullable=False),
    sa.Column('est_recurrente', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.ForeignKeyConstraint(['devise'], ['devises.code_devise'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expenses_category_id'), 'expenses', ['category_id'], unique=False)
    op.create_index(op.f('ix_expenses_user_id'), 'expenses', ['user_id'], unique=False)
    op.create_index(op.f('ix_expenses_wallet_id'), 'expenses', ['wallet_id'], unique=False)
    op.add_column('wallet_transactions', sa.Column('expense_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'wallet_transactions_expense_id_fkey',
        'wallet_transactions', 'expenses',
        ['expense_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('wallet_transactions_expense_id_fkey', 'wallet_transactions', type_='foreignkey')
    op.drop_column('wallet_transactions', 'expense_id')
    op.drop_index(op.f('ix_expenses_wallet_id'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_user_id'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_category_id'), table_name='expenses')
    op.drop_table('expenses')
