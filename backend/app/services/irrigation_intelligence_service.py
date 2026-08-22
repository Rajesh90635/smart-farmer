"""
Phase 38.4: Irrigation Intelligence.

Reuses Phase 37 DIRECTLY - no second weather engine. The underlying
SAFE/CAUTION/UNSAFE/UNKNOWN classification comes from
weather_action_rules.assess_irrigation_conditions (unchanged), and the
current+today's-forecast reading is built via the SAME
_build_current_assessment_reading helper weather_action_engine_service
already uses (imported, not duplicated).

SOIL MOISTURE: confirmed absent from this project by inspection (same
finding as Phase 37) - soil_moisture_available is ALWAYS False, stated
explicitly in every response, never silently omitted.

RECOMMENDATION MAPPING (deterministic, documented):
- weather UNSAFE (heavy rain likely) -> DELAY, regardless of any task.
- weather CAUTION (moderate rain risk) -> MONITOR.
- weather SAFE + a pending irrigation task exists -> IRRIGATE_NOW,
  meaning only "no weather reason to delay your already-planned
  irrigation task" - NEVER a claim that the crop actually needs water.
- weather SAFE + no pending task -> NO_ACTION (nothing to flag).
- weather UNKNOWN -> UNKNOWN.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.task import TaskStatus, TaskType
from app.repositories import crop_cycle_repository, task_repository
from app.schemas.irrigation_intelligence import IrrigationIntelligenceResponse
from app.services import weather_action_rules as rules
from app.services import weather_service
from app.services.weather.weather_provider import WeatherProvider
from app.services.weather_action_engine_service import _build_current_assessment_reading


def get_irrigation_intelligence(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, weather_provider: WeatherProvider, settings: Settings
) -> IrrigationIntelligenceResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    farm_id = crop_cycle.plot.farm_id
    try:
        weather = weather_service.get_farm_weather(db, farmer_id, farm_id, weather_provider, settings)
    except AppError:
        weather = None

    pending_task_id = _find_pending_irrigation_task(db, crop_cycle_id, farmer_uuid)

    if weather is None or not weather.available:
        return IrrigationIntelligenceResponse(
            crop_cycle_id=crop_cycle_id,
            recommendation="unknown",
            reason="Weather data is not available for this farm right now.",
            weather_status="unknown",
            pending_irrigation_task_id=pending_task_id,
            soil_moisture_available=False,
        )

    reading = _build_current_assessment_reading(weather.current, weather.forecast)
    assessment = rules.assess_irrigation_conditions(reading, settings)

    recommendation, reason = _map_recommendation(assessment, pending_task_id)

    return IrrigationIntelligenceResponse(
        crop_cycle_id=crop_cycle_id,
        recommendation=recommendation,
        reason=reason,
        weather_status=assessment.status.value,
        pending_irrigation_task_id=pending_task_id,
        soil_moisture_available=False,
    )


def _map_recommendation(assessment, pending_task_id) -> tuple[str, str]:
    if assessment.status == rules.ActionStatus.UNKNOWN:
        return "unknown", assessment.reason
    if assessment.status == rules.ActionStatus.UNSAFE:
        return "delay", assessment.reason
    if assessment.status == rules.ActionStatus.CAUTION:
        return "monitor", assessment.reason
    if pending_task_id is not None:
        return "irrigate_now", "No weather reason to delay your planned irrigation task. " + assessment.reason
    return "no_action", assessment.reason


def _find_pending_irrigation_task(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID):
    tasks = task_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_id)
    for task in tasks:
        if task.task_type == TaskType.IRRIGATION and task.status == TaskStatus.PENDING:
            return task.id
    return None
