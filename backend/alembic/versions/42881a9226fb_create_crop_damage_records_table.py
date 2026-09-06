"""create crop damage records table

Revision ID: 42881a9226fb
Revises: b6f2afd218b8
Create Date: 2026-09-06 01:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42881a9226fb'
down_revision: Union[str, None] = 'b6f2afd218b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'crop_damage_records',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('crop_cycle_id', sa.UUID(), nullable=False),
        sa.Column('policy_id', sa.UUID(), nullable=False),
        sa.Column(
            'loss_type',
            sa.Enum('drought', 'flood', 'pest', 'disease', 'hail', 'fire', 'other', name='damage_loss_type'),
            nullable=False,
        ),
        sa.Column('extent_percent', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('occurred_on', sa.Date(), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('extent_percent >= 0 AND extent_percent <= 100', name='ck_crop_damage_records_extent_percent_range'),
        sa.ForeignKeyConstraint(['farmer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crop_cycle_id'], ['crop_cycles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['insurance_policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_crop_damage_records_farmer_id'), 'crop_damage_records', ['farmer_id'], unique=False)
    op.create_index(op.f('ix_crop_damage_records_crop_cycle_id'), 'crop_damage_records', ['crop_cycle_id'], unique=False)
    op.create_index(op.f('ix_crop_damage_records_policy_id'), 'crop_damage_records', ['policy_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_crop_damage_records_policy_id'), table_name='crop_damage_records')
    op.drop_index(op.f('ix_crop_damage_records_crop_cycle_id'), table_name='crop_damage_records')
    op.drop_index(op.f('ix_crop_damage_records_farmer_id'), table_name='crop_damage_records')
    op.drop_table('crop_damage_records')
    sa.Enum(name='damage_loss_type').drop(op.get_bind(), checkfirst=True)
