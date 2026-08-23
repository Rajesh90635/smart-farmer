"""
CropHealthCase: connects Farmer -> Farm -> Plot -> CropCycle -> Photo ->
AIAnalysis -> Professional -> Verification.

Only 10 statuses (exact list, no extras) and 4 priorities. `reason`
records WHY the case exists (first four triggers only this phase) - never
silently created without a traceable reason.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    WAITING_FOR_ASSIGNMENT = "waiting_for_assignment"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    NEEDS_MORE_INFORMATION = "needs_more_information"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CaseReason(str, enum.Enum):
    FARMER_REQUESTED = "farmer_requested"
    AI_LOW_CONFIDENCE = "ai_low_confidence"
    AI_UNKNOWN = "ai_unknown"
    FARMER_DISPUTE = "farmer_dispute"


class CropHealthCase(Base):
    __tablename__ = "crop_health_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    plot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_photo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_photos.id", ondelete="SET NULL"), nullable=True)
    ai_analysis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_analyses.id", ondelete="SET NULL"), nullable=True)

    requested_professional_role: Mapped[str] = mapped_column(String(50), nullable=False)

    reason: Mapped[CaseReason] = mapped_column(
        SAEnum(CaseReason, name="case_reason", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, name="case_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=CaseStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[CasePriority] = mapped_column(
        SAEnum(CasePriority, name="case_priority", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=CasePriority.MEDIUM,
        nullable=False,
    )

    final_verified_class: Mapped[str | None] = mapped_column(String(150), nullable=True)
    final_verification_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    second_opinion_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignments: Mapped[list["CaseAssignment"]] = relationship(back_populates="case", order_by="CaseAssignment.assigned_at")
    reviews: Mapped[list["CaseReview"]] = relationship(back_populates="case")
