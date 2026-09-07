"""Missing Backlog Batch 8 (group 2): task completion_percentage,
sale_orders.handling_charge

Revision ID: fc2b32df536e
Revises: 5b87cb6eb39c
Create Date: 2026-09-08 13:00:00.000000

D9-08: tasks.completion_percentage (farmer-entered, 0-100, nullable)
D58-04: sale_orders.handling_charge (itemized charge breakdown, same
    convention as transport_charge/commission_charge/storage_charge)

Both additive, both nullable - no existing column altered.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc2b32df536e'
down_revision: Union[str, None] = '5b87cb6eb39c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('completion_percentage', sa.Integer(), nullable=True))
    op.create_check_constraint(
        'ck_tasks_completion_percentage_range',
        'tasks',
        'completion_percentage IS NULL OR (completion_percentage >= 0 AND completion_percentage <= 100)',
    )
    op.add_column('sale_orders', sa.Column('handling_charge', sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('sale_orders', 'handling_charge')
    op.drop_constraint('ck_tasks_completion_percentage_range', 'tasks', type_='check')
    op.drop_column('tasks', 'completion_percentage')
