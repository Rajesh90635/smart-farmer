import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.crop_cycle import CultivationStatus, FailureReason, Season


class CropMasterResponse(BaseModel):
    id: uuid.UUID
    name: str
    local_names: dict | None
    scientific_name: str | None
    category: str | None

    model_config = {"from_attributes": True}


class CropCycleCreateRequest(BaseModel):
    crop_id: uuid.UUID
    season: Season | None = None
    sowing_date: date
    expected_harvest_date: date | None = None
    seed_variety: str | None = Field(default=None, max_length=150)
    # Additive (Phase 1) - optional FK to a structured CropVariety.
    # Independent of seed_variety: a request can set neither, either, or
    # both. Omitting it entirely preserves pre-Phase-1 behavior exactly.
    variety_id: uuid.UUID | None = None
    # D10-10/D11-01: links a re-sown cycle back to the failed one it
    # replaces - optional, never required, so ordinary "plant a new crop"
    # creation is completely unaffected.
    resown_from_crop_cycle_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CropCycleCreateRequest":
        if self.expected_harvest_date is not None and self.expected_harvest_date < self.sowing_date:
            raise ValueError("expected_harvest_date cannot be before sowing_date")
        return self


class CropFailureReportRequest(BaseModel):
    failure_reason: FailureReason


class CropCycleUpdateRequest(BaseModel):
    season: Season | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    seed_variety: str | None = Field(default=None, max_length=150)
    cultivation_status: CultivationStatus | None = None


class CropCycleCloseRequest(BaseModel):
    actual_harvest_date: date
    # D97-10 (docs/FINAL_GAP_REPORT.md): free-text farmer reflection,
    # optional, only ever settable at the moment of closing the cycle -
    # no other endpoint accepts or edits this field afterward.
    lessons_learned: str | None = Field(default=None, max_length=2000)


class CropCycleResponse(BaseModel):
    id: uuid.UUID
    plot_id: uuid.UUID
    crop: CropMasterResponse
    season: Season | None
    sowing_date: date
    expected_harvest_date: date | None
    actual_harvest_date: date | None
    cultivation_status: CultivationStatus
    seed_variety: str | None
    variety_id: uuid.UUID | None
    failure_reason: str | None = None
    resown_from_crop_cycle_id: uuid.UUID | None = None
    # Only ever set by report_crop_failure() - never persisted, always None elsewhere.
    recommended_next_action: str | None = None
    # Only ever set by close_my_crop_cycle() - never editable afterward.
    lessons_learned: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropCycleListResponse(BaseModel):
    items: list[CropCycleResponse]
    total: int
