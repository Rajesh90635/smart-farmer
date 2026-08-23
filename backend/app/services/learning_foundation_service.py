"""
Phase 39: ML Foundation / Feature Snapshot.

NO TRAINED MODEL EXISTS ANYWHERE IN THIS PROJECT. This service builds a
FeatureSnapshot structure representing what a future training pipeline
WOULD extract - purely illustrative of the foundation, never a
prediction, never a model output. `ml_training_justified` is always
False, and `ml_readiness_note` states this plainly every time.

TEMPORAL LEAKAGE PREVENTION (mandatory, tested): `outcome_label` is only
ever populated when the crop cycle has genuinely reached a terminal,
harvested state - never for an in-progress crop cycle. This prevents a
recommendation made mid-season from ever being paired with an outcome
that hadn't happened yet at the time. `outcome_known_only_after` records
exactly when the outcome became knowable, for future leakage auditing.

Reuses Phase 38's performance service and Phase 31's financial service
directly for the "available_at_time" signals - nothing recalculated.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.crop_cycle import CultivationStatus
from app.repositories import crop_cycle_repository, harvest_repository
from app.schemas.personalization import FeatureSnapshot, LearningSummaryResponse
from app.services import crop_financial_service, crop_performance_service

_FEATURE_VERSION = "v1-foundation"
_ML_READINESS_NOTE = (
    "ML training is not yet justified by the available dataset - this project does not yet have "
    "a sufficient volume of trustworthy, labeled historical outcomes to train or evaluate a model. "
    "This response represents the ML-ready feature foundation only, not a prediction."
)


def get_learning_summary(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> LearningSummaryResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    performance = crop_performance_service.get_performance_score(db, farmer_id, crop_cycle_id)
    financial = crop_financial_service.get_financial_summary(db, farmer_id, crop_cycle_id)

    available_at_time = {
        "cultivation_status": crop_cycle.cultivation_status.value,
        "performance_score": str(performance.overall_score) if performance.overall_score is not None else None,
        "actual_cost_so_far": str(financial.actual_cost),
    }

    outcome_label = None
    outcome_known_only_after = None
    if crop_cycle.cultivation_status == CultivationStatus.HARVESTED:
        harvests = harvest_repository.list_harvests_by_crop_cycle(db, crop_cycle_id)
        harvested = next((h for h in harvests if h.actual_harvest_date is not None), None)
        if harvested is not None:
            outcome_label = {
                "actual_revenue": str(financial.actual_revenue),
                "actual_profit_loss": str(financial.actual_profit_loss),
            }
            outcome_known_only_after = harvested.actual_harvest_date

    snapshot = FeatureSnapshot(
        feature_version=_FEATURE_VERSION,
        crop_cycle_id=crop_cycle_id,
        extracted_at=datetime.now(timezone.utc),
        available_at_time=available_at_time,
        outcome_label=outcome_label,
        outcome_known_only_after=outcome_known_only_after,
    )

    return LearningSummaryResponse(
        crop_cycle_id=crop_cycle_id,
        feature_snapshot=snapshot,
        ml_training_justified=False,
        ml_readiness_note=_ML_READINESS_NOTE,
    )
