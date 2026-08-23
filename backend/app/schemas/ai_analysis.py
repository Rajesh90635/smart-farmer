import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.ai_analysis import AnalysisStatus, ResultStatus


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
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}

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


class AIAnalysisSessionCreateRequest(BaseModel):
    crop_photo_session_id: uuid.UUID


class AIAnalysisSessionResponse(BaseModel):
    id: uuid.UUID
    crop_photo_session_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    created_at: datetime
    analyses: list[AIAnalysisResponse] = []

    model_config = {"from_attributes": True}
