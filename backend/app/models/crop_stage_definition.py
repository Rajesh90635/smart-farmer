"""
CropStageDefinition: crop-aware growth-stage reference (Requirement 17).
Deliberately NOT a fixed global enum - different crops can have different
meaningful stage sets, so stages are rows scoped to a crop_id rather than
a Python enum shared by every crop. The seed data (see migration) uses the
same generic stage set for every seeded crop only because no crop-specific
stage research was available this phase - the schema fully supports
per-crop divergence starting with the very next crop added.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CropStageDefinition(Base):
    __tablename__ = "crop_stage_definitions"
    __table_args__ = (UniqueConstraint("crop_id", "stage_code", name="uq_crop_stage_definitions_crop_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage_code: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Phase 2 infrastructure only - deliberately nullable and unpopulated
    # by default. No crop timing dataset exists in this repository (see
    # app/models/task.py's docstring on the same point), so seeding these
    # with a guessed number would be exactly the kind of unauthoritative
    # invention this project consistently avoids. sequence_order above is
    # unaffected and keeps its existing ordinal-only meaning - these two
    # columns add optional day-offset timing ON TOP of it, they don't
    # replace it.
    typical_days_from_sowing_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    typical_days_from_sowing_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
