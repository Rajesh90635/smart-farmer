"""create crop_grade_options table for D52-02/D51-03

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-09-06 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'crop_grade_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_master.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade_code', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('crop_id', 'grade_code', name='uq_crop_grade_options_crop_code'),
    )
    op.create_index('ix_crop_grade_options_crop_id', 'crop_grade_options', ['crop_id'])


def downgrade() -> None:
    op.drop_index('ix_crop_grade_options_crop_id', table_name='crop_grade_options')
    op.drop_table('crop_grade_options')
