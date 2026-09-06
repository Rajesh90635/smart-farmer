"""create rule version snapshots table

Revision ID: ad3fdbbb5720
Revises: d0f4e71b1d13
Create Date: 2026-09-06 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ad3fdbbb5720'
down_revision: Union[str, None] = 'd0f4e71b1d13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rule_version_snapshots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('rule_id', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('threshold_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rule_version_snapshots_rule_id'), 'rule_version_snapshots', ['rule_id'], unique=False)
    op.create_index(
        'ix_rule_version_snapshots_rule_id_effective_from', 'rule_version_snapshots', ['rule_id', 'effective_from'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_rule_version_snapshots_rule_id_effective_from', table_name='rule_version_snapshots')
    op.drop_index(op.f('ix_rule_version_snapshots_rule_id'), table_name='rule_version_snapshots')
    op.drop_table('rule_version_snapshots')
