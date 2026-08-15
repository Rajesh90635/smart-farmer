"""
NotificationPreference: one row per farmer (Requirement 28/29). Defaults
are all ON except explicitly documented otherwise in docs/NOTIFICATION_ARCHITECTURE.md
- no safety-relevant alert category is silently defaulted OFF.
"""
import uuid
from datetime import datetime, time, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    weather_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rain_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    crop_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    disease_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    audio_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # opt-IN, not opt-out - Requirement 8
    general_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
