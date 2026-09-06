import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.plot import IrrigationSource


class IrrigationRecordCreateRequest(BaseModel):
    task_id: uuid.UUID | None = None
    irrigation_date: date
    duration_minutes: Decimal | None = Field(default=None, gt=0)
    volume_liters: Decimal | None = Field(default=None, gt=0)
    source: IrrigationSource | None = None
    notes: str | None = Field(default=None, max_length=1000)
    # D18-08: the farmer attempted to irrigate but the pump/equipment failed.
    failure_note: str | None = Field(default=None, max_length=500)


class IrrigationRecordResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    task_id: uuid.UUID | None
    irrigation_date: date
    duration_minutes: Decimal | None
    volume_liters: Decimal | None
    source: IrrigationSource | None
    notes: str | None
    failure_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IrrigationRecordListResponse(BaseModel):
    items: list[IrrigationRecordResponse]
    total: int
