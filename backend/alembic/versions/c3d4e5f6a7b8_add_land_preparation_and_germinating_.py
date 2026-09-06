"""add land_preparation and germinating cultivation_status values

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-05 23:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE cultivation_status ADD VALUE IF NOT EXISTS 'land_preparation'")
    op.execute("ALTER TYPE cultivation_status ADD VALUE IF NOT EXISTS 'germinating'")
    # CropCycleStageHistory.status is backed by its OWN separate native
    # Postgres enum (same Python CultivationStatus, different `name=` in
    # SAEnum), so it needs the same two values added independently.
    op.execute("ALTER TYPE crop_cycle_stage_history_status ADD VALUE IF NOT EXISTS 'land_preparation'")
    op.execute("ALTER TYPE crop_cycle_stage_history_status ADD VALUE IF NOT EXISTS 'germinating'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving 'land_preparation'/
    # 'germinating' in either type is harmless (no rows reference them
    # after downgrade), consistent with this project's existing note on
    # enum-value migrations.
    pass
