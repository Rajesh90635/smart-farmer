"""Missing Backlog Batch 9: harvest_listings.packing_requirements

Revision ID: 54738ef35b1a
Revises: e9f7a17d3dd6
Create Date: 2026-09-07 00:00:00.000000

D52-03: farmer-declared packing/packaging requirement. Additive,
nullable - no existing column altered.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54738ef35b1a'
down_revision: Union[str, None] = 'e9f7a17d3dd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('harvest_listings', sa.Column('packing_requirements', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('harvest_listings', 'packing_requirements')
