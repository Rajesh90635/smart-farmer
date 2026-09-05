"""
Phase 33: Crop Risk Score.

Every factor reuses an EXISTING subsystem's real data - nothing here
duplicates disease detection, weather rules, task logic, or financial
calculation. A factor is only ever HIGH/MEDIUM/LOW when real data
supports it; otherwise it is UNKNOWN, and the overall score is
INSUFFICIENT_DATA if literally nothing evaluable exists - never a
fabricated "low risk" from an absence of information.

Treatment/recommendation-effectiveness tracking does not exist anywhere
in this application (confirmed by inspection before this file was
written) - that factor is therefore ALWAYS reported as unknown, honestly.

`recommendation` is a suggestion, never a confirmed fact - kept
separate from the observed factors themselves.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ai_analysis import ResultStatus
from app.models.crop_health_case import CaseStatus
from app.repositories import ai_analysis_repository, case_repository, crop_cycle_repository, task_repository
from app.schemas.crop_risk import CropRiskScoreResponse, RiskFactor
from app.services import crop_financial_service, task_service

# D88-07: bump whenever _aggregate/_build_recommendation's actual logic
# changes, so a historical score stays explainable/reproducible even
# after the rule itself evolves - never silently reinterpreted under an
# unversioned "current" rule.
RULE_VERSION = "crop_risk_v1"


def get_risk_score(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, *, weather_provider=None, settings=None) -> CropRiskScoreResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    factors = [
        _recent_disease_factor(db, crop_cycle_id, farmer_uuid),
        _disease_recurrence_factor(db, crop_cycle_id, farmer_uuid),
        _expert_case_factor(db, crop_cycle_id, farmer_uuid),
        _operational_task_factor(db, crop_cycle_id, farmer_uuid),
        _financial_factor(db, farmer_id, crop_cycle_id),
        _treatment_response_factor(),
    ]
    if weather_provider is not None and settings is not None:
        factors.append(_weather_factor(db, farmer_id, crop_cycle, weather_provider, settings))

    overall = _aggregate(factors)
    recommendation = _build_recommendation(factors, overall)

    return CropRiskScoreResponse(
        crop_cycle_id=crop_cycle_id, overall_risk=overall, factors=factors, recommendation=recommendation,
        rule_version=RULE_VERSION,
    )


def _recent_disease_factor(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> RiskFactor:
    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_id)
    if not analyses:
        return RiskFactor(
            factor_name="Recent Disease Detection", source="AI crop photo analysis", value="unknown",
            explanation="No AI crop analysis has been run yet for this crop.",
        )
    most_recent = max(analyses, key=lambda a: a.created_at)
    if most_recent.result_status == ResultStatus.DISEASE_DETECTED:
        return RiskFactor(
            factor_name="Recent Disease Detection", source="AI crop photo analysis", value="high",
            explanation="The most recent crop photo analysis detected a possible disease.",
        )
    if most_recent.result_status in (ResultStatus.LOW_CONFIDENCE, ResultStatus.CROP_MISMATCH):
        return RiskFactor(
            factor_name="Recent Disease Detection", source="AI crop photo analysis", value="medium",
            explanation="The most recent analysis was inconclusive - a clearer photo or expert review may help.",
        )
    if most_recent.result_status == ResultStatus.HEALTHY:
        return RiskFactor(
            factor_name="Recent Disease Detection", source="AI crop photo analysis", value="low",
            explanation="The most recent crop photo analysis found no signs of disease.",
        )
    return RiskFactor(
        factor_name="Recent Disease Detection", source="AI crop photo analysis", value="unknown",
        explanation="The most recent analysis did not produce a usable result.",
    )


def _disease_recurrence_factor(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> RiskFactor:
    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_id)
    if not analyses:
        return RiskFactor(
            factor_name="Disease Recurrence", source="AI crop photo analysis history", value="unknown",
            explanation="No AI crop analysis history exists yet for this crop.",
        )
    disease_count = sum(1 for a in analyses if a.result_status == ResultStatus.DISEASE_DETECTED)
    if disease_count >= 3:
        value, explanation = "high", f"Disease has been detected {disease_count} separate times during this crop cycle."
    elif disease_count == 2:
        value, explanation = "medium", "Disease has been detected twice during this crop cycle."
    else:
        value, explanation = "low", f"Disease has been detected {disease_count} time(s) during this crop cycle."
    return RiskFactor(factor_name="Disease Recurrence", source="AI crop photo analysis history", value=value, explanation=explanation)


def _expert_case_factor(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> RiskFactor:
    cases = case_repository.list_cases_for_crop_cycle(db, crop_cycle_id, farmer_id)
    if not cases:
        return RiskFactor(
            factor_name="Expert-Verified Case Status", source="Expert/field-agent review", value="unknown",
            explanation="No expert review case has ever been opened for this crop.",
        )
    most_recent = cases[0]
    if most_recent.status == CaseStatus.ESCALATED or most_recent.final_verified_class is not None:
        return RiskFactor(
            factor_name="Expert-Verified Case Status", source="Expert/field-agent review", value="high",
            explanation="An expert case has escalated or confirmed an abnormal finding for this crop.",
        )
    if most_recent.status in (CaseStatus.OPEN, CaseStatus.WAITING_FOR_ASSIGNMENT, CaseStatus.ASSIGNED, CaseStatus.IN_REVIEW, CaseStatus.NEEDS_MORE_INFORMATION):
        return RiskFactor(
            factor_name="Expert-Verified Case Status", source="Expert/field-agent review", value="medium",
            explanation="An expert review is still in progress for this crop.",
        )
    return RiskFactor(
        factor_name="Expert-Verified Case Status", source="Expert/field-agent review", value="low",
        explanation="The most recent expert case for this crop was resolved without an abnormal finding.",
    )


def _operational_task_factor(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> RiskFactor:
    tasks = task_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_id)
    if not tasks:
        return RiskFactor(
            factor_name="Operational Task Risk", source="Farmer task list", value="unknown",
            explanation="No tasks have been recorded yet for this crop.",
        )
    today = datetime.now(timezone.utc).date()
    overdue_count = sum(1 for t in tasks if task_service.compute_display_status(t, today) == "overdue")
    if overdue_count >= 2:
        value, explanation = "high", f"{overdue_count} tasks for this crop are overdue."
    elif overdue_count == 1:
        value, explanation = "medium", "1 task for this crop is overdue."
    else:
        value, explanation = "low", "No tasks for this crop are currently overdue."
    return RiskFactor(factor_name="Operational Task Risk", source="Farmer task list", value=value, explanation=explanation)


def _financial_factor(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> RiskFactor:
    summary = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle_id)
    if summary.cost_variance_percent is None:
        return RiskFactor(
            factor_name="Financial Execution Risk", source="Crop financial summary (Phase 31)", value="unknown",
            explanation="No cost estimate exists yet, so spending cannot be compared against a budget.",
        )
    percent = summary.cost_variance_percent
    if percent < -20:
        value, explanation = "high", f"Actual spending has exceeded the estimate by more than 20% ({abs(percent):.2f}% over)."
    elif percent < 0:
        value, explanation = "medium", f"Actual spending has exceeded the estimate by {abs(percent):.2f}%."
    else:
        value, explanation = "low", "Actual spending is within or under the estimated budget."
    return RiskFactor(factor_name="Financial Execution Risk", source="Crop financial summary (Phase 31)", value=value, explanation=explanation)


def _treatment_response_factor() -> RiskFactor:
    return RiskFactor(
        factor_name="Treatment Response", source="Not tracked in this application", value="unknown",
        explanation="This application does not currently track treatment effectiveness.",
    )


def _weather_factor(db: Session, farmer_id: str, crop_cycle, weather_provider, settings) -> RiskFactor:
    from app.services import weather_service

    farm_id = crop_cycle.plot.farm_id
    try:
        weather = weather_service.get_farm_weather(db, farmer_id, farm_id, weather_provider, settings)
    except AppError:
        return RiskFactor(
            factor_name="Current Weather Risk", source="Weather service", value="unknown",
            explanation="Weather information is not available for this farm.",
        )
    if not weather.available:
        return RiskFactor(
            factor_name="Current Weather Risk", source="Weather service", value="unknown",
            explanation="Weather information is currently unavailable for this farm.",
        )
    if weather.crop_action is not None:
        return RiskFactor(
            factor_name="Current Weather Risk", source="Weather service", value="medium",
            explanation="Current weather conditions may not be suitable for spraying.",
        )
    return RiskFactor(
        factor_name="Current Weather Risk", source="Weather service", value="low",
        explanation="Current weather conditions do not trigger any known alert.",
    )


def _aggregate(factors: list[RiskFactor]) -> str:
    evaluable = [f for f in factors if f.value != "unknown"]
    if not evaluable:
        return "insufficient_data"
    if any(f.value == "high" for f in evaluable):
        return "high"
    medium_count = sum(1 for f in evaluable if f.value == "medium")
    if medium_count >= 2:
        return "high"
    if medium_count >= 1:
        return "medium"
    return "low"


def _build_recommendation(factors: list[RiskFactor], overall: str) -> str | None:
    if overall in ("low", "insufficient_data"):
        return None
    for f in factors:
        if f.factor_name == "Recent Disease Detection" and f.value == "high":
            return "Consider requesting an expert review of this crop's health."
        if f.factor_name == "Current Weather Risk" and f.value == "medium":
            return "Consider delaying spraying until weather conditions improve."
        if f.factor_name == "Financial Execution Risk" and f.value in ("high", "medium"):
            return "Review your recent expenses against your cost estimate."
    return "Review the contributing factors above for details."
