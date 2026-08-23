"""
AssistantConversation/AssistantMessage: the farmer's chat history with the
Smart Farmer Assistant. Every AssistantMessage from the assistant records
its intent, which tools were actually called, and which sources backed
the answer - never a black box. This is what makes "source-aware
responses" a real, queryable fact, not just a UI label.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MessageRole(str, enum.Enum):
    FARMER = "farmer"
    ASSISTANT = "assistant"


class ConfidenceLevel(str, enum.Enum):
    HIGH_CONFIDENCE = "high_confidence"
    MEDIUM_CONFIDENCE = "medium_confidence"
    LOW_CONFIDENCE = "low_confidence"


class AssistantConversation(Base):
    __tablename__ = "assistant_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    messages: Mapped[list["AssistantMessage"]] = relationship(back_populates="conversation", order_by="AssistantMessage.created_at")


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="assistant_message_role", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    intent: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tools_called: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[ConfidenceLevel | None] = mapped_column(
        SAEnum(ConfidenceLevel, name="assistant_confidence_level", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation: Mapped["AssistantConversation"] = relationship(back_populates="messages")
