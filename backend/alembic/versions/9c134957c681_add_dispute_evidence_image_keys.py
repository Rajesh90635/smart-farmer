"""add evidence_image_key to order_disputes and sale_disputes for D67-03

Revision ID: 9c134957c681
Revises: 6701f6e3a235
Create Date: 2026-09-06 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c134957c681'
down_revision: Union[str, None] = '6701f6e3a235'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order_disputes', sa.Column('evidence_image_key', sa.String(500), nullable=True))
    op.add_column('sale_disputes', sa.Column('evidence_image_key', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('sale_disputes', 'evidence_image_key')
    op.drop_column('order_disputes', 'evidence_image_key')
