import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SoilSampleCreateRequest(BaseModel):
    collection_date: date
    lab_name: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)


class SoilSampleResponse(BaseModel):
    id: uuid.UUID
    plot_id: uuid.UUID
    collection_date: date
    lab_name: str | None
    self_tested: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SoilSampleListResponse(BaseModel):
    items: list[SoilSampleResponse]
    total: int


class SoilTestResultCreateRequest(BaseModel):
    test_date: date
    ph_value: Decimal | None = Field(default=None, ge=0, le=14)
    nitrogen_kg_per_ha: Decimal | None = Field(default=None, ge=0)
    phosphorus_kg_per_ha: Decimal | None = Field(default=None, ge=0)
    potassium_kg_per_ha: Decimal | None = Field(default=None, ge=0)
    organic_carbon_percent: Decimal | None = Field(default=None, ge=0)
    ec_ds_per_m: Decimal | None = Field(default=None, ge=0)
    # D20-09: varies by lab (zinc/boron/iron/manganese/...) - a flexible
    # key/value map rather than fixed columns.
    micronutrients: dict[str, Decimal] | None = None


class SoilTestResultResponse(BaseModel):
    id: uuid.UUID
    soil_sample_id: uuid.UUID
    test_date: date
    ph_value: Decimal | None
    nitrogen_kg_per_ha: Decimal | None
    phosphorus_kg_per_ha: Decimal | None
    potassium_kg_per_ha: Decimal | None
    organic_carbon_percent: Decimal | None
    ec_ds_per_m: Decimal | None
    micronutrients: dict | None
    report_storage_key: str | None
    is_stale: bool
    created_at: datetime


class SoilTestResultListResponse(BaseModel):
    items: list[SoilTestResultResponse]
    total: int
