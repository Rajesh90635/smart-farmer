"""
SaleOrder: created when a farmer ACCEPTS a buyer offer/counter-offer. Its
price/quantity/quality fields are populated ONCE at creation and never
recalculated afterward - this IS the SalePriceSnapshot (no separate
table, same consolidation pattern as Prompt 9's OrderItem).

Deliberately NOT a SaleOrderItem child table - a harvest sale is
inherently single-crop/single-listing, so there is no multi-line-item
concept to represent here. Disclosed simplification.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SaleOrderStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY_FOR_COLLECTION = "ready_for_collection"
    COLLECTED = "collected"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
    COMPLETED = "completed"


ALLOWED_SALE_ORDER_TRANSITIONS: dict[SaleOrderStatus, set[SaleOrderStatus]] = {
    SaleOrderStatus.PENDING: {SaleOrderStatus.ACCEPTED, SaleOrderStatus.CANCELLED},
    SaleOrderStatus.ACCEPTED: {SaleOrderStatus.PREPARING, SaleOrderStatus.CANCELLED},
    SaleOrderStatus.PREPARING: {SaleOrderStatus.READY_FOR_COLLECTION, SaleOrderStatus.CANCELLED},
    SaleOrderStatus.READY_FOR_COLLECTION: {SaleOrderStatus.COLLECTED, SaleOrderStatus.CANCELLED},
    SaleOrderStatus.COLLECTED: {SaleOrderStatus.IN_TRANSIT},
    SaleOrderStatus.IN_TRANSIT: {SaleOrderStatus.DELIVERED},
    SaleOrderStatus.DELIVERED: {SaleOrderStatus.PAYMENT_PENDING, SaleOrderStatus.DISPUTED},
    SaleOrderStatus.PAYMENT_PENDING: {SaleOrderStatus.PAID, SaleOrderStatus.DISPUTED},
    SaleOrderStatus.PAID: {SaleOrderStatus.COMPLETED, SaleOrderStatus.DISPUTED},
    SaleOrderStatus.DISPUTED: {SaleOrderStatus.PAYMENT_PENDING, SaleOrderStatus.COMPLETED, SaleOrderStatus.CANCELLED},
    SaleOrderStatus.CANCELLED: set(),
    SaleOrderStatus.COMPLETED: set(),
}

CANCELLATION_REASONS = ("price_dispute", "quantity_change", "buyer_cancelled", "farmer_cancelled", "logistics_failure", "weather", "other")


class SaleOrder(Base):
    __tablename__ = "sale_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    harvest_listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("harvest_listings.id", ondelete="RESTRICT"), nullable=False, index=True)
    buyer_offer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buyer_offers.id", ondelete="RESTRICT"), nullable=False)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="RESTRICT"), nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    quality_grade_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    charges: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    collection_method: Mapped[str] = mapped_column(String(50), nullable=False)
    service_area_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    exact_collection_location: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[SaleOrderStatus] = mapped_column(
        SAEnum(SaleOrderStatus, name="sale_order_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=SaleOrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
