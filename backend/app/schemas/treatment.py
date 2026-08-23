import uuid
from datetime import date, datetime

from pydantic import BaseModel


class TreatmentCreateRequest(BaseModel):
    case_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    application_date: date
    notes: str | None = None


class TreatmentResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    case_id: uuid.UUID | None
    product_id: uuid.UUID | None
    before_analysis_id: uuid.UUID | None
    before_result_status: str | None
    application_date: date
    notes: str | None
    created_at: datetime


class TreatmentListResponse(BaseModel):
    items: list[TreatmentResponse]


class FollowUpCreateRequest(BaseModel):
    after_analysis_id: uuid.UUID | None = None
    observation_date: date
    notes: str | None = None


class FollowUpResponse(BaseModel):
    id: uuid.UUID
    treatment_id: uuid.UUID
    after_analysis_id: uuid.UUID | None
    after_result_status: str | None
    observation_date: date
    notes: str | None
    created_at: datetime


class FollowUpListResponse(BaseModel):
    items: list[FollowUpResponse]


class EffectivenessResponse(BaseModel):
    treatment_id: uuid.UUID
    result: str
    basis: str
    before_result_status: str | None
    after_result_status: str | None
    has_follow_up: bool
