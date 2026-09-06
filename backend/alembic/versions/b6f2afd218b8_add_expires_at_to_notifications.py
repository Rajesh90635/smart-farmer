"""add expires_at to notifications

Revision ID: b6f2afd218b8
Revises: f31007107fbd
Create Date: 2026-09-06 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6f2afd218b8'
down_revision: Union[str, None] = 'f31007107fbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('notifications', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('notifications', 'expires_at')
