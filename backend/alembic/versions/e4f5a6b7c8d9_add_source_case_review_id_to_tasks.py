"""add source_case_review_id to tasks

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-09-08 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('source_case_review_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_tasks_source_case_review_id', 'tasks', 'case_reviews', ['source_case_review_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_tasks_source_case_review_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'source_case_review_id')
