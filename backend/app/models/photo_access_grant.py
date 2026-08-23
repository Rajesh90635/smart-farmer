"""
PhotoAccessGrant: the actual AUTHORIZATION record gating photo access for
a case - not just a log. The existing crop-photo-serving endpoint checks
for a valid, non-expired, non-revoked grant in addition to farmer
ownership, rather than a new parallel photo-serving endpoint being built.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PhotoAccessGrant(Base):
    __tablename__ = "photo_access_grants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_health_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_photo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_photos.id", ondelete="CASCADE"), nullable=False, index=True)
    professional_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def is_active(self, now: datetime) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and now > self.expires_at:
            return False
        return True
