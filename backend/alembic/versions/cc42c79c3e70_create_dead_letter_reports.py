"""create dead_letter_reports

D87-02 (docs/audit/FINAL_CANONICAL_group_D.md): farmer-authenticated,
best-effort reports of on-device dead-lettered uploads.

Revision ID: cc42c79c3e70
Revises: 6e4b094a574f
Create Date: 2026-09-06
"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'cc42c79c3e70'
down_revision: str | None = '6e4b094a574f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'dead_letter_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_upload_id', sa.String(length=100), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_dead_letter_reports_farmer_id', 'dead_letter_reports', ['farmer_id'])


def downgrade() -> None:
    op.drop_index('ix_dead_letter_reports_farmer_id', table_name='dead_letter_reports')
    op.drop_table('dead_letter_reports')
