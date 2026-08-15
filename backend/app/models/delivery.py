"""
Delivery: a clean, simple abstraction ("do not implement a complex
logistics system if it is not needed yet"). No delivery-partner entity,
no GPS tracking - just status + estimate, matching what this platform can
honestly support right now.
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Exactly one of order_id/sale_order_id is set per row - same reuse
    # pattern as Payment above, see docs/PAYMENT_AND_SETTLEMENT.md.
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=True)
    sale_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sale_orders.id", ondelete="CASCADE"), unique=True, nullable=True)

    status: Mapped[DeliveryStatus] = mapped_column(
        SAEnum(DeliveryStatus, name="delivery_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=DeliveryStatus.PENDING,
        nullable=False,
        index=True,
    )
    estimated_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracking_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    weather_delay_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
