"""
DiseaseClass: the disease reference/master entity, per Requirement 7.
Crop -> DiseaseClass -> DiseaseMetadata. Deliberately excludes
treatment/medicine fields (Requirement 7's explicit instruction) - that's
a separate future module referencing disease_id, not a column here.

IMPORTANT: the rows seeded here are illustrative only (see the migration),
matching the same honesty pattern as CropMaster's seed data. They exist so
the schema/API can be exercised end-to-end, NOT because any trained model
in this project actually recognizes them. `is_active` plus the future
`AIModelRegistry.supported_crop_ids` linkage is what will eventually
determine which diseases a real model can actually predict - see
docs/DISEASE_MODEL.md.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DiseaseClass(Base):
    __tablename__ = "disease_classes"
    __table_args__ = (UniqueConstraint("crop_id", "disease_name", name="uq_disease_classes_crop_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="CASCADE"), nullable=False, index=True
    )
    disease_name: Mapped[str] = mapped_column(String(150), nullable=False)
    local_names: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scientific_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Free text, not an enum - "low/medium/high" style severity taxonomies
    # vary by crop/disease and no authoritative scheme is defined yet;
    # same deliberate-simplicity reasoning as Plot.soil_type.
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    disease_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
