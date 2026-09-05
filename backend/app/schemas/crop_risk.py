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
    # D88-07 (docs/audit/c13_governance_farmbrain_security.md): the rule
    # logic version that PRODUCED this score - lets a historical score be
    # explained/reproduced even after the aggregation rule (_aggregate in
    # crop_risk_service.py) changes in a future release.
    rule_version: str
