"""
Phase 38.3: Input ROI Recommendation.

THE CENTRAL HONESTY FINDING (confirmed by inspection before writing this
file): Order (Prompt 9 dealer input purchases) has NO crop_cycle_id
anywhere in its schema - unchanged since Phase 29's original finding.
Nothing anywhere in this project decomposes harvest revenue or yield by
which input category caused it. This means a genuine ROI percentage per
input category cannot be honestly calculated - there is no data path
from "spent on fertilizer" to "attributable revenue." roi_percent is
therefore ALWAYS None (typed as Literal[None] in the schema, not just
conventionally null), and roi_attribution_available is always False.

What CAN be honestly reported, using LedgerEntry.category (which IS
genuinely crop-cycle-linked, unlike Order): a real category-wise
spending breakdown, compared against CropCostEstimate's own category
breakdown where it exists. This is an observation and a comparison,
never a recommendation implying causal benefit.
"""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ledger_entry import LedgerEntryType
from app.repositories import crop_cost_estimate_repository, crop_cycle_repository, ledger_entry_repository
from app.schemas.input_roi import InputCategoryBreakdown, InputRoiResponse

_LIMITATION_NOTE = (
    "This project has no data linking input purchases to crop yield or revenue, "
    "so a true return-on-investment percentage per input cannot be honestly calculated. "
    "The figures below show actual spending by category only."
)


def get_input_roi(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> InputRoiResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    entries = ledger_entry_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    expense_entries = [e for e in entries if e.entry_type == LedgerEntryType.EXPENSE]
    estimates = crop_cost_estimate_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)

    actual_by_category: dict[str, Decimal] = {}
    for entry in expense_entries:
        actual_by_category[entry.category.value] = actual_by_category.get(entry.category.value, Decimal("0")) + entry.amount

    estimated_by_category: dict[str, Decimal] = {}
    for estimate in estimates:
        estimated_by_category[estimate.category] = estimated_by_category.get(estimate.category, Decimal("0")) + estimate.estimated_amount

    total_actual = sum(actual_by_category.values(), Decimal("0"))

    categories = []
    for category, actual_cost in sorted(actual_by_category.items()):
        percent = (actual_cost / total_actual * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_actual else Decimal("0")
        estimated_cost = estimated_by_category.get(category)
        variance = (estimated_cost - actual_cost) if estimated_cost is not None else None
        categories.append(
            InputCategoryBreakdown(
                category=category,
                actual_cost=actual_cost,
                percent_of_total_cost=percent,
                estimated_cost=estimated_cost,
                variance=variance,
            )
        )

    return InputRoiResponse(
        crop_cycle_id=crop_cycle_id,
        total_actual_cost=total_actual,
        categories=categories,
        roi_attribution_available=False,
        limitation_note=_LIMITATION_NOTE,
    )
