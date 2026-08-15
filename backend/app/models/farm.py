"""
Farm: top of the Farm -> Plot -> CropCycle -> Crop hierarchy, owned by
exactly one farmer (via `farmer_id` -> users.id). A farmer may own
multiple farms - this is NOT assumed to be 1:1 anywhere in this schema.

Privacy: latitude/longitude are precise farmer location data. Per the
approved architecture's location-privacy rule, these are never exposed to
any role other than the owning farmer (and, later, an explicitly assigned
field agent) - enforced at the service/schema layer (see
app/schemas/farm.py and app/services/farm_service.py), not just by
convention. A coarse/approximate-location representation for future
limited-sharing use cases is deliberately NOT built here - only the
precise value is stored; approximation, if ever needed, is computed at
the point of sharing, not stored as a second field, to avoid two sources
of truth for one location.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.area_units import AreaUnit
from app.db.session import Base


class FarmStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Farm(Base):
    __tablename__ = "farms"
    __table_args__ = (
        CheckConstraint("area_value > 0", name="ck_farms_area_value_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    farm_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)

    area_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    area_unit: Mapped[AreaUnit] = mapped_column(
        SAEnum(AreaUnit, name="area_unit", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    # Canonical value, always derived from (area_value, area_unit) at write
    # time - never entered directly by the farmer, never the source of
    # truth for display (area_value/area_unit are), only for aggregation
    # and future cross-unit comparison.
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

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

    plots: Mapped[list["Plot"]] = relationship(back_populates="farm", cascade="all, delete-orphan")
