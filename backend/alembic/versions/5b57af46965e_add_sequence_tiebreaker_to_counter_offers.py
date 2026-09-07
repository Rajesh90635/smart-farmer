"""add monotonic sequence tiebreaker to counter_offers

Revision ID: 5b57af46965e
Revises: a7b8c9d0e1f2
Create Date: 2026-09-08 11:00:00.000000

Fixes an evidence-confirmed clock-tie bug: get_latest_counter_offer ordered
purely by created_at DESC, which is not a reliable "latest" indicator when
two counters are inserted within the same timestamp tick (observed in
test_offer_and_counter_offer_negotiation_history_is_never_overwritten).
CounterOffer.id is a random UUID4 and cannot serve as a tiebreaker (no
correlation to insertion order), so a real monotonically-increasing
Postgres IDENTITY column is added instead.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b57af46965e'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'counter_offers',
        sa.Column('sequence', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('counter_offers', 'sequence')
