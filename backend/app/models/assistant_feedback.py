"""
AssistantFeedback: farmer's own judgment of one assistant answer.
AssistantPreference: response-mode/voice/summary UX preferences - kept
separate from NotificationPreference (Prompt 7), which governs
notification CHANNELS, not assistant UX behavior.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class FeedbackType(str, enum.Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    WRONG = "wrong"
    NEED_EXPERT = "need_expert"


class AssistantFeedback(Base):
    __tablename__ = "assistant_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assistant_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    feedback_type: Mapped[FeedbackType] = mapped_column(
        SAEnum(FeedbackType, name="assistant_feedback_type", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ResponseMode(str, enum.Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"


class AssistantPreference(Base):
    __tablename__ = "assistant_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    response_mode: Mapped[ResponseMode] = mapped_column(
        SAEnum(ResponseMode, name="assistant_response_mode", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=ResponseMode.SIMPLE,
        nullable=False,
    )
    voice_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    daily_summary_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    proactive_suggestions_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
