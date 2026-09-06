"""
D91-09/D91-10 (docs/audit/FINAL_CANONICAL_group_D.md): turns individual
farmer_correction rows (D91-07) into real false-positive/false-negative
rates, feeding ai/evaluation.py's dormant EvaluationReport shape with
actual data instead of synthetic pairs. Admin-only, read-only, no writes.
"""
from sqlalchemy.orm import Session

from app.models.ai_analysis import FarmerCorrection, ResultStatus
from app.repositories import ai_analysis_repository
from app.schemas.ai_analysis import AIEvaluationAggregateResponse


def get_correction_aggregate(db: Session) -> AIEvaluationAggregateResponse:
    total_disease_detected = ai_analysis_repository.count_by_result_status(db, ResultStatus.DISEASE_DETECTED)
    total_healthy = ai_analysis_repository.count_by_result_status(db, ResultStatus.HEALTHY)

    false_positive_count = ai_analysis_repository.count_by_result_status_and_correction(
        db, ResultStatus.DISEASE_DETECTED, FarmerCorrection.ACTUALLY_HEALTHY.value
    )
    false_negative_count = ai_analysis_repository.count_by_result_status_and_correction(
        db, ResultStatus.HEALTHY, FarmerCorrection.ACTUALLY_DISEASED.value
    )
    confirmed_correct_count = ai_analysis_repository.count_by_correction(db, FarmerCorrection.CONFIRMED_CORRECT.value)
    wrong_disease_name_count = ai_analysis_repository.count_by_correction(db, FarmerCorrection.WRONG_DISEASE_NAME.value)

    return AIEvaluationAggregateResponse(
        total_disease_detected=total_disease_detected,
        total_healthy=total_healthy,
        false_positive_count=false_positive_count,
        false_positive_rate=(false_positive_count / total_disease_detected) if total_disease_detected else None,
        false_negative_count=false_negative_count,
        false_negative_rate=(false_negative_count / total_healthy) if total_healthy else None,
        confirmed_correct_count=confirmed_correct_count,
        wrong_disease_name_count=wrong_disease_name_count,
    )
