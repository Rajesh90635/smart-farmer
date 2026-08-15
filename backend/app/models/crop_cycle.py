"""
CropCycle: one cultivation instance on a Plot, over a defined period,
pointing at a CropMaster row - NOT a crop attached directly to a Plot,
per the explicit "do not simply attach a crop directly to a plot" rule.
A plot can have many crop cycles over time (Plot A -> Tomato -> harvested
-> Onion), all retained for history.

`cultivation_status` is the single farmer-official status field. The
ai_suggested_* fields exist purely as a future-integration hook (per the
Future AI Integration requirement) and are NOT written or read by any
logic in this phase - a future AI module would populate them, and only an
explicit farmer/expert confirmation action (not built yet) would ever
promote an AI suggestion into `cultivation_status`. Enforced right now
simply by the fact that no code path writes these fields at all.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CultivationStatus(str, enum.Enum):
    PLANNED = "planned"
    SOWN = "sown"
    GROWING = "growing"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    READY_FOR_HARVEST = "ready_for_harvest"
    HARVESTED = "harvested"
    CANCELLED = "cancelled"


class Season(str, enum.Enum):
    KHARIF = "kharif"
    RABI = "rabi"
    ZAID = "zaid"
    PERENNIAL = "perennial"
    OTHER = "other"


# Forward-only linear path. CANCELLED is reachable from any non-terminal
# status (a farmer can abandon a cycle at any active stage). HARVESTED and
# CANCELLED are terminal - nothing transitions out of them. No backward
# transitions are permitted. See app/services/crop_cycle_service.py for
# the enforcement code and docs/CROP_MODULE.md for the diagram.
ALLOWED_TRANSITIONS: dict[CultivationStatus, set[CultivationStatus]] = {
    CultivationStatus.PLANNED: {CultivationStatus.SOWN, CultivationStatus.CANCELLED},
    CultivationStatus.SOWN: {CultivationStatus.GROWING, CultivationStatus.CANCELLED},
    CultivationStatus.GROWING: {CultivationStatus.FLOWERING, CultivationStatus.CANCELLED},
    CultivationStatus.FLOWERING: {CultivationStatus.FRUITING, CultivationStatus.CANCELLED},
    CultivationStatus.FRUITING: {CultivationStatus.READY_FOR_HARVEST, CultivationStatus.CANCELLED},
    CultivationStatus.READY_FOR_HARVEST: {CultivationStatus.HARVESTED, CultivationStatus.CANCELLED},
    CultivationStatus.HARVESTED: set(),
    CultivationStatus.CANCELLED: set(),
}


class CropCycle(Base):
    __tablename__ = "crop_cycles"
    __table_args__ = (
        CheckConstraint(
            "expected_harvest_date IS NULL OR expected_harvest_date >= sowing_date",
            name="ck_crop_cycles_expected_harvest_after_sowing",
        ),
        CheckConstraint(
            "actual_harvest_date IS NULL OR actual_harvest_date >= sowing_date",
            name="ck_crop_cycles_actual_harvest_after_sowing",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    season: Mapped[Season | None] = mapped_column(
        SAEnum(Season, name="crop_season", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    sowing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    actual_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    cultivation_status: Mapped[CultivationStatus] = mapped_column(
        SAEnum(CultivationStatus, name="cultivation_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=CultivationStatus.PLANNED,
        nullable=False,
        index=True,
    )

    seed_variety: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # --- Future AI integration hooks (Requirement 28). Not written or read
    # by any code in this phase. ---
    ai_suggested_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_observation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    plot: Mapped["Plot"] = relationship(back_populates="crop_cycles")
    crop: Mapped["CropMaster"] = relationship(back_populates="crop_cycles")
