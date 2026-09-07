"""create farm_infrastructure table

Revision ID: a6b7c8d9e0f2
Revises: f5a6b7c8d9e0
Create Date: 2026-09-08 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f2'
down_revision: Union[str, None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'farm_infrastructure',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farm_id', sa.UUID(), nullable=False),
        sa.Column(
            'infrastructure_type',
            sa.Enum('storage', 'well', 'borewell', 'shed', 'equipment', 'other', name='farm_infrastructure_type'),
            nullable=False,
        ),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_farm_infrastructure_farm_id'), 'farm_infrastructure', ['farm_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_farm_infrastructure_farm_id'), table_name='farm_infrastructure')
    op.drop_table('farm_infrastructure')
    sa.Enum(name='farm_infrastructure_type').drop(op.get_bind(), checkfirst=True)
