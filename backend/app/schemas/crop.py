import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.crop_cycle import CultivationStatus, Season


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

    @model_validator(mode="after")
    def validate_dates(self) -> "CropCycleCreateRequest":
        if self.expected_harvest_date is not None and self.expected_harvest_date < self.sowing_date:
            raise ValueError("expected_harvest_date cannot be before sowing_date")
        return self


class CropCycleUpdateRequest(BaseModel):
    season: Season | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    seed_variety: str | None = Field(default=None, max_length=150)
    cultivation_status: CultivationStatus | None = None


class CropCycleCloseRequest(BaseModel):
    actual_harvest_date: date


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
    created_at: datetime

    model_config = {"from_attributes": True}


class CropCycleListResponse(BaseModel):
    items: list[CropCycleResponse]
    total: int
