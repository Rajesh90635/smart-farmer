"""
AICropStageResult: AI observation only (Requirement 18/19). Structurally
separate from CropCycle.cultivation_status (the farmer-official field,
untouched since Prompt 4) - no code path in this phase writes to
cultivation_status from here or anywhere in the AI module. Promoting an
AI-suggested stage into the official record requires an explicit farmer
or expert confirmation action, which is a future module, not built here.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.ai_analysis import AnalysisStatus


class AICropStageResult(Base):
    __tablename__ = "ai_crop_stage_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crop_photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_photos.id", ondelete="SET NULL"), nullable=True
    )

    predicted_stage_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus, name="ai_analysis_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
