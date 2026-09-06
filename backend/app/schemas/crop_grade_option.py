import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CropGradeOptionCreateRequest(BaseModel):
    grade_code: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    sort_order: int = 0


class CropGradeOptionResponse(BaseModel):
    id: uuid.UUID
    crop_id: uuid.UUID
    grade_code: str
    display_name: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
