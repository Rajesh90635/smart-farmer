"""
DealerBusinessProfile: extends the EXISTING ProfessionalProfile (Prompt 8)
for the dealer/trader role, rather than creating a duplicate
"DealerProfile" table. ProfessionalProfile already provides: display_name,
organization, service_area, language_codes, verification_status (PENDING/
VERIFIED/REJECTED/SUSPENDED/EXPIRED - exactly matching this phase's
required dealer statuses), and the admin-only verification workflow - all
reused as-is.

This table holds ONLY the fields genuinely specific to a commercial
dealer/trader: business type, license/registration info, business hours,
and delivery areas (distinct from the professional's advisory service_area).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DealerBusinessProfile(Base):
    __tablename__ = "dealer_business_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_areas: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
