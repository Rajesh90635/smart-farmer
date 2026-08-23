"""
TreatmentFollowUp: linked to a TreatmentRecord. after_analysis_id
references a NEW, real AIAnalysis row created through the EXISTING
photo-upload/analyze pipeline (Prompt 6) - never a duplicate disease
detection, never a second AI call invented for this phase.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TreatmentFollowUp(Base):
    __tablename__ = "treatment_follow_ups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    treatment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("treatment_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    after_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_analyses.id", ondelete="SET NULL"), nullable=True
    )

    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
