"""add perceptual_hash to crop_photos

Revision ID: f31007107fbd
Revises: fd90ec676715
Create Date: 2026-09-06 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f31007107fbd'
down_revision: Union[str, None] = 'fd90ec676715'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('crop_photos', sa.Column('perceptual_hash', sa.String(length=16), nullable=True))
    op.create_index(op.f('ix_crop_photos_perceptual_hash'), 'crop_photos', ['perceptual_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_crop_photos_perceptual_hash'), table_name='crop_photos')
    op.drop_column('crop_photos', 'perceptual_hash')
