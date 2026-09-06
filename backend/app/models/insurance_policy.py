"""
InsurancePolicy: D74-01 (docs/audit/FINAL_CANONICAL_group_D.md). Entirely
farmer-entered/self-reported - no insurer integration exists, so nothing
here is ever verified against a real insurer's records. crop_id is
optional (a policy may cover a crop not yet linked to any CropCycle, or a
general/multi-crop policy) and points at the shared CropMaster reference
data, not a specific CropCycle.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="SET NULL"), nullable=True)

    policy_number: Mapped[str] = mapped_column(String(100), nullable=False)
    insurer: Mapped[str] = mapped_column(String(200), nullable=False)
    sum_insured: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    season: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
