"""add severe_weather_alert notification category for D14-09

Revision ID: 1e25cb4e88d7
Revises: 21f2c9cef22d
Create Date: 2026-09-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e25cb4e88d7'
down_revision: Union[str, None] = '21f2c9cef22d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'severe_weather_alert'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving 'severe_weather_alert'
    # in the type is harmless (no rows reference it after downgrade),
    # consistent with this project's existing note on enum-value migrations.
    pass
