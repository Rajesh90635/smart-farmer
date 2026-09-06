import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.crop_damage_record import DamageLossType


class CropDamageRecordCreateRequest(BaseModel):
    policy_id: uuid.UUID
    loss_type: DamageLossType
    extent_percent: Decimal = Field(ge=0, le=100)
    occurred_on: date
    notes: str | None = Field(default=None, max_length=1000)


class CropDamageRecordResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    policy_id: uuid.UUID
    loss_type: DamageLossType
    extent_percent: Decimal
    occurred_on: date
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropDamageRecordListResponse(BaseModel):
    items: list[CropDamageRecordResponse]
    total: int
