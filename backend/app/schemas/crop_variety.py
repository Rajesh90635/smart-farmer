import uuid
from datetime import datetime

from pydantic import BaseModel


class CropVarietyResponse(BaseModel):
    id: uuid.UUID
    crop_id: uuid.UUID
    name: str
    typical_duration_days: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
