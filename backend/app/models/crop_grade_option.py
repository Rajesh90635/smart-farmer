"""
CropGradeOption: D52-02 (docs/audit/FINAL_CANONICAL_group_C.md) - a
per-crop, admin-authored set of allowed grade values, replacing
unconstrained free text on HarvestListing.quality_grade once configured.

Deliberately empty by default, same honesty pattern as ReferencePrice/
DemandSignal/KnowledgeEntry elsewhere in this project: no real,
authoritative per-crop grading criteria (AGMARK-style or otherwise) is
invented here. Until an admin populates real, sourced grade options for a
crop, quality_grade stays free text for that crop (see
crop_grade_option_service.validate_quality_grade) - never silently
blocking a farmer's listing over a schema nobody has actually configured.

Deliberately dimension-agnostic rather than adding a separate size_grade
column (D51-03): an admin can configure size-based grade codes
("Large"/"Medium"/"Small") exactly as easily as quality-based ones
("Grade A"/"Grade B") through this same table - the crop-specific
taxonomy decision belongs to whoever sources the real data, not to this
schema.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CropGradeOption(Base):
    __tablename__ = "crop_grade_options"
    __table_args__ = (UniqueConstraint("crop_id", "grade_code", name="uq_crop_grade_options_crop_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="CASCADE"), nullable=False, index=True)

    grade_code: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
