"""
ConsentRecord: one row per (user, consent_type) acceptance/revocation
event. Per the "do not assume consent for optional features" rule,
TERMS_OF_SERVICE and PRIVACY_POLICY are required at registration;
CROP_IMAGE_PROCESSING and LOCATION_USAGE are optional and must be recorded
explicitly whenever the farmer actually grants them (not assumed, and not
collected at registration in this phase — no feature that needs them
exists yet).
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ConsentType(str, enum.Enum):
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    CROP_IMAGE_PROCESSING = "crop_image_processing"
    LOCATION_USAGE = "location_usage"


class ConsentStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    REVOKED = "revoked"


REQUIRED_CONSENTS_AT_REGISTRATION: tuple[ConsentType, ...] = (
    ConsentType.TERMS_OF_SERVICE,
    ConsentType.PRIVACY_POLICY,
)


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = (Index("ix_consent_user_type", "user_id", "consent_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    consent_type: Mapped[ConsentType] = mapped_column(
        SAEnum(ConsentType, name="consent_type", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(
        SAEnum(ConsentStatus, name="consent_status", native_enum=True, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="consents")
