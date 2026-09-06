"""add is_sorted and sorting_notes to harvest_listings for D52-01

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-09-06 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('harvest_listings', sa.Column('is_sorted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('harvest_listings', sa.Column('sorting_notes', sa.String(500), nullable=True))
    op.alter_column('harvest_listings', 'is_sorted', server_default=None)


def downgrade() -> None:
    op.drop_column('harvest_listings', 'sorting_notes')
    op.drop_column('harvest_listings', 'is_sorted')
