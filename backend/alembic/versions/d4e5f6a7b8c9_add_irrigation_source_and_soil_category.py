"""add irrigation_source and soil_category to plots

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-05 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    irrigation_source = sa.Enum('rain_fed', 'borewell', 'canal', 'drip', 'sprinkler', 'other', name='irrigation_source')
    irrigation_source.create(op.get_bind(), checkfirst=True)
    op.add_column('plots', sa.Column('irrigation_source', irrigation_source, nullable=True))

    soil_category = sa.Enum('loamy', 'clayey', 'sandy', 'black_cotton', 'red', 'alluvial', 'other', name='soil_category')
    soil_category.create(op.get_bind(), checkfirst=True)
    op.add_column('plots', sa.Column('soil_category', soil_category, nullable=True))


def downgrade() -> None:
    op.drop_column('plots', 'soil_category')
    op.drop_column('plots', 'irrigation_source')
    sa.Enum(name='soil_category').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='irrigation_source').drop(op.get_bind(), checkfirst=True)
