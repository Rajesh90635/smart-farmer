"""
OrderDispute: farmer-raised issue after delivery (or non-delivery). Photo
evidence upload is NOT built this phase (disclosed gap) - evidence_note
is free text only.

Refund: foundation only - no real payment-gateway refund API integration
exists (only SANDBOX payments exist this phase), so a "COMPLETED" refund
here means the sandbox/manual bookkeeping marked it complete, never a
real money movement. Never auto-completed without a business-rule check
in the service layer.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DisputeReason(str, enum.Enum):
    WRONG_PRODUCT = "wrong_product"
    MISSING_ITEM = "missing_item"
    DAMAGED_PRODUCT = "damaged_product"
    PAYMENT_ISSUE = "payment_issue"
    DELIVERY_ISSUE = "delivery_issue"
    UNEXPECTED_CHARGE = "unexpected_charge"
    PRODUCT_AUTHENTICITY_CONCERN = "product_authenticity_concern"


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class OrderDispute(Base):
    __tablename__ = "order_disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    reason: Mapped[DisputeReason] = mapped_column(
        SAEnum(DisputeReason, name="dispute_reason", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[DisputeStatus] = mapped_column(
        SAEnum(DisputeStatus, name="dispute_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=DisputeStatus.OPEN,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RefundType(str, enum.Enum):
    FULL_REFUND = "full_refund"
    PARTIAL_REFUND = "partial_refund"
    NO_REFUND = "no_refund"


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    dispute_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("order_disputes.id", ondelete="SET NULL"), nullable=True)

    refund_type: Mapped[RefundType] = mapped_column(
        SAEnum(RefundType, name="refund_type", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[RefundStatus] = mapped_column(
        SAEnum(RefundStatus, name="refund_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=RefundStatus.PENDING,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
