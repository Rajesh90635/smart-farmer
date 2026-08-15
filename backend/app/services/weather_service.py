"""
Weather service: Farm Location -> WeatherProvider -> cache -> Farmer
(Requirement 11). Never returns fabricated weather (Requirement 51) -
every path either returns real provider data, real cached data (clearly
marked stale if expired), or an honest unavailable state.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.weather_snapshot import WeatherSnapshot, WeatherSnapshotType
from app.repositories import farm_repository, weather_repository
from app.schemas.weather import CropActionAdvisoryResponse, FarmWeatherResponse, ForecastDayResponse, WeatherReadingResponse
from app.services.weather.weather_provider import WeatherProvider, WeatherReading
from app.services.weather_alert_rules import evaluate_spray_condition_warning

_DEFAULT_FORECAST_DAYS = 3


def get_farm_weather(
    db: Session, farmer_id: str, farm_id: uuid.UUID, provider: WeatherProvider, settings: Settings
) -> FarmWeatherResponse:
    farm = farm_repository.get_owned(db, farm_id, uuid.UUID(farmer_id))
    if farm is None:
        raise AppError(error_codes.NOT_FOUND, "Farm not found.", 404)

    if farm.latitude is None or farm.longitude is None:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            "This farm has no location set, so weather cannot be retrieved. Please add a location to the farm.",
            422,
        )

    fresh_current = weather_repository.get_fresh_current(db, farm_id)
    fresh_forecast = weather_repository.get_fresh_forecast(db, farm_id)

    if fresh_current is not None and fresh_forecast:
        return _build_response(fresh_current, fresh_forecast, is_stale=False, settings=settings)

    result = provider.get_weather(
        latitude=float(farm.latitude), longitude=float(farm.longitude), forecast_days=_DEFAULT_FORECAST_DAYS
    )

    if not result.available:
        stale_current = weather_repository.get_latest_current(db, farm_id)
        if stale_current is not None:
            stale_forecast = weather_repository.get_fresh_forecast(db, farm_id) or []
            return _build_response(stale_current, stale_forecast, is_stale=True, settings=settings)
        return FarmWeatherResponse(
            available=False, unavailable_reason=result.unavailable_reason or "Weather information is temporarily unavailable."
        )

    now = datetime.now(timezone.utc)
    current_snapshot = WeatherSnapshot(
        farm_id=farm_id,
        snapshot_type=WeatherSnapshotType.CURRENT,
        provider=result.provider_name,
        temperature_c=result.current.temperature_c,
        feels_like_c=result.current.feels_like_c,
        humidity_percent=result.current.humidity_percent,
        rainfall_mm=result.current.rainfall_mm,
        wind_speed_kmh=result.current.wind_speed_kmh,
        wind_direction_degrees=result.current.wind_direction_degrees,
        condition_code=result.current.condition_code,
        fetched_at=now,
        expires_at=now + timedelta(minutes=settings.weather_current_cache_minutes),
    )
    weather_repository.save_snapshot(db, current_snapshot)

    forecast_snapshots = []
    for day in result.forecast or []:
        snap = WeatherSnapshot(
            farm_id=farm_id,
            snapshot_type=WeatherSnapshotType.FORECAST,
            forecast_date=day.forecast_date,
            provider=result.provider_name,
            temperature_min_c=day.reading.temperature_min_c,
            temperature_max_c=day.reading.temperature_max_c,
            rain_probability_percent=day.reading.rain_probability_percent,
            rainfall_mm=day.reading.rainfall_mm,
            wind_speed_kmh=day.reading.wind_speed_kmh,
            condition_code=day.reading.condition_code,
            sunrise=day.reading.sunrise,
            sunset=day.reading.sunset,
            fetched_at=now,
            expires_at=now + timedelta(minutes=settings.weather_forecast_cache_minutes),
        )
        weather_repository.save_snapshot(db, snap)
        forecast_snapshots.append(snap)

    db.commit()
    return _build_response(current_snapshot, forecast_snapshots, is_stale=False, settings=settings)


def _build_response(current: WeatherSnapshot, forecast: list[WeatherSnapshot], *, is_stale: bool, settings: Settings) -> FarmWeatherResponse:
    return FarmWeatherResponse(
        available=True,
        provider=current.provider,
        is_stale=is_stale,
        fetched_at=current.fetched_at,
        current=WeatherReadingResponse.model_validate(current),
        forecast=[
            ForecastDayResponse(forecast_date=f.forecast_date, reading=WeatherReadingResponse.model_validate(f))
            for f in forecast
        ],
        crop_action=_compute_crop_action_advisory(current, settings),
    )


def _compute_crop_action_advisory(current: WeatherSnapshot, settings: Settings) -> CropActionAdvisoryResponse | None:
    """Re-evaluates the EXACT SAME deterministic rule already used for the
    background spray-condition notification (weather_alert_rules.py) -
    for live, on-screen display only. This does NOT create/dedupe/send a
    Notification row - that pipeline is untouched and still runs
    separately when weather is fetched (weather_alert_orchestration_service.py).
    No new agronomic rule was written for this; it is a read-only reuse
    of the existing pure function."""
    reading = WeatherReading(
        temperature_c=current.temperature_c,
        wind_speed_kmh=current.wind_speed_kmh,
        rain_probability_percent=current.rain_probability_percent,
    )
    candidate = evaluate_spray_condition_warning(reading, settings)
    if candidate is None:
        return None
    return CropActionAdvisoryResponse(
        action="avoid_spraying",
        reason_message_key=candidate.message_key,
        basis="high_wind" if (current.wind_speed_kmh or 0) >= settings.weather_high_wind_kmh_threshold else "rain_expected",
    )
