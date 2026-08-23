"""
FarmerProfile: farmer-specific profile fields, one-to-one with User.

Privacy notes:
- full_name: required, shown only to the farmer themselves and (per the
  approved architecture's privacy rules) never exposed to dealers, buyers,
  other farmers, or field agents unless a future explicitly-approved
  workflow requires it (e.g. a field-agent visit assignment - not built
  yet, and even then would be a minimum-necessary disclosure, not a full
  profile share).
- preferred_language_code / preferred_voice_language_code: not sensitive,
  used to drive UI/voice localization once those features exist.
- No profile photo field yet — not required by the approved architecture
  and not requested in this phase; add only when a real feature needs it,
  per "do not collect unnecessary information."
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.localization import DEFAULT_LANGUAGE_CODE
from app.db.session import Base


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    preferred_language_code: Mapped[str] = mapped_column(String(10), nullable=False, default=DEFAULT_LANGUAGE_CODE)
    preferred_voice_language_code: Mapped[str] = mapped_column(
        String(10), nullable=False, default=DEFAULT_LANGUAGE_CODE
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="farmer_profile")
