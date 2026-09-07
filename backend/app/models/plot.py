"""
Plot: belongs to exactly one Farm. A farm may have multiple plots.

soil_type / irrigation_type remain plain free-text fields, unchanged, for
any plot that already has one - no lossy backfill migration was invented
here to guess at a new controlled vocabulary from arbitrary old free text.
D3-08/D3-09/D17-01 (docs/audit/FINAL_CANONICAL_group_A.md) added the
validated enum as NEW, separate, purely additive fields instead
(irrigation_source/soil_category, both nullable - None for every existing
plot, honestly "not yet classified" rather than a fabricated mapping).
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.area_units import AreaUnit
from app.models.farm import FarmStatus  # Plot reuses the same active/inactive vocabulary
from app.db.session import Base


class IrrigationSource(str, enum.Enum):
    RAIN_FED = "rain_fed"
    BOREWELL = "borewell"
    CANAL = "canal"
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    OTHER = "other"


class SoilCategory(str, enum.Enum):
    LOAMY = "loamy"
    CLAYEY = "clayey"
    SANDY = "sandy"
    BLACK_COTTON = "black_cotton"
    RED = "red"
    ALLUVIAL = "alluvial"
    OTHER = "other"


class WaterAvailability(str, enum.Enum):
    """D17-02 (docs/audit/FINAL_CANONICAL_group_A.md): farmer-declared,
    self-reported reliability of this plot's water access - never
    measured/inferred by this system (no flow-meter/sensor integration
    exists), same honesty convention as is_sorted/quality_grade."""
    ADEQUATE = "adequate"
    LIMITED = "limited"
    SCARCE = "scarce"


class Plot(Base):
    __tablename__ = "plots"
    __table_args__ = (
        CheckConstraint("area_value > 0", name="ck_plots_area_value_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )

    plot_name: Mapped[str] = mapped_column(String(200), nullable=False)

    area_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    area_unit: Mapped[AreaUnit] = mapped_column(
        SAEnum(AreaUnit, name="area_unit", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    # D3-07 (docs/audit/FINAL_CANONICAL_group_A.md): a farmer-drawn polygon
    # boundary as a plain ordered list of {"latitude", "longitude"} points -
    # deliberately NOT a PostGIS geometry column (PostGIS is not enabled in
    # this project - see D76-01's own note) and never used to (re)compute
    # area_value/area_sqm, which stay exactly what the farmer entered
    # separately. Display/reference only.
    boundary_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    soil_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    irrigation_source: Mapped[IrrigationSource | None] = mapped_column(
        SAEnum(IrrigationSource, name="irrigation_source", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    soil_category: Mapped[SoilCategory | None] = mapped_column(
        SAEnum(SoilCategory, name="soil_category", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )

    # D17-02 (docs/audit/FINAL_CANONICAL_group_A.md): additive and
    # independent of irrigation_source/irrigation_type (which describe the
    # TYPE of water source, not its reliability) - None means "not yet
    # reported," never a fabricated guess.
    water_availability: Mapped[WaterAvailability | None] = mapped_column(
        SAEnum(WaterAvailability, name="water_availability", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )

    status: Mapped[FarmStatus] = mapped_column(
        SAEnum(FarmStatus, name="farm_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=FarmStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    farm: Mapped["Farm"] = relationship(back_populates="plots")
    crop_cycles: Mapped[list["CropCycle"]] = relationship(back_populates="plot", cascade="all, delete-orphan")

    # D17-03 (docs/audit/FINAL_CANONICAL_group_A.md): a farmer-declared
    # shortage flag derived from water_availability - never a separate
    # fabricated detection mechanism. None (not-yet-reported) is honestly
    # distinct from False (reported adequate/limited).
    @property
    def water_shortage(self) -> bool | None:
        if self.water_availability is None:
            return None
        return self.water_availability == WaterAvailability.SCARCE
