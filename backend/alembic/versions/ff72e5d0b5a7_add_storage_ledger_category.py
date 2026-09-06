"""add storage ledger category for D69-08

Revision ID: ff72e5d0b5a7
Revises: dddfe33f4f32
Create Date: 2026-09-06 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff72e5d0b5a7'
down_revision: Union[str, None] = 'dddfe33f4f32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE ledger_category ADD VALUE IF NOT EXISTS 'storage'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - leaving 'storage' in the
    # type is harmless (no rows reference it after downgrade), consistent
    # with this project's existing note on enum-value migrations.
    pass
