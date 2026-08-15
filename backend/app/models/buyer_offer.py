"""
BuyerOffer: a buyer's opening offer against a HarvestListing.
CounterOffer: append-only negotiation history - every counter is a NEW
row referencing the same BuyerOffer thread - the current/latest row (by
created_at) is the "live" price under discussion; nothing is ever edited
or deleted.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class OfferStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class NegotiationParty(str, enum.Enum):
    BUYER = "buyer"
    FARMER = "farmer"


class BuyerOffer(Base):
    __tablename__ = "buyer_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    harvest_listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("harvest_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quality_requirements: Mapped[str | None] = mapped_column(String(200), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collection_terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[OfferStatus] = mapped_column(
        SAEnum(OfferStatus, name="offer_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=OfferStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    counter_offers: Mapped[list["CounterOffer"]] = relationship(back_populates="buyer_offer", order_by="CounterOffer.created_at")


class CounterOffer(Base):
    __tablename__ = "counter_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_offer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("buyer_offers.id", ondelete="CASCADE"), nullable=False, index=True)

    proposed_by: Mapped[NegotiationParty] = mapped_column(
        SAEnum(NegotiationParty, name="negotiation_party", native_enum=True, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    buyer_offer: Mapped["BuyerOffer"] = relationship(back_populates="counter_offers")
