"""
ProfessionalProfile: one row per FIELD_AGENT/EXPERT/TRADER/DEALER user.
Reuses the existing User/Role system - this is NOT a second authentication
system, just role-specific profile data, the same pattern FarmerProfile
already established for the farmer role.

Deliberate consolidation (per "do not create unnecessary tables"):
languages, crop/disease specializations, and service area are stored as
JSONB fields here rather than as three separate child tables - the same
pattern already used by AIModelRegistry.supported_crop_ids. Revisit with
real child tables only if per-row metadata is ever needed.

Limitation disclosed: `service_area` holds exactly ONE area object per
professional this phase - see docs/PROFESSIONAL_NETWORK.md.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)

    language_codes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    crop_specialization_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    disease_specialization_categories: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    service_area: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="professional_verification_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        SAEnum(AvailabilityStatus, name="professional_availability_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=AvailabilityStatus.OFFLINE,
        nullable=False,
        index=True,
    )

    max_active_cases: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    completed_case_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_test_account: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    verification_records: Mapped[list["VerificationRecord"]] = relationship(back_populates="professional")
