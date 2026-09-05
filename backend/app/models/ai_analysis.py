"""
AIAnalysis: one AI analysis run against one CropPhoto (Requirement 8).

Deliberate simplification (per "do not blindly copy every field"): the
prompt's suggested `prediction_type` field was dropped as redundant with
`result_status` below - both would have tracked overlapping information
(what kind of result this is), and a single well-defined status field is
clearer than two partially-overlapping ones.

Two status fields ARE kept, and are NOT redundant:
- `analysis_status`: the job/pipeline lifecycle (PENDING/PROCESSING/
  COMPLETED/FAILED) - "did the analysis attempt run to completion."
- `result_status`: the safety-layer verdict (HEALTHY/DISEASE_DETECTED/
  UNKNOWN/LOW_CONFIDENCE/CROP_MISMATCH/AI_UNAVAILABLE) - "what does the
  completed (or failed) analysis actually say, if anything."
A COMPLETED analysis can still have result_status=LOW_CONFIDENCE or
UNKNOWN - completing successfully and having a confident answer are two
different things, which is the entire point of Requirement 10/13.

`model_name`/`model_version` are stored as immutable strings IN ADDITION
to the `model_registry_id` FK, so a historical result still identifies its
model even if the registry row is later edited or deactivated
(Requirement 33's "old results must still identify the original model").

`requires_review` is the expert-verification hook (Requirement 27) - not a
workflow, just a flag a future expert-review module will query.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DISEASE_DETECTED = "disease_detected"
    UNKNOWN = "unknown"
    LOW_CONFIDENCE = "low_confidence"
    CROP_MISMATCH = "crop_mismatch"
    PROCESSING = "processing"
    FAILED = "failed"
    AI_UNAVAILABLE = "ai_unavailable"  # Requirement 36 - MODEL_NOT_AVAILABLE, never a fake result


class FarmerCorrection(str, enum.Enum):
    """D91-07/D91-09/D91-10 (docs/audit/c13_governance_farmbrain_security.md):
    a farmer's own after-the-fact correction of THIS specific AIAnalysis
    result - distinct from AdvisoryFeedback/AssistantFeedback, which the
    audit confirmed are scoped away from the disease-detection pipeline
    entirely. Also the raw signal false-positive/false-negative tracking
    needs - CONFIRMED_CORRECT/ACTUALLY_HEALTHY/ACTUALLY_DISEASED/
    WRONG_DISEASE_NAME let a false positive (ACTUALLY_HEALTHY on a
    DISEASE_DETECTED result) or false negative (ACTUALLY_DISEASED on a
    HEALTHY result) be derived without guessing."""
    CONFIRMED_CORRECT = "confirmed_correct"
    ACTUALLY_HEALTHY = "actually_healthy"
    ACTUALLY_DISEASED = "actually_diseased"
    WRONG_DISEASE_NAME = "wrong_disease_name"


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    crop_photo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_photos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_analysis_sessions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Denormalized for single-table ownership checks, same pattern as
    # CropPhoto - set server-side only, from the validated photo's own
    # farmer_id, never from client input.
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crop_master.id", ondelete="SET NULL"), nullable=True
    )
    model_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_model_registry.id", ondelete="RESTRICT"), nullable=False
    )

    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    predicted_class: Mapped[str | None] = mapped_column(String(150), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_k_predictions: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{"class_name":..,"confidence":..}]

    result_status: Mapped[ResultStatus] = mapped_column(
        SAEnum(ResultStatus, name="ai_result_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus, name="ai_analysis_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True,
    )
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # D91-07/D91-09/D91-10: a plain string (a FarmerCorrection value), not
    # a shared native enum - avoids touching the ai_result_status/
    # ai_analysis_status enum types, consistent with this project's
    # precedent elsewhere (e.g. InputInventoryItem.category).
    farmer_correction: Mapped[str | None] = mapped_column(String(30), nullable=True)
    farmer_correction_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    farmer_corrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    inference_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preprocessing_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    analysis_session: Mapped["AIAnalysisSession"] = relationship(back_populates="analyses")
