"""
CropDamageRecord: D74-02 (docs/audit/FINAL_CANONICAL_group_D.md) -
entirely farmer-entered/self-reported, like InsurancePolicy - no insurer
or disaster-authority verification exists, so nothing here is ever
cross-checked against a real assessment. Always tied to both a specific
crop cycle AND a specific insurance policy - this is explicitly an
insurance-purpose damage record, not a general crop-health log (that's
what AI disease analysis / crop_health_case already cover).
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DamageLossType(str, enum.Enum):
    DROUGHT = "drought"
    FLOOD = "flood"
    PEST = "pest"
    DISEASE = "disease"
    HAIL = "hail"
    FIRE = "fire"
    OTHER = "other"


class CropDamageRecord(Base):
    __tablename__ = "crop_damage_records"
    __table_args__ = (CheckConstraint("extent_percent >= 0 AND extent_percent <= 100", name="ck_crop_damage_records_extent_percent_range"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("insurance_policies.id", ondelete="CASCADE"), nullable=False, index=True)

    loss_type: Mapped[DamageLossType] = mapped_column(
        SAEnum(DamageLossType, name="damage_loss_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    extent_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
