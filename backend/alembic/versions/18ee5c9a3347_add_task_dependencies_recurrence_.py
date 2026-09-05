"""add task dependencies/recurrence, lessons learned, rule version, daily summary snapshot

Revision ID: 18ee5c9a3347
Revises: 1f4a1db926d6
Create Date: 2026-09-05 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '18ee5c9a3347'
down_revision: Union[str, None] = '1f4a1db926d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('depends_on_task_id', sa.UUID(), nullable=True))
    op.add_column('tasks', sa.Column('repeat_interval_days', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_tasks_depends_on_task_id_tasks', 'tasks', 'tasks', ['depends_on_task_id'], ['id'], ondelete='SET NULL'
    )
    op.create_check_constraint(
        'ck_tasks_repeat_interval_positive', 'tasks', 'repeat_interval_days IS NULL OR repeat_interval_days > 0'
    )

    op.add_column('crop_cycles', sa.Column('lessons_learned', sa.Text(), nullable=True))

    op.add_column('notifications', sa.Column('rule_version', sa.String(length=50), nullable=True))

    op.add_column('farmer_profiles', sa.Column('last_daily_summary_snapshot', postgresql.JSONB(), nullable=True))
    op.add_column('farmer_profiles', sa.Column('last_daily_summary_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('farmer_profiles', 'last_daily_summary_at')
    op.drop_column('farmer_profiles', 'last_daily_summary_snapshot')

    op.drop_column('notifications', 'rule_version')

    op.drop_column('crop_cycles', 'lessons_learned')

    op.drop_constraint('ck_tasks_repeat_interval_positive', 'tasks', type_='check')
    op.drop_constraint('fk_tasks_depends_on_task_id_tasks', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'repeat_interval_days')
    op.drop_column('tasks', 'depends_on_task_id')
