import uuid
from decimal import Decimal

from pydantic import BaseModel


class PerformanceComponent(BaseModel):
    name: str
    score: int | None
    explanation: str


class PerformanceScoreResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    insufficient_data: bool
    overall_score: Decimal | None
    data_completeness_percent: Decimal
    components: list[PerformanceComponent]
