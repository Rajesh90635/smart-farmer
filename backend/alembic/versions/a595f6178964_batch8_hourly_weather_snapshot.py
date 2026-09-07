"""Missing Backlog Batch 8 (group 6): weather_snapshots hourly support

Revision ID: a595f6178964
Revises: cd0584254c03
Create Date: 2026-09-08 16:00:00.000000

D14-02: adds 'hourly' to the weather_snapshot_type enum and a nullable
hour_timestamp column - reuses the existing weather_snapshots table
(same "one table, snapshot_type distinguishes rows" convention as
CURRENT/FORECAST), rather than a new table. Additive only.

ALTER TYPE ... ADD VALUE cannot run inside the same transaction as a
statement that USES the new value, but running it alone in its own
migration transaction (nothing else in this migration touches
weather_snapshots.snapshot_type='hourly') is safe on Postgres 12+.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a595f6178964'
down_revision: Union[str, None] = 'cd0584254c03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE weather_snapshot_type ADD VALUE IF NOT EXISTS 'hourly'")
    op.add_column('weather_snapshots', sa.Column('hour_timestamp', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_weather_snapshots_hour_timestamp'), 'weather_snapshots', ['hour_timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_weather_snapshots_hour_timestamp'), table_name='weather_snapshots')
    op.drop_column('weather_snapshots', 'hour_timestamp')
    # Postgres has no ALTER TYPE ... DROP VALUE - removing 'hourly' from
    # the enum would require rebuilding the type; deliberately left as a
    # no-op downgrade limitation, same as any other native-enum addition.
