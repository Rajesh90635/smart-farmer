"""add pruning task type

Revision ID: fd90ec676715
Revises: ad3fdbbb5720
Create Date: 2026-09-06 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'fd90ec676715'
down_revision: Union[str, None] = 'ad3fdbbb5720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # D13-05 (docs/audit/FINAL_CANONICAL_group_A.md). Postgres requires
    # ADD VALUE to run outside the value's own usage transaction, but
    # allows it inside its own migration transaction on PG 12+ (this
    # project runs PG 18) as long as the new value isn't referenced in the
    # SAME transaction - it isn't, here.
    op.execute("ALTER TYPE task_type ADD VALUE IF NOT EXISTS 'pruning'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value - downgrading leaves
    # 'pruning' in the task_type type (harmless: an enum value with no
    # rows referencing it), consistent with this project's existing note
    # that "Enum types are not dropped by autogenerate."
    pass
