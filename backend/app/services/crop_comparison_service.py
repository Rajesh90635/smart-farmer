"""
Phase 38.2: Crop-to-Crop Comparison.

Reuses crop_performance_service and crop_financial_service DIRECTLY for
both crop cycles - no metric here is recalculated independently. A
metric is only ever compared when BOTH crop cycles have a real value for
it; otherwise the comparison is honestly 'insufficient_data'.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.repositories import crop_cycle_repository
from app.schemas.crop_comparison import ComparisonMetric, CropComparisonResponse
from app.services import crop_financial_service, crop_performance_service

_METRIC_DIRECTIONS = {
    "overall_performance_score": "higher_better",
    "actual_cost": "lower_better",
    "actual_revenue": "higher_better",
    "actual_profit_loss": "higher_better",
}


def compare_crop_cycles(db: Session, farmer_id: str, crop_cycle_id_a: uuid.UUID, crop_cycle_id_b: uuid.UUID) -> CropComparisonResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_a = crop_cycle_repository.get_owned(db, crop_cycle_id_a, farmer_uuid)
    crop_b = crop_cycle_repository.get_owned(db, crop_cycle_id_b, farmer_uuid)
    if crop_a is None or crop_b is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    performance_a = crop_performance_service.get_performance_score(db, farmer_id, crop_cycle_id_a)
    performance_b = crop_performance_service.get_performance_score(db, farmer_id, crop_cycle_id_b)
    financial_a = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle_id_a)
    financial_b = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle_id_b)

    metrics = [
        _build_metric("overall_performance_score", performance_a.overall_score, performance_b.overall_score),
        _build_metric("actual_cost", financial_a.actual_cost, financial_b.actual_cost),
        _build_metric("actual_revenue", financial_a.actual_revenue, financial_b.actual_revenue),
        _build_metric("actual_profit_loss", financial_a.actual_profit_loss, financial_b.actual_profit_loss),
        _build_metric("crop_stage", crop_a.cultivation_status.value, crop_b.cultivation_status.value, comparable=False),
    ]

    return CropComparisonResponse(crop_cycle_id_a=crop_cycle_id_a, crop_cycle_id_b=crop_cycle_id_b, metrics=metrics)


def _build_metric(name: str, value_a, value_b, *, comparable: bool = True) -> ComparisonMetric:
    if value_a is None or value_b is None:
        return ComparisonMetric(metric_name=name, value_a=_stringify(value_a), value_b=_stringify(value_b), comparison="insufficient_data")

    if not comparable:
        comparison = "equal" if value_a == value_b else "not_directly_comparable"
        return ComparisonMetric(metric_name=name, value_a=str(value_a), value_b=str(value_b), comparison=comparison)

    direction = _METRIC_DIRECTIONS.get(name, "higher_better")
    if value_a == value_b:
        comparison = "equal"
    elif (value_a > value_b) == (direction == "higher_better"):
        comparison = "a_higher"
    else:
        comparison = "b_higher"

    return ComparisonMetric(metric_name=name, value_a=str(value_a), value_b=str(value_b), comparison=comparison)


def _stringify(value) -> str | None:
    return str(value) if value is not None else None
