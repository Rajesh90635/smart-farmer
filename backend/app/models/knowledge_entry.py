"""
KnowledgeEntry: RAG foundation. Deliberately empty by default this phase
(no seed rows) - no vetted, licensed agricultural content source was
available to populate this table from within this environment. Mirrors
the exact honesty pattern already established for ReferencePrice (Prompt
9) and DemandSignal (Prompt 10).

AIEvaluationRecord: a lightweight record for offline evaluation, mostly
populated from farmer feedback rather than a live automated evaluation
pipeline (no LLM judge is available in this environment either).
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LicenseStatus(str, enum.Enum):
    OPEN_LICENSE = "open_license"
    PUBLIC_DOMAIN = "public_domain"
    OFFICIAL_GOVERNMENT_SOURCE = "official_government_source"
    INTERNAL_APPROVED_SUMMARY = "internal_approved_summary"


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    crop_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="SET NULL"), nullable=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    content_summary: Mapped[str] = mapped_column(Text, nullable=False)

    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_status: Mapped[LicenseStatus] = mapped_column(
        SAEnum(LicenseStatus, name="knowledge_license_status", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    version_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AIEvaluationRecord(Base):
    __tablename__ = "ai_evaluation_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assistant_messages.id", ondelete="SET NULL"), nullable=True)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grounded: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    safety_flag_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    farmer_reported_issue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
