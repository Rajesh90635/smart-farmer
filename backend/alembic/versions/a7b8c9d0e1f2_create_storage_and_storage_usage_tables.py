"""create storage and storage_usage tables

Revision ID: a7b8c9d0e1f2
Revises: a6b7c8d9e0f2
Create Date: 2026-09-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'a6b7c8d9e0f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'storages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('location', sa.String(length=500), nullable=False),
        sa.Column(
            'storage_type',
            sa.Enum('on_farm', 'rented_warehouse', 'cold_storage', 'godown', 'other', name='storage_type'),
            nullable=False,
        ),
        sa.Column('capacity', sa.Numeric(12, 2), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('cost_per_unit_per_day', sa.Numeric(12, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['farmer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_storages_farmer_id'), 'storages', ['farmer_id'], unique=False)

    op.create_table(
        'storage_usages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('storage_id', sa.UUID(), nullable=False),
        sa.Column('harvest_record_id', sa.UUID(), nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 2), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('stored_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['storage_id'], ['storages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['harvest_record_id'], ['harvest_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['farmer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_storage_usages_storage_id'), 'storage_usages', ['storage_id'], unique=False)
    op.create_index(op.f('ix_storage_usages_harvest_record_id'), 'storage_usages', ['harvest_record_id'], unique=False)
    op.create_index(op.f('ix_storage_usages_farmer_id'), 'storage_usages', ['farmer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_storage_usages_farmer_id'), table_name='storage_usages')
    op.drop_index(op.f('ix_storage_usages_harvest_record_id'), table_name='storage_usages')
    op.drop_index(op.f('ix_storage_usages_storage_id'), table_name='storage_usages')
    op.drop_table('storage_usages')

    op.drop_index(op.f('ix_storages_farmer_id'), table_name='storages')
    op.drop_table('storages')
    sa.Enum(name='storage_type').drop(op.get_bind(), checkfirst=True)
