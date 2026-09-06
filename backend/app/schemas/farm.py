import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.core.area_units import AreaUnit
from app.models.farm import Farm, FarmStatus


class FarmCreateRequest(BaseModel):
    farm_name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    state_id: int | None = None
    district_id: int | None = None
    mandal_id: int | None = None
    village_id: int | None = None
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
    state_id: int | None = None
    district_id: int | None = None
    mandal_id: int | None = None
    village_id: int | None = None
    area_value: Decimal | None = Field(default=None, gt=0)
    area_unit: AreaUnit | None = None


class FarmResponse(BaseModel):
    id: uuid.UUID
    farm_name: str
    description: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    state_id: int | None
    district_id: int | None
    mandal_id: int | None
    village_id: int | None
    # Denormalized names for display only, filled in by from_orm_farm()
    # below from the joined master-data row - never a second source of
    # truth (the *_id fields above remain authoritative; these are None
    # whenever the corresponding id is None or its row was since removed).
    state_name: str | None = None
    district_name: str | None = None
    mandal_name: str | None = None
    village_name: str | None = None
    area_value: Decimal
    area_unit: AreaUnit
    status: FarmStatus
    created_at: datetime
    # D2-08/D2-09 (docs/audit/FINAL_CANONICAL_group_A.md): computed rollup
    # of the farm's own plots - never a separate farm-level column, so
    # there is no duplicate/conflicting data-entry point to keep in sync.
    irrigation_summary: list[str] = []
    soil_summary: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_farm(cls, farm: Farm) -> "FarmResponse":
        response = cls.model_validate(farm)
        response.state_name = farm.state.name if farm.state else None
        response.district_name = farm.district.name if farm.district else None
        response.mandal_name = farm.mandal.name if farm.mandal else None
        response.village_name = farm.village.name if farm.village else None
        # D2-08/D2-09: merges the legacy free-text fields with D3-08/D3-09's
        # later, separate, validated-enum fields (irrigation_source/
        # soil_category) - both are real, independently settable per plot
        # (see app/models/plot.py's own docstring), so a plot classified
        # only via the newer enum field must not be silently dropped from
        # this rollup.
        irrigation_values = {p.irrigation_type for p in farm.plots if p.irrigation_type} | {
            p.irrigation_source.value for p in farm.plots if p.irrigation_source
        }
        soil_values = {p.soil_type for p in farm.plots if p.soil_type} | {p.soil_category.value for p in farm.plots if p.soil_category}
        response.irrigation_summary = sorted(irrigation_values)
        response.soil_summary = sorted(soil_values)
        return response


class FarmListResponse(BaseModel):
    items: list[FarmResponse]
    total: int
