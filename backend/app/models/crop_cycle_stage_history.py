"""
CropCycleStageHistory: an append-only log of a CropCycle's actual
cultivation_status transitions - "flowering started on X" as a fact,
never overwritten.

Phase 2 infrastructure only. This table exists purely to record WHEN a
transition actually happened; it does not calculate, predict, or suggest
anything, and it does not attach any agronomic meaning to a status
(no "you should have flowered by now" logic lives here). A row is
created only as a side effect of an explicit farmer-driven status
change (see crop_cycle_service.py) - never speculatively, never because
a plan exists, and never for an unchanged status.

Deliberately one-to-many with CropCycle (no unique constraint on
crop_cycle_id) - a cycle passes through several statuses over its
lifetime, and every one of them is worth keeping, same reasoning as
Phase 0's HarvestRecord fix.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.crop_cycle import CultivationStatus


class CropCycleStageHistory(Base):
    __tablename__ = "crop_cycle_stage_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[CultivationStatus] = mapped_column(
        SAEnum(
            CultivationStatus,
            name="crop_cycle_stage_history_status",
            native_enum=True,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    crop_cycle: Mapped["CropCycle"] = relationship()
