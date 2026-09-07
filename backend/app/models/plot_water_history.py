"""
PlotWaterHistory: an append-only log of a Plot's water_availability
changes - D17-06 (docs/audit/FINAL_CANONICAL_group_A.md).

Mirrors PlotSoilHistory/CropCycleStageHistory's own conventions exactly.
A row is created only as a side effect of an explicit farmer-driven
update (see plot_service.py) - never speculatively, never for an
unchanged value.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.plot import WaterAvailability


class PlotWaterHistory(Base):
    __tablename__ = "plot_water_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    water_availability: Mapped[WaterAvailability] = mapped_column(
        SAEnum(
            WaterAvailability,
            name="plot_water_history_water_availability",
            native_enum=True,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    plot: Mapped["Plot"] = relationship()
