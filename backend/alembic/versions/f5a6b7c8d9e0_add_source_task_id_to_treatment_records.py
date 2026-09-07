"""add source_task_id to treatment_records

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-09-08 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('treatment_records', sa.Column('source_task_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_treatment_records_source_task_id', 'treatment_records', 'tasks', ['source_task_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_treatment_records_source_task_id', 'treatment_records', type_='foreignkey')
    op.drop_column('treatment_records', 'source_task_id')
