import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.harvest_listing import CollectionOption
from app.models.harvest_record import HarvestStatus


class HarvestConfirmReadyRequest(BaseModel):
    """Farmer's explicit confirmation - AI/weather may SUGGEST readiness,
    but only this farmer action moves status to READY."""
    actual_harvest_date: date | None = None
    estimated_quantity: Decimal | None = Field(default=None, gt=0)


class HarvestResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    crop_id: uuid.UUID
    expected_harvest_date: date | None
    actual_harvest_date: date | None
    estimated_quantity: Decimal | None
    actual_quantity: Decimal | None
    unit: str
    quality_grade: str | None
    status: HarvestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class HarvestListResponse(BaseModel):
    items: list[HarvestResponse]
    total: int


class HarvestListingCreateRequest(BaseModel):
    quantity_available: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    quality_grade: str | None = None
    expected_availability_date: date | None = None
    service_area: dict | None = None  # approximate only - never exact coordinates
    preferred_price: Decimal | None = Field(default=None, gt=0)
    delivery_option: CollectionOption
    notes: str | None = Field(default=None, max_length=1000)
    confirm_duplicate: bool = False  # set true to proceed despite an existing active listing warning


class HarvestListingResponse(BaseModel):
    id: uuid.UUID
    harvest_record_id: uuid.UUID
    crop_id: uuid.UUID
    quantity_available: Decimal
    unit: str
    quality_grade: str | None
    expected_availability_date: date | None
    service_area: dict | None
    preferred_price: Decimal | None
    delivery_option: CollectionOption
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HarvestListingListResponse(BaseModel):
    items: list[HarvestListingResponse]
    total: int
