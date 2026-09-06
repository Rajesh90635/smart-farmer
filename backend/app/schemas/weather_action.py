import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ActionAssessmentResponse(BaseModel):
    action_type: str
    status: str
    reason: str
    evidence: dict
    is_deterministic: bool = True


class WindowSuggestionResponse(BaseModel):
    forecast_date: date
    status: str
    reason: str


class CropWeatherActionResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    weather_available: bool
    is_stale: bool
    fetched_at: datetime | None
    assessments: list[ActionAssessmentResponse]
    recommended_spray_window: WindowSuggestionResponse | None
    relevant_pending_spray_task_id: uuid.UUID | None
    data_completeness_notes: list[str]
    # D88-07 (docs/audit/FINAL_CANONICAL_group_D.md): mirrors
    # CropRiskScoreResponse.rule_version - always populated, same as every
    # other rule-driven output in this project.
    rule_version: str
