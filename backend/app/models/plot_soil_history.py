"""
PlotSoilHistory: an append-only log of a Plot's soil_type/soil_category
changes - D19-04 (docs/audit/FINAL_CANONICAL_group_A.md).

Plot.soil_type/soil_category themselves remain single current-value
fields, silently overwritten on update (unchanged) - this table exists
purely to record WHEN a change happened, mirroring
CropCycleStageHistory/CropCycleSeasonHistory's own "record the fact,
attach no agronomic meaning" convention. A row is created only as a
side effect of an explicit farmer-driven update (see plot_service.py) -
never speculatively, and never for an unchanged value.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.plot import SoilCategory


class PlotSoilHistory(Base):
    __tablename__ = "plot_soil_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    soil_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    soil_category: Mapped[SoilCategory | None] = mapped_column(
        SAEnum(
            SoilCategory,
            name="plot_soil_history_soil_category",
            native_enum=True,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    plot: Mapped["Plot"] = relationship()
