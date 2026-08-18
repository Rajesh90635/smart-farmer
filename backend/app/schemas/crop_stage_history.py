import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.crop_cycle import CultivationStatus


class CropCycleStageHistoryResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    status: CultivationStatus
    entered_at: datetime

    model_config = {"from_attributes": True}


class CropCycleStageHistoryListResponse(BaseModel):
    items: list[CropCycleStageHistoryResponse]
    total: int
