"""
CropVariety: a structured, crop-scoped reference entity (e.g. "Pusa Ruby"
for Tomato) - the FK-able alternative to CropCycle.seed_variety's plain
free-text field.

Deliberately minimal for Phase 1: name + optional typical duration only.
No yield/nutrient/spacing data here - inventing those without an
authoritative agronomic source would be exactly the kind of unauthoritative
guess this project consistently avoids (same reasoning already applied to
Plot.soil_type and Product.usage_information). Those fields can be added
later, additively, once a real data source exists.

CropCycle.seed_variety is NOT replaced or renamed by this model. It
continues to work exactly as before - this is a genuinely additive,
backward-compatible change (see CropCycle.variety_id, nullable).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CropVariety(Base):
    __tablename__ = "crop_varieties"
    __table_args__ = (
        # Same variety name can exist for different crops (e.g. a variety
        # literally named "Local" for both Tomato and Chilli), but not
        # duplicated twice for the SAME crop.
        UniqueConstraint("crop_id", "name", name="uq_crop_varieties_crop_id_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Nullable and deliberately vague ("typical") rather than a guaranteed
    # figure - real crop-stage duration varies by region/season/practice,
    # and this project does not invent an authoritative number where none
    # exists. Populated only when a real source provides it.
    typical_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    crop: Mapped["CropMaster"] = relationship()
