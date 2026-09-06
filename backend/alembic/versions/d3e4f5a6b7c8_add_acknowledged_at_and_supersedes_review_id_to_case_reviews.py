"""add acknowledged_at and supersedes_review_id to case_reviews

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-09-07 09:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('case_reviews', sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('case_reviews', sa.Column('supersedes_review_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_case_reviews_supersedes_review_id', 'case_reviews', 'case_reviews', ['supersedes_review_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_case_reviews_supersedes_review_id', 'case_reviews', type_='foreignkey')
    op.drop_column('case_reviews', 'supersedes_review_id')
    op.drop_column('case_reviews', 'acknowledged_at')
