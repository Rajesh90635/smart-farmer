"""
CaseReview: structured review submission. The outcome MUST be one of a
controlled set (validated at the service layer against role-specific
allowed values) - `notes` is optional supplementary free text, never the
sole result.

AI_RESULT / EXPERT_RESULT / FIELD_AGENT_OBSERVATION / FARMER_CONFIRMATION
are kept separate: AIAnalysis is untouched; this table is an ADDITIVE
record, never an edit to the AI row.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ReviewerRole(str, enum.Enum):
    EXPERT = "expert"
    FIELD_AGENT = "field_agent"


EXPERT_OUTCOMES = ("confirmed", "different_diagnosis", "insufficient_image", "needs_more_information", "no_disease_visible")
FIELD_AGENT_OUTCOMES = ("healthy_looking", "possible_disease", "needs_expert", "needs_better_photo", "field_visit_required")


class CaseReview(Base):
    __tablename__ = "case_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_health_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_assignments.id", ondelete="CASCADE"), nullable=False)
    professional_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False)

    reviewer_role: Mapped[ReviewerRole] = mapped_column(
        SAEnum(ReviewerRole, name="reviewer_role", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    alternative_disease_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    case: Mapped["CropHealthCase"] = relationship(back_populates="reviews")
