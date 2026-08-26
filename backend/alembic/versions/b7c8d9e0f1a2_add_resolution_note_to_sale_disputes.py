"""add resolution_note to sale disputes

Revision ID: b7c8d9e0f1a2
Revises: c1a2b3d4e5f6
Create Date: 2026-08-26 00:00:00.000000

Additive, backward-compatible column supporting the new admin
resolve/close/escalate endpoint for sale disputes - existing rows are
unaffected (nullable, no default).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sale_disputes', sa.Column('resolution_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('sale_disputes', 'resolution_note')
