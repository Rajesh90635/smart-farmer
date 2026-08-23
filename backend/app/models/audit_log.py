"""
Append-only audit trail model.

This is the only business-adjacent table created in the foundation phase
(rather than waiting for a later module) because the development rules
require every state-changing action, from the very first one, to be
audit-logged. Every future module's migrations will assume this table
already exists.
"""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    entity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurred_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity", "entity_id"),
        Index("ix_audit_logs_occurred_at", "occurred_at_utc"),
    )
