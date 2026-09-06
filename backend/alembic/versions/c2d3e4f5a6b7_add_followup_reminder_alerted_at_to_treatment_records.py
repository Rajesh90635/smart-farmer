"""add followup_reminder_alerted_at to treatment_records

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-09-07 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('treatment_records', sa.Column('followup_reminder_alerted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('treatment_records', 'followup_reminder_alerted_at')
