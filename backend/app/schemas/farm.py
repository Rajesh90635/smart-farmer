import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.core.area_units import AreaUnit
from app.models.farm import FarmStatus


class FarmCreateRequest(BaseModel):
    farm_name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    area_value: Decimal = Field(gt=0)
    area_unit: AreaUnit

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


class FarmUpdateRequest(BaseModel):
    farm_name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    area_value: Decimal | None = Field(default=None, gt=0)
    area_unit: AreaUnit | None = None


class FarmResponse(BaseModel):
    id: uuid.UUID
    farm_name: str
    description: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    area_value: Decimal
    area_unit: AreaUnit
    status: FarmStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmListResponse(BaseModel):
    items: list[FarmResponse]
    total: int
