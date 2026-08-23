"""
DealerProduct: a dealer's listing of an APPROVED product. Batch/expiry
fields live here (one active batch per listing at a time - a disclosed
MVP simplification, not full multi-batch inventory) rather than a
separate ProductBatch table.

Selling eligibility (dealer VERIFIED + product APPROVED) is enforced at
the SERVICE layer on every read/write that matters (listing creation,
price comparison, cart/checkout) - never assumed from this row's mere
existence.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DealerProduct(Base):
    __tablename__ = "dealer_products"
    __table_args__ = (UniqueConstraint("dealer_id", "product_id", name="uq_dealer_products_dealer_product"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_area: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    def is_expired(self, today: date) -> bool:
        return self.expiry_date is not None and self.expiry_date < today
