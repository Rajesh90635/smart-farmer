"""add device_id to refresh_tokens for D78-13 new-device-login detection

Revision ID: 21f2c9cef22d
Revises: e6f7a8b9c0d1
Create Date: 2026-09-06 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21f2c9cef22d'
down_revision: Union[str, None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('refresh_tokens', sa.Column('device_id', sa.String(255), nullable=True))
    op.create_index('ix_refresh_tokens_user_id_device_id', 'refresh_tokens', ['user_id', 'device_id'])


def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_user_id_device_id', table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'device_id')
