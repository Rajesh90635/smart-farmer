"""
CropPhotoSession: groups multiple photos taken during one "crop check"
(e.g. whole-plant, affected-leaf, close-up, stem photos for the same
inspection), per Requirement 9/10. AI aggregation across a session's
photos is NOT implemented yet - this phase only supports Crop -> Photo
Session -> Photos -> Upload.

farmer_id is denormalized here (in addition to being derivable via
crop_cycle_id -> plot -> farm -> farmer_id) specifically because this
prompt's photo module explicitly calls for farmer_id-indexed ownership
checks on photo-adjacent tables - unlike Plot/CropCycle, which deliberately
do NOT denormalize farmer_id. This is a scoped exception, not a pattern
change - see docs/CROP_PHOTO_MODULE.md.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CropPhotoSession(Base):
    __tablename__ = "crop_photo_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(150), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    photos: Mapped[list["CropPhoto"]] = relationship(back_populates="session", cascade="all, delete-orphan")
