"""D27-02 symptom_description, D36-03 case_reviews evidence, D38-01 next_check_due_date

Revision ID: dddfe33f4f32
Revises: a2f94d64b787
Create Date: 2026-09-06 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'dddfe33f4f32'
down_revision: Union[str, None] = 'a2f94d64b787'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('crop_health_cases', sa.Column('symptom_description', sa.String(500), nullable=True))
    op.add_column('case_reviews', sa.Column('evidence_photo_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('case_reviews', sa.Column('evidence_analysis_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('treatment_records', sa.Column('next_check_due_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('treatment_records', 'next_check_due_date')
    op.drop_column('case_reviews', 'evidence_analysis_ids')
    op.drop_column('case_reviews', 'evidence_photo_ids')
    op.drop_column('crop_health_cases', 'symptom_description')
