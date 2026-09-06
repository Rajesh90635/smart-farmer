"""add dispute_alert and security_alert notification categories

Revision ID: f1a2b3c4d5e6
Revises: 381e2dc405e4
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '381e2dc405e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'dispute_alert'")
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'security_alert'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving 'dispute_alert'/
    # 'security_alert' in the type is harmless (no rows reference them
    # after downgrade), consistent with this project's existing note on
    # enum-value migrations.
    pass
