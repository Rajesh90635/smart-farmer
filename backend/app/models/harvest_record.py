"""
HarvestRecord: one row per harvest EVENT for a crop cycle, not one row per
crop cycle. A crop cycle supports multiple HarvestRecords (Phase 0 fix -
see migration "remove unique constraint on harvest_records
crop_cycle_id") because many real crops (tomato, chilli, okra, brinjal,
beans, cucumber) are picked repeatedly over the season, not harvested
once. AI (Prompt 6 crop-stage intelligence) may SUGGEST that a crop is
approaching harvest, but no code path in this phase automatically sets
status past PLANNED/APPROACHING without an explicit farmer action -
enforced by the service layer, not just documented intent.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class HarvestStatus(str, enum.Enum):
    PLANNED = "planned"
    APPROACHING = "approaching"
    READY = "ready"
    HARVESTED = "harvested"
    LISTED = "listed"
    PARTIALLY_SOLD = "partially_sold"
    SOLD = "sold"
    CANCELLED = "cancelled"


class HarvestRecord(Base):
    __tablename__ = "harvest_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    plot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="RESTRICT"), nullable=False)

    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    quality_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)

    status: Mapped[HarvestStatus] = mapped_column(
        SAEnum(HarvestStatus, name="harvest_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=HarvestStatus.PLANNED,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
