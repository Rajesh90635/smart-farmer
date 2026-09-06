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
    # D96-01 (docs/audit/FINAL_CANONICAL_group_D.md): crop identity itself
    # is not a "metric" (there is no higher/lower/better direction to a
    # crop being the same or different), so it is a top-level flag rather
    # than another ComparisonMetric row.
    same_crop: bool
    metrics: list[ComparisonMetric]
