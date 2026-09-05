"""add payment_alert notification category

Revision ID: b8069da2cd90
Revises: d7557ced4b7b
Create Date: 2026-09-05 09:43:46.728838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8069da2cd90'
down_revision: Union[str, None] = 'd7557ced4b7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'payment_alert'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving 'payment_alert'
    # in the type is harmless (no rows reference it after downgrade),
    # consistent with this project's existing note on enum-value migrations.
    pass
