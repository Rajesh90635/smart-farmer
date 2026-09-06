"""add itemized transport/commission/storage charges to sale_orders for D57-04/05/D58-02/03

Revision ID: 6701f6e3a235
Revises: ff72e5d0b5a7
Create Date: 2026-09-06 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6701f6e3a235'
down_revision: Union[str, None] = 'ff72e5d0b5a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sale_orders', sa.Column('transport_charge', sa.Numeric(12, 2), nullable=True))
    op.add_column('sale_orders', sa.Column('commission_charge', sa.Numeric(12, 2), nullable=True))
    op.add_column('sale_orders', sa.Column('storage_charge', sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('sale_orders', 'storage_charge')
    op.drop_column('sale_orders', 'commission_charge')
    op.drop_column('sale_orders', 'transport_charge')
