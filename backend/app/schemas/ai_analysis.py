import uuid
from datetime import datetime

from pydantic import BaseModel, computed_field, field_validator

from app.models.ai_analysis import AnalysisStatus, FarmerCorrection, ResultStatus


class TopKPredictionResponse(BaseModel):
    class_name: str
    confidence: float


class AIAnalysisResponse(BaseModel):
    id: uuid.UUID
    crop_photo_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    analysis_session_id: uuid.UUID | None
    model_name: str
    model_version: str
    predicted_class: str | None
    confidence: float | None
    top_k_predictions: list[TopKPredictionResponse]
    result_status: ResultStatus
    analysis_status: AnalysisStatus
    requires_review: bool
    processing_time_ms: int | None
    farmer_correction: str | None
    farmer_correction_notes: str | None
    farmer_corrected_at: datetime | None
    created_at: datetime
    # D88-10 (docs/audit/FINAL_CANONICAL_group_D.md): mirrors weather's own
    # is_stale flag - set by the service layer (needs Settings, which a
    # bare model_validate() call has no access to), defaults to False so
    # every existing construction site stays correct until explicitly set.
    is_stale: bool = False

    model_config = {"from_attributes": True, "protected_namespaces": ()}

    @computed_field
    @property
    def original_call_judged_correct(self) -> bool | None:
        """D91-08 (docs/audit/FINAL_CANONICAL_group_D.md): a distinct
        "was the AI's original call right" signal, separate from
        treatment effectiveness - derived directly from farmer_correction
        rather than a second stored field, since the two can never
        disagree by construction. None until a correction is submitted."""
        if self.farmer_correction is None:
            return None
        return self.farmer_correction == FarmerCorrection.CONFIRMED_CORRECT.value

    @field_validator("top_k_predictions", mode="before")
    @classmethod
    def default_empty_predictions(cls, v):
        # NULL on the FAILED/AI_UNAVAILABLE paths (no prediction was ever
        # produced to record) - coerced to [] rather than requiring every
        # caller to remember to set it explicitly. Found via a real test
        # failure on the AI-failure path, not by inspection.
        return v if v is not None else []


class AIAnalysisListResponse(BaseModel):
    items: list[AIAnalysisResponse]
    total: int


class AIAnalysisCorrectionRequest(BaseModel):
    correction: FarmerCorrection
    notes: str | None = None


class AIEvaluationAggregateResponse(BaseModel):
    """D91-09/D91-10 (docs/audit/FINAL_CANONICAL_group_D.md): real rates
    computed from farmer_correction rows, never a synthetic/fabricated
    metric - a rate is None whenever its denominator is genuinely zero
    (no analyses of that result type exist yet), never a fake 0%."""
    total_disease_detected: int
    total_healthy: int
    false_positive_count: int
    false_positive_rate: float | None
    false_negative_count: int
    false_negative_rate: float | None
    confirmed_correct_count: int
    wrong_disease_name_count: int


class AIAnalysisSessionCreateRequest(BaseModel):
    crop_photo_session_id: uuid.UUID


class AIAnalysisSessionResponse(BaseModel):
    id: uuid.UUID
    crop_photo_session_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    created_at: datetime
    analyses: list[AIAnalysisResponse] = []

    model_config = {"from_attributes": True}
