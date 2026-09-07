"""Missing Backlog Batch 8 (group 7): plots.boundary_points

Revision ID: e9f7a17d3dd6
Revises: a595f6178964
Create Date: 2026-09-08 17:00:00.000000

D3-07: a farmer-drawn polygon boundary as a plain JSONB list of
{latitude, longitude} points - not a PostGIS geometry (PostGIS is not
enabled in this project). Additive, nullable.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e9f7a17d3dd6'
down_revision: Union[str, None] = 'a595f6178964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('plots', sa.Column('boundary_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('plots', 'boundary_points')
