"""add farmer correction fields to ai_analyses

Revision ID: 1f4a1db926d6
Revises: b8069da2cd90
Create Date: 2026-09-05 10:02:15.277368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f4a1db926d6'
down_revision: Union[str, None] = 'b8069da2cd90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_analyses', sa.Column('farmer_correction', sa.String(length=30), nullable=True))
    op.add_column('ai_analyses', sa.Column('farmer_correction_notes', sa.String(length=1000), nullable=True))
    op.add_column('ai_analyses', sa.Column('farmer_corrected_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_analyses', 'farmer_corrected_at')
    op.drop_column('ai_analyses', 'farmer_correction_notes')
    op.drop_column('ai_analyses', 'farmer_correction')
