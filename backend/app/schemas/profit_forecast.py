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

    data_completeness_notes: list[str]
