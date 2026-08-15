"""
Payment: the abstraction supports UPI/CARD/NET_BANKING/COD/SANDBOX as
provider values, but ONLY SANDBOX is actually implemented this phase - no
real gateway integration. NEVER stores card numbers, CVV, UPI PINs, or
banking passwords - there are no such columns at all, structurally
impossible to store them here by accident.

An order is only ever marked PAID by payment_service after a Payment row
here actually reaches SUCCESS - never inferred or assumed.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PaymentProvider(str, enum.Enum):
    SANDBOX = "sandbox"
    UPI = "upi"
    CARD = "card"
    NET_BANKING = "net_banking"
    CASH_ON_DELIVERY = "cash_on_delivery"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Exactly one of order_id/sale_order_id is set per row - enforced at
    # the service layer (Prompt 10 reuses this table for harvest-sale
    # payments rather than creating a duplicate SalePayment table; see
    # docs/PAYMENT_AND_SETTLEMENT.md). Not a DB CHECK constraint - kept
    # simple and validated in code, consistent with how this project
    # already handles several other "exactly one of" invariants.
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    sale_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=True, index=True)

    provider: Mapped[PaymentProvider] = mapped_column(
        SAEnum(PaymentProvider, name="payment_provider", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
