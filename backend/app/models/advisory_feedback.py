"""
Phase 39: AdvisoryFeedback.

WHY THIS IS A GENUINELY NEW TABLE (confirmed by inspection first): the
existing AssistantFeedback (Prompt 11) is foreign-keyed to
assistant_messages.id - it can ONLY represent feedback on the original
farmer-wide assistant's PERSISTED conversation messages. None of Phase
33 (Crop Risk Score), Phase 36 (crop-scoped Assistant), Phase 37
(Weather Action Engine), or Phase 38 (Performance/Comparison/ROI/
Irrigation) persist any row that a feedback record could reference -
they are all deterministic, computed-on-read responses.

source_type + source_reference identify WHICH advisory the feedback is
about without requiring that advisory to have its own persisted row -
source_reference is a free-form identifier meaningful only within its
source_type, since the underlying advisories are stateless by design.

Reuses the EXISTING feedback vocabulary already established in
AssistantFeedback (helpful/not_helpful/wrong/need_expert) rather than
inventing a second, incompatible feedback vocabulary.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AdvisorySourceType(str, enum.Enum):
    CROP_ASSISTANT = "crop_assistant"
    RISK_SCORE = "risk_score"
    WEATHER_ACTION = "weather_action"
    IRRIGATION_INTELLIGENCE = "irrigation_intelligence"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"


class AdvisoryFeedbackType(str, enum.Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    WRONG = "wrong"
    NEED_EXPERT = "need_expert"


class AdvisoryFeedback(Base):
    __tablename__ = "advisory_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type: Mapped[AdvisorySourceType] = mapped_column(
        SAEnum(AdvisorySourceType, name="advisory_source_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    source_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    feedback_type: Mapped[AdvisoryFeedbackType] = mapped_column(
        SAEnum(AdvisoryFeedbackType, name="advisory_feedback_type", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
