"""create insurance policies table

Revision ID: d0f4e71b1d13
Revises: aa4170ae6a30
Create Date: 2026-09-06 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0f4e71b1d13'
down_revision: Union[str, None] = 'aa4170ae6a30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'insurance_policies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('crop_id', sa.UUID(), nullable=True),
        sa.Column('policy_number', sa.String(length=100), nullable=False),
        sa.Column('insurer', sa.String(length=200), nullable=False),
        sa.Column('sum_insured', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('premium', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('season', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['farmer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crop_id'], ['crop_master.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_insurance_policies_farmer_id'), 'insurance_policies', ['farmer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_insurance_policies_farmer_id'), table_name='insurance_policies')
    op.drop_table('insurance_policies')
