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
    # D51-02/D51-04 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-entered
    # only, never fabricated sensor/lab data.
    moisture_percent: Decimal | None = Field(default=None, ge=0, le=100)
    defect_notes: str | None = Field(default=None, max_length=1000)


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
    moisture_percent: Decimal | None
    defect_notes: str | None
    status: HarvestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class HarvestListResponse(BaseModel):
    items: list[HarvestResponse]
    total: int


class YieldHistoryEntry(BaseModel):
    """D50-04 (docs/audit/FINAL_CANONICAL_group_C.md): one past harvest for
    this crop, across ANY crop cycle this farmer has closed - never
    fabricated for a cycle with no recorded quantity yet (see
    actual_quantity's own None-ability)."""
    crop_cycle_id: uuid.UUID
    harvest_id: uuid.UUID
    actual_harvest_date: date | None
    actual_quantity: Decimal | None
    unit: str


class YieldHistoryResponse(BaseModel):
    crop_id: uuid.UUID
    items: list[YieldHistoryEntry]
    # None (never a fabricated 0) when no entry in `items` has a real
    # actual_quantity yet - same "don't average nothing into zero"
    # convention as this project's other aggregate fields.
    average_yield: Decimal | None
    average_yield_unit: str | None


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
    # D52-01 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-declared only.
    is_sorted: bool = False
    sorting_notes: str | None = Field(default=None, max_length=500)
    # D51-06 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-declared only,
    # never verified against a real issuing authority.
    certificate_reference: str | None = Field(default=None, max_length=200)
    # D55-05 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-declared
    # preferred pickup/delivery date.
    preferred_pickup_date: date | None = None
    # D52-03 (docs/audit/FINAL_CANONICAL_group_C.md): farmer-declared
    # packing/packaging requirement, free text only.
    packing_requirements: str | None = Field(default=None, max_length=500)


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
    is_sorted: bool
    sorting_notes: str | None
    certificate_reference: str | None
    preferred_pickup_date: date | None
    packing_requirements: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HarvestListingListResponse(BaseModel):
    items: list[HarvestListingResponse]
    total: int
