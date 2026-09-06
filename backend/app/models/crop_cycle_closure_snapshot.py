"""
CropCycleClosureSnapshot: D97-02..09 (docs/audit/FINAL_CANONICAL_group_D.md)
- a point-in-time freeze of a crop cycle's outcome, taken exactly once at
close_my_crop_cycle(). Every other view of this data (harvest quantity,
financial summary, disease/weather history) is a LIVE aggregate that can
drift after closure if underlying rows are later edited/added - this
table exists so a closed season's own record never silently changes.

Consolidates what the source audit doc's D97-02/D97-03 rows separately
proposed as new CropCycle columns and D97-04..09 proposed as a shared
table into ONE table, since all eight rows are the exact same "freeze at
close time" concept - splitting them across two homes would be a
distinction without a difference.

One row per crop cycle (unique FK) - close_my_crop_cycle can only ever
run once per cycle (PLANNED/APPROACHING/READY -> HARVESTED is a one-way
transition), so no upsert/versioning concern exists.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CropCycleClosureSnapshot(Base):
    __tablename__ = "crop_cycle_closure_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # D97-02/D97-03: from the linked HarvestRecord, if one exists - None
    # (never fabricated) when no harvest was ever recorded against this cycle.
    harvest_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    harvest_quantity_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quality_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    harvest_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # D97-04/D97-05/D97-06/D97-07: from crop_financial_service.get_financial_summary()
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    actual_profit_loss: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # D97-08: derived from AIAnalysis rows for this crop cycle - counts and
    # distinct diagnoses only, never a fabricated narrative.
    disease_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # D97-09: derived from Notification rows tied to this crop cycle
    # (related_entity_type="crop_cycle") in a weather-related category.
    weather_impact_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
