"""add reminder_alerted_at to soil_test_results

Revision ID: a6b7c8d9e0f1
Revises: f3a8c9d1e5b2
Create Date: 2026-09-06 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'f3a8c9d1e5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('soil_test_results', sa.Column('reminder_alerted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('soil_test_results', 'reminder_alerted_at')
