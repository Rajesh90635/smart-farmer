"""
CropCycleSeasonHistory: an append-only log of a CropCycle's `season`
changes - D13-02 (docs/audit/FINAL_CANONICAL_group_A.md).

A perennial crop's single cultivation cycle can span multiple seasons
over its life (e.g. a long-running crop tracked through kharif, then
rabi). `CropCycle.season` itself remains a single current-value field
(unchanged, nothing else depends on it becoming a list) - this table
exists purely to record WHEN it changed, mirroring
CropCycleStageHistory's own "record the fact, attach no agronomic
meaning" convention exactly. A row is created only as a side effect of
an explicit farmer-driven season change (see crop_cycle_service.py) -
never speculatively, and never for an unchanged value.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.crop_cycle import Season


class CropCycleSeasonHistory(Base):
    __tablename__ = "crop_cycle_season_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    season: Mapped[Season] = mapped_column(
        SAEnum(
            Season,
            name="crop_cycle_season_history_season",
            native_enum=True,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    crop_cycle: Mapped["CropCycle"] = relationship()
