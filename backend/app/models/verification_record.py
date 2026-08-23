"""
VerificationRecord: append-only history of admin verification actions
(Requirement 40/62). ProfessionalProfile.verification_status is the
CURRENT state; this table is why/when/who changed it - a professional
can never self-verify (enforced at the service layer: only an ADMIN-role
caller can invoke the verification endpoints at all).
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class VerificationAction(str, enum.Enum):
    VERIFY = "verify"
    REJECT = "reject"
    SUSPEND = "suspend"
    REACTIVATE = "reactivate"


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[VerificationAction] = mapped_column(
        SAEnum(VerificationAction, name="verification_action", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    performed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    professional: Mapped["ProfessionalProfile"] = relationship(back_populates="verification_records")
