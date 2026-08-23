"""
Phase 32: Dynamic Profit Forecast.

Reuses Phase 31's cost calculation (via crop_cost_estimate_repository +
ledger_entry_repository) directly - no cost calculation is duplicated
here. The genuinely new piece is projecting FORWARD using only real,
non-fabricated signals:

1. Committed revenue - real, accepted-but-not-yet-completed SaleOrders
   (a genuine agreed transaction, not a guess).
2. Potential additional revenue - ONLY computed when an active,
   unsold HarvestListing exists with the farmer's OWN preferred_price,
   multiplied by the farmer's OWN yield estimate (HarvestRecord.actual_quantity
   if harvested, else estimated_quantity). Both factors are farmer-
   provided data, never a system-invented number. If either factor is
   missing, this is None - never a guess.

No external market-price reference exists for crop selling prices in
this repository (ReferencePrice is scoped to Prompt 9's agricultural
INPUT products only, confirmed by inspection before writing this file) -
so "approved/available selling-price references" here means the
farmer's own listing price, the only real, available signal.
"""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.repositories import crop_cost_estimate_repository, crop_cycle_repository, harvest_repository, ledger_entry_repository, sale_order_repository
from app.schemas.profit_forecast import CropProfitForecastResponse


def _percent(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_profit_forecast(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropProfitForecastResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    notes: list[str] = []

    estimated_cost = crop_cost_estimate_repository.total_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    actual_cost, actual_revenue = ledger_entry_repository.compute_totals(db, crop_cycle_id, farmer_uuid)

    if estimated_cost is None:
        remaining_estimated_cost = None
        projected_total_cost = None
        notes.append("No cost estimate entered yet - cannot project total cost. Add a cost estimate to enable this.")
    else:
        remaining_estimated_cost = max(estimated_cost - actual_cost, Decimal("0"))
        projected_total_cost = actual_cost + remaining_estimated_cost
        if actual_cost > estimated_cost:
            notes.append("Actual spending has already exceeded the estimate - remaining estimated cost is shown as 0, not negative.")

    committed_sales = sale_order_repository.list_committed_but_not_completed_sales_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    committed_revenue = sum((s.net_value for s in committed_sales), Decimal("0"))

    potential_additional_revenue, potential_basis = _compute_potential_additional_revenue(db, crop_cycle_id, notes)

    projected_total_revenue = actual_revenue + committed_revenue + (potential_additional_revenue or Decimal("0"))
    revenue_projection_is_partial = potential_additional_revenue is None

    if projected_total_cost is None:
        projected_profit_loss = None
        projected_profit_loss_percent = None
    else:
        projected_profit_loss = projected_total_revenue - projected_total_cost
        projected_profit_loss_percent = _percent(projected_profit_loss, projected_total_cost) if projected_total_cost else None

    return CropProfitForecastResponse(
        crop_cycle_id=crop_cycle_id,
        estimated_cost=estimated_cost,
        actual_cost=actual_cost,
        remaining_estimated_cost=remaining_estimated_cost,
        projected_total_cost=projected_total_cost,
        actual_revenue=actual_revenue,
        committed_revenue=committed_revenue,
        potential_additional_revenue=potential_additional_revenue,
        potential_additional_revenue_basis=potential_basis,
        projected_total_revenue=projected_total_revenue,
        revenue_projection_is_partial=revenue_projection_is_partial,
        projected_profit_loss=projected_profit_loss,
        projected_profit_loss_percent=projected_profit_loss_percent,
        data_completeness_notes=notes,
    )


def _compute_potential_additional_revenue(db: Session, crop_cycle_id: uuid.UUID, notes: list[str]) -> tuple[Decimal | None, str | None]:
    harvest = harvest_repository.get_most_recent_harvest_by_crop_cycle(db, crop_cycle_id)
    if harvest is None:
        notes.append("No harvest record exists yet - cannot project revenue from an unsold harvest.")
        return None, None

    quantity = harvest.actual_quantity if harvest.actual_quantity is not None else harvest.estimated_quantity
    quantity_label = "actual yield" if harvest.actual_quantity is not None else "estimated yield"
    if quantity is None:
        notes.append("No actual or estimated harvest quantity recorded yet - cannot project revenue from an unsold harvest.")
        return None, None

    listing = harvest_repository.get_active_listing_for_crop_cycle(db, harvest.id)
    if listing is None:
        notes.append("No active harvest listing exists yet - cannot project revenue from unsold harvest without a price to reference.")
        return None, None
    if listing.preferred_price is None:
        notes.append("Your active harvest listing does not have a preferred price set - cannot project revenue from it.")
        return None, None

    potential = (quantity * listing.preferred_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    basis = f"{quantity} {harvest.unit} ({quantity_label}) x Rs {listing.preferred_price}/{harvest.unit} (your listing price)"
    return potential, basis
