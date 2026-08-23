"""
Orchestrates weather + crop-weather alert generation, triggered whenever
a farmer's weather is fetched (pull-based - this project has no
background push scheduler yet, see docs/NOTIFICATION_ARCHITECTURE.md for
why that's a disclosed, deliberate scope limit rather than an oversight).

Failures here must never break the weather response itself - alert
generation is best-effort and wrapped defensively by the caller.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.crop_cycle import CropCycle, CultivationStatus
from app.models.farm import Farm
from app.models.plot import Plot
from app.schemas.weather import FarmWeatherResponse
from app.services import notification_service
from app.services.weather.weather_provider import WeatherReading
from app.services.weather_alert_rules import (
    evaluate_crop_weather_alert,
    evaluate_extreme_weather_alerts,
    evaluate_rain_alerts,
    evaluate_spray_condition_warning,
)

_ACTIVE_STATUSES = tuple(s for s in CultivationStatus if s not in (CultivationStatus.HARVESTED, CultivationStatus.CANCELLED))


def generate_alerts_for_farm_weather(
    db: Session, farmer_id: str, farm: Farm, weather: FarmWeatherResponse, language_code: str, settings: Settings
) -> list:
    if not weather.available:
        return []

    today_bucket = datetime.now(timezone.utc).date().isoformat()
    dedup_scope = f"farm:{farm.id}:{today_bucket}"

    current_reading = _to_reading(weather.current) if weather.current else None
    forecast_today = _to_reading(weather.forecast[0].reading) if weather.forecast else None

    created = []

    for candidate in evaluate_rain_alerts(forecast_today, settings):
        n = notification_service.create_alert_notification(
            db, farmer_id, candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id),
        )
        if n:
            created.append(n)

    for candidate in evaluate_extreme_weather_alerts(current_reading, settings):
        n = notification_service.create_alert_notification(
            db, farmer_id, candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id),
        )
        if n:
            created.append(n)

    spray_candidate = evaluate_spray_condition_warning(current_reading, settings)
    if spray_candidate:
        n = notification_service.create_alert_notification(
            db, farmer_id, spray_candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id),
        )
        if n:
            created.append(n)

    active_cycles = db.execute(
        select(CropCycle)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .where(Plot.farm_id == farm.id, CropCycle.cultivation_status.in_(_ACTIVE_STATUSES))
    ).scalars().all()

    for cycle in active_cycles:
        candidate = evaluate_crop_weather_alert(
            crop_name=cycle.crop.name, cultivation_status=cycle.cultivation_status.value, forecast_today=forecast_today, settings=settings
        )
        if candidate:
            n = notification_service.create_alert_notification(
                db, farmer_id, candidate, dedup_scope=f"{dedup_scope}:cycle:{cycle.id}", language_code=language_code,
                related_entity_type="crop_cycle", related_entity_id=str(cycle.id),
            )
            if n:
                created.append(n)

    return created


def _to_reading(reading_response) -> WeatherReading:
    return WeatherReading(
        temperature_c=reading_response.temperature_c,
        feels_like_c=reading_response.feels_like_c,
        temperature_min_c=reading_response.temperature_min_c,
        temperature_max_c=reading_response.temperature_max_c,
        humidity_percent=reading_response.humidity_percent,
        rain_probability_percent=reading_response.rain_probability_percent,
        rainfall_mm=reading_response.rainfall_mm,
        wind_speed_kmh=reading_response.wind_speed_kmh,
        wind_direction_degrees=reading_response.wind_direction_degrees,
        condition_code=reading_response.condition_code,
        sunrise=reading_response.sunrise,
        sunset=reading_response.sunset,
    )
