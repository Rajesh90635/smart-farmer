import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.core.area_units import AreaUnit
from app.models.farm import FarmStatus


class PlotCreateRequest(BaseModel):
    plot_name: str = Field(min_length=2, max_length=200)
    area_value: Decimal = Field(gt=0)
    area_unit: AreaUnit
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    soil_type: str | None = Field(default=None, max_length=100)
    irrigation_type: str | None = Field(default=None, max_length=100)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("longitude must be between -180 and 180")
        return v


class PlotUpdateRequest(BaseModel):
    plot_name: str | None = Field(default=None, min_length=2, max_length=200)
    area_value: Decimal | None = Field(default=None, gt=0)
    area_unit: AreaUnit | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    soil_type: str | None = Field(default=None, max_length=100)
    irrigation_type: str | None = Field(default=None, max_length=100)


class PlotResponse(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID
    plot_name: str
    area_value: Decimal
    area_unit: AreaUnit
    latitude: Decimal | None
    longitude: Decimal | None
    soil_type: str | None
    irrigation_type: str | None
    status: FarmStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PlotListResponse(BaseModel):
    items: list[PlotResponse]
    total: int
