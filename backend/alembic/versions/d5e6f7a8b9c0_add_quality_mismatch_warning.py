"""add quality_mismatch_warning to sale_orders for D59-04

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-09-06 00:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sale_orders', sa.Column('quality_mismatch_warning', sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column('sale_orders', 'quality_mismatch_warning')
