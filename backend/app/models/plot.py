"""
Plot: belongs to exactly one Farm. A farm may have multiple plots.

soil_type / irrigation_type are deliberately plain free-text fields, not a
controlled vocabulary/enum - the approved architecture doesn't define an
authoritative taxonomy for either yet, and inventing one here would be
guessing at a decision that belongs to whoever designs the future soil
report OCR / irrigation advisor modules. Flagged as an assumption, not a
silent design choice.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.area_units import AreaUnit
from app.models.farm import FarmStatus  # Plot reuses the same active/inactive vocabulary
from app.db.session import Base


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

    soil_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

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
