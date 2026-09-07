import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CropVarietyCreateRequest(BaseModel):
    """D5-02 (docs/audit/FINAL_CANONICAL_group_A.md): admin-authored, same
    convention as CropGradeOptionCreateRequest - no fabricated variety
    dataset, only what an admin actually enters."""
    name: str = Field(min_length=1, max_length=150)
    typical_duration_days: int | None = Field(default=None, gt=0)


class CropVarietyResponse(BaseModel):
    id: uuid.UUID
    crop_id: uuid.UUID
    name: str
    typical_duration_days: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
