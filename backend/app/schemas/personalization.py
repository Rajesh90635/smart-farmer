import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.advisory_feedback import AdvisoryFeedbackType, AdvisorySourceType


class AdvisoryFeedbackCreateRequest(BaseModel):
    source_type: AdvisorySourceType
    source_reference: str | None = Field(default=None, max_length=100)
    feedback_type: AdvisoryFeedbackType
    note: str | None = Field(default=None, max_length=1000)


class AdvisoryFeedbackResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    source_type: AdvisorySourceType
    source_reference: str | None
    feedback_type: AdvisoryFeedbackType
    note: str | None
    created_at: datetime


class LearnedPreference(BaseModel):
    signal_name: str
    observation: str | None
    evidence_count: int
    confidence: str | None
    last_observed_at: datetime | None
    explanation: str


class PersonalizationProfileResponse(BaseModel):
    farmer_id: uuid.UUID
    preferences: list[LearnedPreference]


class FeatureSnapshot(BaseModel):
    feature_version: str
    crop_cycle_id: uuid.UUID
    extracted_at: datetime
    available_at_time: dict
    outcome_label: dict | None
    outcome_known_only_after: date | None


class LearningSummaryResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    feature_snapshot: FeatureSnapshot
    ml_training_justified: bool
    ml_readiness_note: str
