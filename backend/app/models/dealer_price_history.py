"""
DealerPriceHistory: append-only record of every dealer price change.
Written by the service layer whenever DealerProduct.price is updated -
never edited or deleted afterward.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DealerPriceHistory(Base):
    __tablename__ = "dealer_price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dealer_products.id", ondelete="CASCADE"), nullable=False, index=True)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
