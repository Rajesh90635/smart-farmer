import uuid

from pydantic import BaseModel


class RiskFactor(BaseModel):
    """Every factor is fully explainable - never a bare number. `value`
    is one of HIGH/MEDIUM/LOW/UNKNOWN; UNKNOWN means the underlying real
    data genuinely doesn't exist, never a guessed default."""
    factor_name: str
    source: str
    value: str
    explanation: str


class CropRiskScoreResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    overall_risk: str
    factors: list[RiskFactor]
    recommendation: str | None
