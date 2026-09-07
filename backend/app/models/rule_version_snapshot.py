"""
RuleVersionSnapshot: D89-03 (docs/audit/FINAL_CANONICAL_group_D.md) -
effective-dated history of a rule module's real threshold values, letting
a later query answer "what were the thresholds on date X" and reproduce a
past decision. Never fabricated: every row's threshold_values is copied
verbatim from the real Settings values in force at the moment it was
recorded, never invented or backfilled for a date before this feature
existed.

Effective-dated, not a plain version log: exactly one row per rule_id has
effective_to = NULL at any time (the currently-active snapshot); recording
a new snapshot closes the previous open one first.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Identity, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RuleVersionSnapshot(Base):
    __tablename__ = "rule_version_snapshots"
    __table_args__ = (Index("ix_rule_version_snapshots_rule_id_effective_from", "rule_id", "effective_from"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    threshold_values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Monotonic tiebreaker for get_effective_at's "which snapshot is current
    # among ties" ordering - effective_from alone can tie (this codebase's
    # own tests backdate it to a fixed literal, and any real caller could in
    # principle record two snapshots in the same instant); id is a random
    # UUID4 with no correlation to insertion order, so a real DB-assigned
    # IDENTITY is used instead, mirroring CounterOffer.sequence.
    sequence: Mapped[int] = mapped_column(BigInteger, Identity(always=False), nullable=False)
