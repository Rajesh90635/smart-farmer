"""
BuyerBusinessProfile: extends the EXISTING ProfessionalProfile (Prompt 8)
for the buyer role - identical reuse pattern to DealerBusinessProfile
(Prompt 9). Buyer verification (PENDING/VERIFIED/REJECTED/SUSPENDED/
EXPIRED) is entirely ProfessionalProfile.verification_status, unchanged -
no second buyer-verification system.
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


class BuyerType(str, enum.Enum):
    BUSINESS_BUYER = "business_buyer"
    WHOLESALER = "wholesaler"
    PROCESSOR = "processor"
    RETAILER = "retailer"
    TRADER = "trader"
    INSTITUTIONAL_BUYER = "institutional_buyer"


class BuyerBusinessProfile(Base):
    __tablename__ = "buyer_business_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    buyer_type: Mapped[BuyerType] = mapped_column(
        SAEnum(BuyerType, name="buyer_type", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    crops_purchased: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    quality_requirements: Mapped[str | None] = mapped_column(String(200), nullable=True)
    min_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    purchase_frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collection_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
