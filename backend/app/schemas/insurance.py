import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InsurancePolicyCreateRequest(BaseModel):
    policy_number: str = Field(min_length=1, max_length=100)
    insurer: str = Field(min_length=1, max_length=200)
    sum_insured: Decimal = Field(gt=0)
    premium: Decimal = Field(gt=0)
    crop_id: uuid.UUID | None = None
    season: str | None = Field(default=None, max_length=100)


class InsurancePolicyResponse(BaseModel):
    id: uuid.UUID
    policy_number: str
    insurer: str
    sum_insured: Decimal
    premium: Decimal
    crop_id: uuid.UUID | None
    season: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InsurancePolicyListResponse(BaseModel):
    items: list[InsurancePolicyResponse]
    total: int
