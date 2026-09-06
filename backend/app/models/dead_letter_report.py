"""
DeadLetterReport: D87-02 (docs/audit/FINAL_CANONICAL_group_D.md). A
best-effort, farmer-authenticated report the client posts the first time
a queued photo upload transitions to needsManualAction (pending_upload_queue.dart)
- this is the entire "dead-letter" concept's only server-side visibility
today; it is a report of an on-device event, never itself the queue.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DeadLetterReport(Base):
    __tablename__ = "dead_letter_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_upload_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
