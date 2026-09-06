"""add soil_test_reminder notification category

Revision ID: f3a8c9d1e5b2
Revises: 42881a9226fb
Create Date: 2026-09-06 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a8c9d1e5b2'
down_revision: Union[str, None] = '42881a9226fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'soil_test_reminder'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving 'soil_test_reminder'
    # in the type is harmless (no rows reference it after downgrade),
    # consistent with this project's existing note on enum-value migrations.
    pass
