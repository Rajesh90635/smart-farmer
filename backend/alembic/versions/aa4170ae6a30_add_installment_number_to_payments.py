"""add installment_number to payments

Revision ID: aa4170ae6a30
Revises: 3c576f4e67d4
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa4170ae6a30'
down_revision: Union[str, None] = '3c576f4e67d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('payments', sa.Column('installment_number', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('payments', 'installment_number')
