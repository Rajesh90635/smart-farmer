"""add variety_id to products for D21-03

Revision ID: a2f94d64b787
Revises: 1e25cb4e88d7
Create Date: 2026-09-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a2f94d64b787'
down_revision: Union[str, None] = '1e25cb4e88d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('variety_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_products_variety_id_crop_varieties', 'products', 'crop_varieties', ['variety_id'], ['id']
    )
    op.create_index('ix_products_variety_id', 'products', ['variety_id'])


def downgrade() -> None:
    op.drop_index('ix_products_variety_id', table_name='products')
    op.drop_constraint('fk_products_variety_id_crop_varieties', 'products', type_='foreignkey')
    op.drop_column('products', 'variety_id')
