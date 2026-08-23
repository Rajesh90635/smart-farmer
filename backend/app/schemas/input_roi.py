import uuid
from decimal import Decimal

from pydantic import BaseModel


class InputCategoryBreakdown(BaseModel):
    category: str
    actual_cost: Decimal
    percent_of_total_cost: Decimal
    estimated_cost: Decimal | None
    variance: Decimal | None
    roi_percent: None = None


class InputRoiResponse(BaseModel):
    crop_cycle_id: uuid.UUID
    total_actual_cost: Decimal
    categories: list[InputCategoryBreakdown]
    roi_attribution_available: bool
    limitation_note: str
