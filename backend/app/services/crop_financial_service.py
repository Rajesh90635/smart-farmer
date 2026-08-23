"""
Phase 31: Estimated vs Actual Cost + Profit/Loss.

THE ABSOLUTE FINANCIAL RULE: estimated and actual data are computed from
entirely separate sources and never mixed. `expected_revenue` and
`estimated_profit` are ALWAYS None - no yield/selling-price dataset
exists anywhere in this project, and inventing one here would be exactly
the kind of fabricated agricultural/financial data this project
consistently refuses to produce.
"""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.crop_cost_estimate import CropCostEstimate
from app.models.ledger_entry import LedgerEntryType
from app.repositories import ai_reference_repository, crop_cost_estimate_repository, crop_cycle_repository, ledger_entry_repository
from app.schemas.cost_estimate import (
    CropCostEstimateCreateRequest,
    CropCostEstimateListResponse,
    CropCostEstimateResponse,
    CropFinancialSummaryResponse,
    StageFinancialSummary,
)


def create_estimate(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: CropCostEstimateCreateRequest) -> CropCostEstimateResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    estimate = CropCostEstimate(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        crop_stage_definition_id=payload.crop_stage_definition_id,
        category=payload.category.value,
        estimated_amount=payload.estimated_amount,
        description=payload.description,
    )
    crop_cost_estimate_repository.create(db, estimate)
    db.commit()
    db.refresh(estimate)
    return CropCostEstimateResponse.model_validate(estimate)


def list_estimates(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropCostEstimateListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
    estimates = crop_cost_estimate_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return CropCostEstimateListResponse(items=[CropCostEstimateResponse.model_validate(e) for e in estimates])


def delete_estimate(db: Session, farmer_id: str, estimate_id: uuid.UUID) -> None:
    estimate = crop_cost_estimate_repository.get_owned(db, estimate_id, uuid.UUID(farmer_id))
    if estimate is None:
        raise AppError(error_codes.NOT_FOUND, "Cost estimate not found.", 404)
    crop_cost_estimate_repository.delete(db, estimate)
    db.commit()


def _percent(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_financial_summary(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropFinancialSummaryResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    estimated_cost = crop_cost_estimate_repository.total_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    actual_cost, actual_revenue = ledger_entry_repository.compute_totals(db, crop_cycle_id, farmer_uuid)

    cost_variance = (estimated_cost - actual_cost) if estimated_cost is not None else None
    cost_variance_percent = _percent(cost_variance, estimated_cost) if (cost_variance is not None and estimated_cost) else None

    actual_profit_loss = actual_revenue - actual_cost
    profit_loss_percent = _percent(actual_profit_loss, actual_cost) if actual_cost else None
    revenue_to_cost_ratio = (actual_revenue / actual_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if actual_cost else None

    stage_summaries = _build_stage_summaries(db, crop_cycle, crop_cycle_id, farmer_uuid)

    return CropFinancialSummaryResponse(
        crop_cycle_id=crop_cycle_id,
        estimated_cost=estimated_cost,
        actual_cost=actual_cost,
        cost_variance=cost_variance,
        cost_variance_percent=cost_variance_percent,
        actual_revenue=actual_revenue,
        actual_profit_loss=actual_profit_loss,
        profit_loss_percent=profit_loss_percent,
        revenue_to_cost_ratio=revenue_to_cost_ratio,
        has_any_actual_revenue=actual_revenue > 0,
        stage_summaries=stage_summaries,
    )


def _build_stage_summaries(db: Session, crop_cycle, crop_cycle_id: uuid.UUID, farmer_uuid: uuid.UUID) -> list[StageFinancialSummary]:
    """Uses the ACTUAL CropStageDefinition rows for this crop (Prompt 4)
    - never invents stage names. Only stages with at least one estimate
    or one actual expense tagged to them are included, since an untagged
    stage genuinely has no data to show, not a zero."""
    stages = ai_reference_repository.list_stages_for_crop(db, crop_cycle.crop_id)
    estimates = crop_cost_estimate_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    entries = ledger_entry_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)

    summaries = []
    for stage in stages:
        stage_estimates = [e for e in estimates if e.crop_stage_definition_id == stage.id]
        stage_expenses = [e for e in entries if e.crop_stage_definition_id == stage.id and e.entry_type == LedgerEntryType.EXPENSE]

        if not stage_estimates and not stage_expenses:
            continue

        stage_estimated = sum((e.estimated_amount for e in stage_estimates), Decimal("0")) if stage_estimates else None
        stage_actual = sum((e.amount for e in stage_expenses), Decimal("0")) if stage_expenses else None
        stage_variance = (stage_estimated - stage_actual) if (stage_estimated is not None and stage_actual is not None) else None

        summaries.append(
            StageFinancialSummary(
                crop_stage_definition_id=stage.id,
                stage_display_name=stage.display_name,
                estimated_amount=stage_estimated,
                actual_amount=stage_actual,
                variance=stage_variance,
            )
        )
    return summaries
