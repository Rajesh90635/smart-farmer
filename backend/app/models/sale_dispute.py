"""
SaleDispute: generic sale-level dispute. QualityDispute is a 1:1
extension holding fields ONLY relevant to a quality disagreement - kept
separate from SaleDispute so the base dispute table doesn't carry
quality-specific columns that are null for every non-quality dispute
reason.

SaleFeedback: ONE table serving both farmer-gives-feedback-on-buyer and
buyer-gives-feedback-on-farmer, distinguished by given_by_role - avoids
two near-duplicate tables for what is structurally the same shape.

DemandSignal: honestly empty by default ("do not invent demand data").
No seed data populates this table; it exists so an admin can enter a
documented-source signal later, mirroring the ReferencePrice honesty
pattern from Prompt 9.
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SaleDisputeReason(str, enum.Enum):
    WRONG_QUANTITY = "wrong_quantity"
    QUALITY_DISAGREEMENT = "quality_disagreement"
    PRICE_DISAGREEMENT = "price_disagreement"
    PAYMENT_ISSUE = "payment_issue"
    DELIVERY_ISSUE = "delivery_issue"
    BUYER_CANCELLATION = "buyer_cancellation"
    FARMER_CANCELLATION = "farmer_cancellation"
    DAMAGED_CROP = "damaged_crop"
    OTHER = "other"


class SaleDisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class SaleDispute(Base):
    __tablename__ = "sale_disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    raised_by_role: Mapped[str] = mapped_column(String(20), nullable=False)

    reason: Mapped[SaleDisputeReason] = mapped_column(
        SAEnum(SaleDisputeReason, name="sale_dispute_reason", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[SaleDisputeStatus] = mapped_column(
        SAEnum(SaleDisputeStatus, name="sale_dispute_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=SaleDisputeStatus.OPEN,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QualityDispute(Base):
    __tablename__ = "quality_disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_dispute_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_disputes.id", ondelete="CASCADE"), unique=True, nullable=False)

    agreed_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    buyer_claimed_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    farmer_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SaleFeedback(Base):
    __tablename__ = "sale_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    given_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    given_by_role: Mapped[str] = mapped_column(String(20), nullable=False)

    helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DemandLevel(str, enum.Enum):
    HIGH_DEMAND = "high_demand"
    NORMAL = "normal"
    LOW_DEMAND = "low_demand"


class DemandSignal(Base):
    __tablename__ = "demand_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="CASCADE"), nullable=False, index=True)
    region: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    level: Mapped[DemandLevel] = mapped_column(
        SAEnum(DemandLevel, name="demand_level", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
