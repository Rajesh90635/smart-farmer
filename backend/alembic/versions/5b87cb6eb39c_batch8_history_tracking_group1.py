"""Missing Backlog Batch 8 (group 1): plot soil/water history, crop-cycle
season history, water availability, harvest certificate reference

Revision ID: 5b87cb6eb39c
Revises: 5b57af46965e
Create Date: 2026-09-08 12:00:00.000000

D13-02: crop_cycle_season_history (append-only season-change log)
D17-02/D17-03: plots.water_availability (farmer-declared; water_shortage
    is a derived property, no column needed)
D17-06: plot_water_history (append-only water_availability-change log)
D19-04: plot_soil_history (append-only soil_type/soil_category-change log)
D51-06: harvest_listings.certificate_reference (farmer-declared, nullable)

All additive - no existing column is altered, renamed, or dropped, and
every new column is nullable. Safe to run against data already in place;
idempotent in the sense that alembic tracks it has already run (no
if-not-exists dance needed, this is a single fresh set of objects).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b87cb6eb39c'
down_revision: Union[str, None] = '5b57af46965e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    water_availability = sa.Enum('adequate', 'limited', 'scarce', name='water_availability')
    water_availability.create(op.get_bind(), checkfirst=True)
    op.add_column('plots', sa.Column('water_availability', water_availability, nullable=True))

    op.add_column(
        'harvest_listings',
        sa.Column('certificate_reference', sa.String(length=200), nullable=True),
    )

    # NOTE: unlike water_availability above (added via add_column, which
    # needs the type pre-created), the enums below are used directly as
    # create_table column types - create_table emits their CREATE TYPE
    # itself, so no separate .create() call here (would double-create).
    season_history_season = sa.Enum(
        'kharif', 'rabi', 'zaid', 'perennial', 'other', name='crop_cycle_season_history_season'
    )
    op.create_table(
        'crop_cycle_season_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('crop_cycle_id', sa.UUID(), nullable=False),
        sa.Column('season', season_history_season, nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['crop_cycle_id'], ['crop_cycles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_crop_cycle_season_history_crop_cycle_id'), 'crop_cycle_season_history', ['crop_cycle_id'], unique=False
    )

    soil_history_category = sa.Enum(
        'loamy', 'clayey', 'sandy', 'black_cotton', 'red', 'alluvial', 'other',
        name='plot_soil_history_soil_category',
    )
    op.create_table(
        'plot_soil_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plot_id', sa.UUID(), nullable=False),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('soil_category', soil_history_category, nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plot_soil_history_plot_id'), 'plot_soil_history', ['plot_id'], unique=False)

    water_history_availability = sa.Enum('adequate', 'limited', 'scarce', name='plot_water_history_water_availability')
    op.create_table(
        'plot_water_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plot_id', sa.UUID(), nullable=False),
        sa.Column('water_availability', water_history_availability, nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plot_water_history_plot_id'), 'plot_water_history', ['plot_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_plot_water_history_plot_id'), table_name='plot_water_history')
    op.drop_table('plot_water_history')
    op.drop_index(op.f('ix_plot_soil_history_plot_id'), table_name='plot_soil_history')
    op.drop_table('plot_soil_history')
    op.drop_index(op.f('ix_crop_cycle_season_history_crop_cycle_id'), table_name='crop_cycle_season_history')
    op.drop_table('crop_cycle_season_history')
    op.drop_column('harvest_listings', 'certificate_reference')
    op.drop_column('plots', 'water_availability')
    sa.Enum(name='water_availability').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='plot_water_history_water_availability').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='plot_soil_history_soil_category').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='crop_cycle_season_history_season').drop(op.get_bind(), checkfirst=True)
