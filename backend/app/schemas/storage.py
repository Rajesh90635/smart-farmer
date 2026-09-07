import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.storage import StorageType


class StorageCreateRequest(BaseModel):
    location: str = Field(max_length=500)
    storage_type: StorageType
    capacity: Decimal | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    cost_per_unit_per_day: Decimal | None = Field(default=None, gt=0)


class StorageResponse(BaseModel):
    id: uuid.UUID
    farmer_id: uuid.UUID
    location: str
    storage_type: StorageType
    capacity: Decimal | None
    unit: str | None
    cost_per_unit_per_day: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StorageListResponse(BaseModel):
    items: list[StorageResponse]
    total: int


class StorageUsageCreateRequest(BaseModel):
    harvest_record_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    unit: str = Field(max_length=20)


class StorageUsageResponse(BaseModel):
    id: uuid.UUID
    storage_id: uuid.UUID
    harvest_record_id: uuid.UUID
    quantity: Decimal
    unit: str
    stored_at: datetime
    released_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StorageUsageListResponse(BaseModel):
    items: list[StorageUsageResponse]
    total: int
