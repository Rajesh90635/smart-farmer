"""
IrrigationRecord: D18-06 (docs/audit/FINAL_CANONICAL_group_A.md) - mirrors
TreatmentRecord's exact shape/reasoning for the irrigation domain, which
had no analogous activity/event log before this (only a generic completed
Task with no volume/duration data).

source reuses Plot.IrrigationSource - the same validated vocabulary
D17-01 introduced, never a second, duplicate enum.

D18-08 (Pump failure): rather than a full equipment-inventory system,
failure_note is a simple optional free-text field here, per this
project's own incremental-scope convention (the audit's own suggested
resolution) - "the farmer attempted to irrigate but the pump failed" is
recorded as a fact on the irrigation attempt itself, not a separate
equipment-status model.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.plot import IrrigationSource


class IrrigationRecord(Base):
    __tablename__ = "irrigation_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    # Optional link to the task that prompted this irrigation (if any) -
    # a farmer can equally log irrigation with no task behind it at all.
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    irrigation_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    volume_liters: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    source: Mapped[IrrigationSource | None] = mapped_column(
        SAEnum(IrrigationSource, name="irrigation_source", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # D18-08: farmer-entered, optional - never inferred/auto-detected.
    failure_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
