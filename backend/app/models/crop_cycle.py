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


class FailureReason(str, enum.Enum):
    """D10-02/D10-03 (docs/audit/c02_lifecycle_edgecases.md): a reason
    taxonomy for a reported crop failure - stored as a plain string
    column (see `CropCycle.failure_reason`), not a native Postgres enum,
    consistent with this project's precedent of storing some enum-like
    values as plain strings to avoid touching a shared enum type."""
    DISEASE = "disease"
    PEST = "pest"
    DROUGHT = "drought"
    FLOOD = "flood"
    WEATHER_DAMAGE = "weather_damage"
    MARKET_CONDITIONS = "market_conditions"
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
    # Additive, Phase 1 (CropVariety). Nullable and independent of
    # seed_variety - the free-text field is NOT replaced, renamed, or
    # deprecated by this column. A crop cycle can have neither, either, or
    # both populated; nothing in this codebase requires variety_id.
    variety_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_varieties.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # D10-02/D10-03/D10-10/D11-01 (docs/audit/c02_lifecycle_edgecases.md):
    # only ever set by report_crop_failure() (crop_cycle_service.py) -
    # a plain cancel via update_my_crop_cycle leaves this None, so
    # "reported failure" stays distinguishable from "farmer changed
    # their mind." resown_from_crop_cycle_id links a NEW cycle back to
    # the one it replaced - set only at creation time, never retroactively.
    failure_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resown_from_crop_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="SET NULL"), nullable=True
    )

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
    variety: Mapped["CropVariety | None"] = relationship()
