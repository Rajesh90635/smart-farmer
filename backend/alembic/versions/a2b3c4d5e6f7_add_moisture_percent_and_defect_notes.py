"""add moisture_percent and defect_notes to harvest_records

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-06 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('harvest_records', sa.Column('moisture_percent', sa.Numeric(5, 2), nullable=True))
    op.add_column('harvest_records', sa.Column('defect_notes', sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column('harvest_records', 'defect_notes')
    op.drop_column('harvest_records', 'moisture_percent')
