import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.crop_cycle import Season


class CropCycleSeasonHistoryResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    season: Season
    changed_at: datetime

    model_config = {"from_attributes": True}


class CropCycleSeasonHistoryListResponse(BaseModel):
    items: list[CropCycleSeasonHistoryResponse]
    total: int
