"""
Phase 38.1: Crop Performance Score.

Every component is computed from an EXISTING service/repository -
nothing here recalculates financial, risk, treatment, or health logic.
A component is only ever included if real data supports it; missing
components are excluded from the average (never filled with a neutral
50/100 guess), and data_completeness_percent honestly reflects how much
of the score is backed by real data. If ZERO components are available,
the response is insufficient_data, never a fabricated score.
"""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ai_analysis import ResultStatus
from app.models.crop_cycle import CultivationStatus
from app.repositories import ai_analysis_repository, crop_cycle_repository, harvest_repository, treatment_repository
from app.schemas.crop_performance import PerformanceComponent, PerformanceScoreResponse
from app.services import crop_financial_service, treatment_service

_STAGE_SCORES = {
    CultivationStatus.PLANNED: 10,
    CultivationStatus.SOWN: 20,
    CultivationStatus.GROWING: 40,
    CultivationStatus.FLOWERING: 60,
    CultivationStatus.FRUITING: 70,
    CultivationStatus.READY_FOR_HARVEST: 90,
    CultivationStatus.HARVESTED: 100,
    CultivationStatus.CANCELLED: 0,
}

_EFFECTIVENESS_SCORES = {"improved": 100, "no_significant_change": 60, "worsened": 20}
_HEALTH_SCORES = {ResultStatus.HEALTHY: 100, ResultStatus.DISEASE_DETECTED: 40}


def get_performance_score(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> PerformanceScoreResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    components: list[PerformanceComponent] = [
        _stage_component(crop_cycle),
        _health_component(db, farmer_uuid, crop_cycle_id),
        _treatment_component(db, farmer_id, crop_cycle_id),
        _financial_component(db, farmer_id, crop_cycle_id),
        _harvest_component(db, crop_cycle_id),
    ]

    available = [c for c in components if c.score is not None]
    completeness = Decimal(len(available)) / Decimal(len(components)) * 100

    if not available:
        return PerformanceScoreResponse(
            crop_cycle_id=crop_cycle_id,
            insufficient_data=True,
            overall_score=None,
            data_completeness_percent=completeness.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            components=components,
        )

    overall = sum(Decimal(c.score) for c in available) / Decimal(len(available))
    return PerformanceScoreResponse(
        crop_cycle_id=crop_cycle_id,
        insufficient_data=False,
        overall_score=overall.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        data_completeness_percent=completeness.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        components=components,
    )


def _stage_component(crop_cycle) -> PerformanceComponent:
    score = _STAGE_SCORES.get(crop_cycle.cultivation_status)
    return PerformanceComponent(
        name="stage_progression", score=score, explanation=f"Crop cycle is currently at the '{crop_cycle.cultivation_status.value}' stage."
    )


def _health_component(db: Session, farmer_uuid: uuid.UUID, crop_cycle_id: uuid.UUID) -> PerformanceComponent:
    analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    if not analyses:
        return PerformanceComponent(name="health", score=None, explanation="No AI crop health analysis has been recorded yet.")
    most_recent = max(analyses, key=lambda a: a.created_at)
    score = _HEALTH_SCORES.get(most_recent.result_status)
    if score is None:
        return PerformanceComponent(name="health", score=None, explanation="The most recent health analysis was inconclusive.")
    return PerformanceComponent(name="health", score=score, explanation=f"Most recent health analysis: {most_recent.result_status.value}.")


def _treatment_component(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> PerformanceComponent:
    farmer_uuid = uuid.UUID(farmer_id)
    treatments = treatment_repository.list_treatments_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    if not treatments:
        return PerformanceComponent(name="treatment_effectiveness", score=None, explanation="No treatment has been recorded for this crop.")
    most_recent = treatments[0]
    effectiveness = treatment_service.get_effectiveness(db, farmer_id, most_recent.id)
    score = _EFFECTIVENESS_SCORES.get(effectiveness.result)
    if score is None:
        return PerformanceComponent(name="treatment_effectiveness", score=None, explanation="Treatment effectiveness could not be determined yet.")
    return PerformanceComponent(name="treatment_effectiveness", score=score, explanation=f"Most recent treatment effectiveness: {effectiveness.result}.")


def _financial_component(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> PerformanceComponent:
    summary = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle_id)
    if summary.cost_variance_percent is None:
        return PerformanceComponent(name="financial_performance", score=None, explanation="No cost estimate exists to compare actual spending against.")
    percent = summary.cost_variance_percent
    score = max(min(100, 70 + int(percent)), 0)
    return PerformanceComponent(name="financial_performance", score=score, explanation=f"Cost variance vs estimate: {percent}%.")


def _harvest_component(db: Session, crop_cycle_id: uuid.UUID) -> PerformanceComponent:
    harvests = harvest_repository.list_harvests_by_crop_cycle(db, crop_cycle_id)
    if not harvests or harvests[0].actual_harvest_date is None:
        return PerformanceComponent(name="harvest_completion", score=None, explanation="This crop has not been harvested yet.")
    return PerformanceComponent(name="harvest_completion", score=100, explanation="Harvest has been recorded for this crop.")
