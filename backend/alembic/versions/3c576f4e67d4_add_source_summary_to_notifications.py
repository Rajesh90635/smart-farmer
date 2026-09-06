"""add source_summary to notifications

D88-01 (docs/audit/FINAL_CANONICAL_group_D.md): which subsystem produced
this notification.

Revision ID: 3c576f4e67d4
Revises: cc42c79c3e70
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision: str = '3c576f4e67d4'
down_revision: str | None = 'cc42c79c3e70'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('notifications', sa.Column('source_summary', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('notifications', 'source_summary')
