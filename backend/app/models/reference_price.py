"""
ReferencePrice: never an unexplained number. Every row has a source_type,
and rows are never updated in place - a new reference price is a new row,
giving natural price history via effective_date/retrieved_at ordering, no
separate PriceHistory table needed for this entity.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ReferencePriceSourceType(str, enum.Enum):
    OFFICIAL_SOURCE = "official_source"
    AUTHORIZED_MARKET_SOURCE = "authorized_market_source"
    MANUFACTURER_REFERENCE = "manufacturer_reference"
    VERIFIED_MARKET_DATA = "verified_market_data"
    ADMIN_ENTERED_REFERENCE = "admin_entered_reference"


class ReferencePrice(Base):
    __tablename__ = "reference_prices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    source_type: Mapped[ReferencePriceSourceType] = mapped_column(
        SAEnum(ReferencePriceSourceType, name="reference_price_source_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    region: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
