"""
Phase 37: Weather -> Action Engine orchestration.

READ-ONLY: this creates no Notification rows and touches no persistence
whatsoever. The existing background notification pipeline
(weather_alert_orchestration_service.py) is completely untouched - this
is purely an additional, farmer-facing, on-demand decision layer,
reusing weather_service.get_farm_weather() (the SAME function Step
15/16 already built) for the underlying weather fetch, never
re-querying WeatherSnapshot directly.

Task integration is ADVISORY ONLY: a pending spraying task is
cross-referenced and its ID surfaced, but never automatically
rescheduled or modified.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.task import TaskStatus, TaskType
from app.repositories import crop_cycle_repository, task_repository
from app.schemas.weather_action import ActionAssessmentResponse, CropWeatherActionResponse, WindowSuggestionResponse
from app.services import weather_action_rules as rules
from app.services import weather_service
from app.services.weather.weather_provider import WeatherProvider, WeatherReading


def get_weather_actions(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, weather_provider: WeatherProvider, settings: Settings
) -> CropWeatherActionResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    farm_id = crop_cycle.plot.farm_id
    notes: list[str] = []

    try:
        weather = weather_service.get_farm_weather(db, farmer_id, farm_id, weather_provider, settings)
    except AppError:
        weather = None

    if weather is None or not weather.available:
        notes.append("Weather data is not available for this farm right now.")
        assessments = [
            ActionAssessmentResponse(action_type=t, status="unknown", reason="Weather data is unavailable.", evidence={})
            for t in ("spray", "irrigation", "harvest")
        ]
        return CropWeatherActionResponse(
            crop_cycle_id=crop_cycle_id,
            weather_available=False,
            is_stale=False,
            fetched_at=None,
            assessments=assessments,
            recommended_spray_window=None,
            relevant_pending_spray_task_id=None,
            data_completeness_notes=notes,
        )

    if weather.is_stale:
        notes.append("The weather data shown is not current - it may be out of date.")

    # A genuine architectural fact, not a bug: rain_probability_percent
    # is only ever populated on FORECAST snapshots in this system, never
    # on CURRENT ones (confirmed directly in weather_service.py's
    # snapshot construction) - a "current" reading has no meaningful
    # concept of rain PROBABILITY. The correct "conditions right now"
    # picture combines current wind/temperature with TODAY's forecast
    # rain probability - both real, both already fetched, never
    # fabricated.
    current_reading = _build_current_assessment_reading(weather.current, weather.forecast)
    assessments = [
        _to_response(rules.assess_spray_conditions(current_reading, settings)),
        _to_response(rules.assess_irrigation_conditions(current_reading, settings)),
        _to_response(rules.assess_harvest_conditions(current_reading, settings)),
    ]

    recommended_window = _find_spray_window(weather.forecast, settings, notes)
    pending_spray_task_id = _find_pending_spray_task(db, crop_cycle_id, farmer_uuid)

    return CropWeatherActionResponse(
        crop_cycle_id=crop_cycle_id,
        weather_available=True,
        is_stale=weather.is_stale,
        fetched_at=weather.fetched_at,
        assessments=assessments,
        recommended_spray_window=recommended_window,
        relevant_pending_spray_task_id=pending_spray_task_id,
        data_completeness_notes=notes,
    )


def _to_reading(response) -> WeatherReading:
    return WeatherReading(
        temperature_c=response.temperature_c,
        humidity_percent=response.humidity_percent,
        rain_probability_percent=response.rain_probability_percent,
        rainfall_mm=response.rainfall_mm,
        wind_speed_kmh=response.wind_speed_kmh,
    )


def _build_current_assessment_reading(current_response, forecast: list) -> WeatherReading:
    """Combines real current wind/temperature with real today's-forecast
    rain probability - see the module-level comment above for why this
    combination is necessary rather than using `current` alone."""
    todays_rain_probability = forecast[0].reading.rain_probability_percent if forecast else None
    todays_rainfall = forecast[0].reading.rainfall_mm if forecast else None
    return WeatherReading(
        temperature_c=current_response.temperature_c,
        humidity_percent=current_response.humidity_percent,
        wind_speed_kmh=current_response.wind_speed_kmh,
        rain_probability_percent=todays_rain_probability,
        rainfall_mm=todays_rainfall,
    )


def _to_response(assessment: rules.ActionAssessment) -> ActionAssessmentResponse:
    return ActionAssessmentResponse(action_type=assessment.action_type, status=assessment.status.value, reason=assessment.reason, evidence=assessment.evidence)


def _find_spray_window(forecast: list, settings: Settings, notes: list[str]) -> WindowSuggestionResponse | None:
    if not forecast:
        notes.append("No forecast data is available to suggest a better spraying window.")
        return None

    for day in forecast:
        reading = _to_reading(day.reading)
        assessment = rules.assess_spray_conditions(reading, settings)
        if assessment.status == rules.ActionStatus.SAFE:
            return WindowSuggestionResponse(forecast_date=day.forecast_date, status=assessment.status.value, reason=assessment.reason)

    notes.append("No suitable spraying window was found in the available forecast data.")
    return None


def _find_pending_spray_task(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID):
    tasks = task_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_id)
    for task in tasks:
        if task.task_type == TaskType.SPRAYING and task.status == TaskStatus.PENDING:
            return task.id
    return None
