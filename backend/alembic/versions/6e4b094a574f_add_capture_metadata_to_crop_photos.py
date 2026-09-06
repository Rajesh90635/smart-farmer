"""add capture metadata to crop_photos

D91-03 (docs/audit/FINAL_CANONICAL_group_D.md): optional, client-reported
device_model/capture_condition columns for AI governance traceability.

Revision ID: 6e4b094a574f
Revises: 9c134957c681
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision: str = '6e4b094a574f'
down_revision: str | None = '9c134957c681'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('crop_photos', sa.Column('device_model', sa.String(length=150), nullable=True))
    op.add_column('crop_photos', sa.Column('capture_condition', sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column('crop_photos', 'capture_condition')
    op.drop_column('crop_photos', 'device_model')
