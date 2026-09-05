import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.ledger_entry import LedgerCategory


class CropCostEstimateCreateRequest(BaseModel):
    category: LedgerCategory
    estimated_amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    crop_stage_definition_id: uuid.UUID | None = None


class CropCostEstimateResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    crop_stage_definition_id: uuid.UUID | None
    category: str
    estimated_amount: Decimal
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CropCostEstimateListResponse(BaseModel):
    items: list[CropCostEstimateResponse]


class StageFinancialSummary(BaseModel):
    """None (not 0) means no data exists yet for this stage - a farmer
    who hasn't entered an estimate or logged an expense for a stage sees
    an honest gap, never a fabricated zero implying 'nothing was spent'."""
    crop_stage_definition_id: uuid.UUID
    stage_display_name: str
    estimated_amount: Decimal | None
    actual_amount: Decimal | None
    variance: Decimal | None


class CropFinancialSummaryResponse(BaseModel):
    crop_cycle_id: uuid.UUID

    estimated_cost: Decimal | None
    actual_cost: Decimal
    cost_variance: Decimal | None
    cost_variance_percent: Decimal | None

    # ALWAYS None - no yield/price dataset exists in this project; the
    # type itself (Literal None) makes fabricating a value a type error,
    # not just a discipline choice.
    expected_revenue: None = None
    actual_revenue: Decimal

    estimated_profit: None = None
    actual_profit_loss: Decimal
    profit_loss_percent: Decimal | None

    revenue_to_cost_ratio: Decimal | None

    has_any_actual_revenue: bool
    stage_summaries: list[StageFinancialSummary]

    # D72-04/05/06 (docs/FINAL_GAP_REPORT.md): None (not 0) whenever the
    # plot's area can't be resolved - never a fabricated per-acre figure.
    cost_per_acre: Decimal | None = None
    revenue_per_acre: Decimal | None = None
    profit_loss_per_acre: Decimal | None = None
