"""add failure_reason and resown_from_crop_cycle_id to crop_cycles

Revision ID: d7557ced4b7b
Revises: fb6859bdd48d
Create Date: 2026-09-05 08:35:05.154609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7557ced4b7b'
down_revision: Union[str, None] = 'fb6859bdd48d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('crop_cycles', sa.Column('failure_reason', sa.String(length=50), nullable=True))
    op.add_column('crop_cycles', sa.Column('resown_from_crop_cycle_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_crop_cycles_resown_from_crop_cycle_id', 'crop_cycles', 'crop_cycles',
        ['resown_from_crop_cycle_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_crop_cycles_resown_from_crop_cycle_id', 'crop_cycles', type_='foreignkey')
    op.drop_column('crop_cycles', 'resown_from_crop_cycle_id')
    op.drop_column('crop_cycles', 'failure_reason')
