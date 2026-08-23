"""
PriceAnomalyFlag: persisted only for NON-normal flags (HIGH/UNUSUAL/
REVIEW_REQUIRED) - normal prices are never stored here, keeping this
table an actual review queue rather than a log of everything. Language is
always neutral/observational - this table has no field for an accusation,
only a comparison fact.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PriceAnomalyLevel(str, enum.Enum):
    HIGH = "high"
    UNUSUAL = "unusual"
    REVIEW_REQUIRED = "review_required"


class PriceAnomalyFlag(Base):
    __tablename__ = "price_anomaly_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dealer_products.id", ondelete="CASCADE"), nullable=False, index=True)

    level: Mapped[PriceAnomalyLevel] = mapped_column(
        SAEnum(PriceAnomalyLevel, name="price_anomaly_level", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    dealer_price_at_detection: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reference_price_at_detection: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
