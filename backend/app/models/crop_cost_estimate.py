"""
CropCostEstimate: Phase 31's genuinely missing "Estimated" data source.

No CropPlanCostEntry/agricultural cost-estimation dataset exists anywhere
in this repository (confirmed by exhaustive search before writing this
file). Rather than fabricate typical cultivation costs (explicitly
forbidden), this follows the EXACT same principle already established
for LedgerEntry's manual entries and Task's farmer-created tasks: the
FARMER types in their own estimate. This is not a "smart" cost predictor
and does not claim to be one - it is a simple, honest place for a farmer
to record what THEY expect to spend, so it can later be compared against
what they actually spent.

Optionally tagged to a CropStageDefinition for stage-wise comparison -
untagged estimates represent a general/total estimate not broken down
by stage.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CropCostEstimate(Base):
    __tablename__ = "crop_cost_estimates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_stage_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_stage_definitions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Plain string, not a native enum - reuses the SAME category
    # vocabulary as LedgerCategory (validated at the Pydantic schema
    # layer, see app/schemas/cost_estimate.py) so a farmer estimating
    # "fertilizer: Rs 1200" uses the same word as when they later record
    # the actual fertilizer expense, keeping the two directly comparable.
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
