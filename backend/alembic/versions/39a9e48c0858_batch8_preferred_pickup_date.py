"""Missing Backlog Batch 8 (group 4): harvest_listings.preferred_pickup_date

Revision ID: 39a9e48c0858
Revises: fc2b32df536e
Create Date: 2026-09-08 14:00:00.000000

D55-05: farmer-declared preferred pickup/delivery date. Additive,
nullable - no existing column altered.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39a9e48c0858'
down_revision: Union[str, None] = 'fc2b32df536e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('harvest_listings', sa.Column('preferred_pickup_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('harvest_listings', 'preferred_pickup_date')
