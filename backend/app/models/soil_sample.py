"""
SoilSample: D20-01 (docs/audit/FINAL_CANONICAL_group_A.md) - the keystone
scenario every other D20 row depends on. A sample-collection event,
mirroring crop_photo_session.py's session/record shape (an event that
later gets result data attached, rather than a single flat row).

self_tested is a computed property (lab_name is None), not a separate
stored column - storing both would let them disagree with each other for
no benefit.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SoilSample(Base):
    __tablename__ = "soil_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True)

    collection_date: Mapped[date] = mapped_column(Date, nullable=False)
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def self_tested(self) -> bool:
        return self.lab_name is None
