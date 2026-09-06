"""add task priority, failed status, cancellation reason, overdue alert gate, task_alert notification category

Revision ID: a1b2c3d4e5f6
Revises: 18ee5c9a3347
Create Date: 2026-09-05 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '18ee5c9a3347'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE notification_category ADD VALUE IF NOT EXISTS 'task_alert'")

    task_priority = sa.Enum('low', 'medium', 'high', name='task_priority')
    task_priority.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'tasks',
        sa.Column('priority', task_priority, nullable=False, server_default='medium'),
    )
    op.alter_column('tasks', 'priority', server_default=None)

    op.add_column('tasks', sa.Column('cancellation_reason', sa.Text(), nullable=True))
    op.add_column('tasks', sa.Column('overdue_alerted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', 'overdue_alerted_at')
    op.drop_column('tasks', 'cancellation_reason')
    op.drop_column('tasks', 'priority')
    op.execute("DROP TYPE IF EXISTS task_priority")
    # Postgres cannot drop a single enum value - leaving 'task_alert'/'failed'
    # in their types is harmless (no rows reference them after downgrade),
    # consistent with this project's existing note on enum-value migrations.
