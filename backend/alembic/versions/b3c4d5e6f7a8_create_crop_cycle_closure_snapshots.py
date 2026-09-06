"""create crop_cycle_closure_snapshots table for D97-02..09

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-09-06 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'crop_cycle_closure_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_cycle_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_cycles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('harvest_quantity', sa.Numeric(12, 2), nullable=True),
        sa.Column('harvest_quantity_unit', sa.String(20), nullable=True),
        sa.Column('quality_grade', sa.String(50), nullable=True),
        sa.Column('harvest_status', sa.String(20), nullable=True),
        sa.Column('actual_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('actual_revenue', sa.Numeric(12, 2), nullable=True),
        sa.Column('actual_profit_loss', sa.Numeric(12, 2), nullable=True),
        sa.Column('disease_summary', postgresql.JSONB, nullable=True),
        sa.Column('weather_impact_summary', postgresql.JSONB, nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_crop_cycle_closure_snapshots_crop_cycle_id', 'crop_cycle_closure_snapshots', ['crop_cycle_id'])


def downgrade() -> None:
    op.drop_index('ix_crop_cycle_closure_snapshots_crop_cycle_id', table_name='crop_cycle_closure_snapshots')
    op.drop_table('crop_cycle_closure_snapshots')
