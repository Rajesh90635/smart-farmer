import uuid

from pydantic import BaseModel


class ComparisonMetric(BaseModel):
    metric_name: str
    value_a: str | None
    value_b: str | None
    comparison: str


class CropComparisonResponse(BaseModel):
    crop_cycle_id_a: uuid.UUID
    crop_cycle_id_b: uuid.UUID
    metrics: list[ComparisonMetric]
