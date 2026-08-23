"""
TreatmentRecord: Phase 34 - Treatment Effectiveness Tracking.

No ExpertRecommendation/treatment model existed anywhere in this
repository before this phase (confirmed by exhaustive search). Rather
than fabricate a "recommendation" concept, this reuses existing
structures wherever possible:
- case_id (nullable) reuses CropHealthCase for context - never
  duplicated.
- product_id (nullable) reuses Product (Prompt 9's agricultural input
  catalog) for "what was applied" - never a fabricated new product
  concept.
- before_analysis_id (nullable) is a SNAPSHOT REFERENCE to an existing
  AIAnalysis row (the most recent one for this crop cycle at the moment
  this treatment is recorded) - never a copy of disease-detection data.

Only the farmer who owns the crop cycle can create this record, so
"farmer confirmation that treatment was applied" is implicit in the act
of creating it - no separate boolean field was added for this, since it
would be redundant with ownership + creation itself.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TreatmentRecord(Base):
    __tablename__ = "treatment_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_health_cases.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    before_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_analyses.id", ondelete="SET NULL"), nullable=True
    )

    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
