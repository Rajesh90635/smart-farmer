import uuid
from decimal import Decimal

from pydantic import BaseModel


class CropProfitForecastResponse(BaseModel):
    """Phase 32 - Dynamic Profit Forecast.

    THE ABSOLUTE RULE, same as Phase 31: every nullable field here is
    null because the underlying real data genuinely doesn't exist yet -
    never a fabricated placeholder. data_completeness_notes explains IN
    WORDS exactly what's missing and why.
    """
    crop_cycle_id: uuid.UUID

    estimated_cost: Decimal | None
    actual_cost: Decimal
    remaining_estimated_cost: Decimal | None
    projected_total_cost: Decimal | None

    actual_revenue: Decimal
    committed_revenue: Decimal
    potential_additional_revenue: Decimal | None
    potential_additional_revenue_basis: str | None
    projected_total_revenue: Decimal
    revenue_projection_is_partial: bool

    projected_profit_loss: Decimal | None
    projected_profit_loss_percent: Decimal | None

    # D50-03 (docs/audit/FINAL_CANONICAL_group_C.md): same _per_acre pattern
    # as D72-04/05/06's cost/revenue/profit_loss_per_acre, applied to
    # harvest quantity instead - None whenever quantity or plot area is
    # unavailable, never a fabricated figure.
    yield_per_acre: Decimal | None
    yield_per_acre_unit: str | None

    data_completeness_notes: list[str]
