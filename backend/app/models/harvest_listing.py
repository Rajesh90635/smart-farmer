"""
HarvestListing: "Sell My Harvest" - what buyers actually see and offer
against. service_area is APPROXIMATE only (village/taluk/district) - the
farmer's exact farm coordinates are never copied here.
quantity_available is decremented as offers are ACCEPTED (never as merely
made) - see docs/SALE_WORKFLOW.md for the concurrency-safe acceptance
logic that updates this field.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CollectionOption(str, enum.Enum):
    BUYER_COLLECTION = "buyer_collection"
    FARMER_DELIVERY = "farmer_delivery"
    THIRD_PARTY_LOGISTICS = "third_party_logistics"


class HarvestListing(Base):
    __tablename__ = "harvest_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    harvest_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("harvest_records.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="RESTRICT"), nullable=False, index=True)

    quantity_available: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    quality_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expected_availability_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    service_area: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    delivery_option: Mapped[CollectionOption] = mapped_column(
        SAEnum(CollectionOption, name="collection_option", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
