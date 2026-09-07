"""add monotonic sequence tiebreaker to rule_version_snapshots

Revision ID: 7fb0f206a5a5
Revises: 54738ef35b1a
Create Date: 2026-09-07 00:00:00.000000

Fixes a disclosed, evidence-confirmed clock-tie bug in
test_rule_versioning.py::test_a_query_for_an_old_date_still_reproduces_the_old_decision_after_a_threshold_change:
get_effective_at ordered purely by effective_from DESC, which is not a
reliable tiebreaker when multiple snapshots share the exact same
effective_from (the test itself backdates to a fixed literal
datetime(2020, 1, 1), so repeated full-suite runs against the persistent
shared test database accumulate many rows with that identical value).
RuleVersionSnapshot.id is a random UUID4 with no correlation to insertion
order, so a real monotonically-increasing Postgres IDENTITY column is
added instead, mirroring the same fix already applied to
counter_offers.sequence (revision 5b57af46965e).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fb0f206a5a5'
down_revision: Union[str, None] = '54738ef35b1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'rule_version_snapshots',
        sa.Column('sequence', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('rule_version_snapshots', 'sequence')
