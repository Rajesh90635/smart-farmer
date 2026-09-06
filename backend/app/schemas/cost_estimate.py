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


class PlotFinancialTotalsResponse(BaseModel):
    """D70-04 (docs/audit/FINAL_CANONICAL_group_C.md): totals across every
    crop cycle this plot has ever had, not just the currently-active one.
    Deliberately scoped to totals only (no per-stage/per-acre breakdown,
    no cost-variance) - a fuller Plot P&L view is tracked separately as
    D71-05 (Missing), not attempted here."""
    plot_id: uuid.UUID
    total_cost: Decimal
    total_revenue: Decimal
    profit_loss: Decimal


class SeasonFinancialTotalsResponse(BaseModel):
    """D70-05: same shape as PlotFinancialTotalsResponse, scoped by
    Season instead of Plot. A fuller Season P&L view is tracked
    separately as D71-07 (Missing), not attempted here."""
    season: str
    total_cost: Decimal
    total_revenue: Decimal
    profit_loss: Decimal


class PlotFinancialSummaryResponse(BaseModel):
    """D71-05 (docs/audit/FINAL_CANONICAL_group_C.md): the fuller Plot P&L
    view D70-04's own PlotFinancialTotalsResponse deliberately deferred -
    same honest-NULL-handling conventions as CropFinancialSummaryResponse
    (estimated_cost/cost_variance None when no estimate rows exist at
    all, never a fabricated zero; per-acre None when the plot's area
    can't be resolved). Deliberately NO stage_summaries here - stages are
    a single crop cycle's own concept and don't aggregate meaningfully
    across a plot's full multi-crop-cycle history."""
    plot_id: uuid.UUID

    estimated_cost: Decimal | None
    actual_cost: Decimal
    cost_variance: Decimal | None
    cost_variance_percent: Decimal | None

    expected_revenue: None = None
    actual_revenue: Decimal

    estimated_profit: None = None
    actual_profit_loss: Decimal
    profit_loss_percent: Decimal | None

    revenue_to_cost_ratio: Decimal | None
    has_any_actual_revenue: bool

    cost_per_acre: Decimal | None = None
    revenue_per_acre: Decimal | None = None
    profit_loss_per_acre: Decimal | None = None


class FarmFinancialSummaryResponse(BaseModel):
    """D71-06: same shape as PlotFinancialSummaryResponse, one level up -
    per-acre uses the sum of every plot's own area_sqm on this farm."""
    farm_id: uuid.UUID

    estimated_cost: Decimal | None
    actual_cost: Decimal
    cost_variance: Decimal | None
    cost_variance_percent: Decimal | None

    expected_revenue: None = None
    actual_revenue: Decimal

    estimated_profit: None = None
    actual_profit_loss: Decimal
    profit_loss_percent: Decimal | None

    revenue_to_cost_ratio: Decimal | None
    has_any_actual_revenue: bool

    cost_per_acre: Decimal | None = None
    revenue_per_acre: Decimal | None = None
    profit_loss_per_acre: Decimal | None = None


class SeasonFinancialSummaryResponse(BaseModel):
    """D71-07: same shape as PlotFinancialSummaryResponse, scoped by
    Season across every plot/farm the farmer owns. No per-acre figures -
    a Season spans an arbitrary number of farms/plots with no single
    area to divide by, unlike Plot/Farm which each have exactly one."""
    season: str

    estimated_cost: Decimal | None
    actual_cost: Decimal
    cost_variance: Decimal | None
    cost_variance_percent: Decimal | None

    expected_revenue: None = None
    actual_revenue: Decimal

    estimated_profit: None = None
    actual_profit_loss: Decimal
    profit_loss_percent: Decimal | None

    revenue_to_cost_ratio: Decimal | None
    has_any_actual_revenue: bool
