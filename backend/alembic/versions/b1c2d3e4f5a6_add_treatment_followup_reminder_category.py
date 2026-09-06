"""add treatment_followup_reminder notification category

Revision ID: b1c2d3e4f5a6
Revises: a6b7c8d9e0f1
Create Date: 2026-09-07 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a6b7c8d9e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'treatment_followup_reminder'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving
    # 'treatment_followup_reminder' in the type is harmless (no rows
    # reference it after downgrade), consistent with this project's
    # existing note on enum-value migrations.
    pass
