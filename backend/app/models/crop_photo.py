"""
CropPhoto: one uploaded photo, always belonging to Farmer -> Farm -> Plot
-> CropCycle -> CropPhotoSession -> CropPhoto. Never stored against a
farmer without crop context, per Requirement 2.

Storage decision (documented, not left implicit): only ONE image file is
persisted per photo (the processed version - EXIF-stripped, orientation-
normalized, compressed if oversized) plus one thumbnail. The original
upload bytes are held in memory only long enough to validate/process and
are never separately persisted - this avoids "storing duplicate files
unnecessarily" (Requirement 14) while still preserving enough quality for
future AI analysis (the processed version is capped at
photo_max_dimension_px, not aggressively downscaled).

Privacy decision (documented): EXIF metadata - including GPS - is always
stripped from the stored image (Requirement 15). If the farmer explicitly
consents to sharing location for this photo, the coordinates are stored
in the `latitude`/`longitude` DB columns (private, not embedded in image
bytes, not returned by the normal photo-serving endpoint) - never silently
read from EXIF.

Two status fields are kept deliberately separate:
- `upload_status`: the upload/processing pipeline's own lifecycle.
- `image_quality_status`: the non-AI technical quality heuristic verdict
  (ACCEPT/REJECT), independent of whether the upload itself succeeded.
A `processing_status` field was considered and deliberately NOT added -
in this phase all processing is synchronous, so a third status field would
just duplicate `upload_status`. Revisit if/when processing moves to a
background queue.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PhotoSource(str, enum.Enum):
    CAMERA = "camera"
    GALLERY = "gallery"


class UploadStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    FAILED = "failed"
    READY = "ready"
    DELETED = "deleted"


class ImageQualityStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CropPhoto(Base):
    __tablename__ = "crop_photos"
    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="ck_crop_photos_file_size_positive"),
        CheckConstraint("width_px > 0 AND height_px > 0", name="ck_crop_photos_dimensions_positive"),
        UniqueConstraint("session_id", "client_upload_id", name="uq_crop_photos_session_client_upload_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_photo_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Denormalized ownership/hierarchy chain - set server-side only, from
    # the validated session -> crop_cycle -> plot -> farm chain, never from
    # client input. Exists so ownership checks and listing don't require a
    # 4-table join on every request. See module docstring for why this
    # table (uniquely) denormalizes farmer_id.
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Idempotency key: the Flutter client generates a UUID once per capture
    # and resends the SAME value on retry - the unique constraint below is
    # what makes a retried upload update/return the existing row instead of
    # creating a duplicate (Requirement 22).
    client_upload_id: Mapped[str] = mapped_column(String(100), nullable=False)

    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)

    capture_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    upload_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Only populated with explicit per-photo farmer consent - never read
    # silently from EXIF (which is stripped before storage regardless).
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)

    source: Mapped[PhotoSource] = mapped_column(
        SAEnum(PhotoSource, name="photo_source", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    upload_status: Mapped[UploadStatus] = mapped_column(
        SAEnum(UploadStatus, name="photo_upload_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=UploadStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    image_quality_status: Mapped[ImageQualityStatus] = mapped_column(
        SAEnum(ImageQualityStatus, name="photo_quality_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=ImageQualityStatus.PENDING,
        nullable=False,
    )
    quality_reasons: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # e.g. "too_dark,too_blurry" - farmer-facing message is composed from this, not stored pre-rendered

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    session: Mapped["CropPhotoSession"] = relationship(back_populates="photos")
