"""
Orchestrates weather + crop-weather alert generation. Two triggers now
call the exact same `generate_alerts_for_farm_weather` function - no
redesign was needed to add the second one:

1. Pull-based: whenever a farmer's weather is fetched (`GET .../weather`).
2. D16-10 (docs/audit/c03_weather_water_soil.md): a proactive background
   sweep (`run_proactive_weather_alert_sweep`, called by
   app/services/scheduler.py) that checks every farm with a location,
   closing the previously-disclosed "a farmer who never opens the app
   never gets warned of a heavy-rain event" safety gap.

Failures here must never break the weather response itself - alert
generation is best-effort and wrapped defensively by the caller (the
pull-based path); the sweep wraps each farm individually the same way.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.crop_cycle import CropCycle, CultivationStatus
from app.models.farm import Farm
from app.models.plot import Plot
from app.repositories import farm_repository, user_repository, weather_repository
from app.schemas.weather import FarmWeatherResponse
from app.services import notification_service
from app.services.weather.weather_provider import WeatherProvider, WeatherReading
from app.services.weather_alert_rules import (
    RULE_VERSION,
    evaluate_consecutive_dry_days_risk,
    evaluate_crop_weather_alert,
    evaluate_cumulative_rainfall_risk,
    evaluate_extreme_weather_alerts,
    evaluate_frost_risk,
    evaluate_rain_alerts,
    evaluate_severe_weather_co_occurrence,
    evaluate_spray_condition_warning,
)

_ACTIVE_STATUSES = tuple(s for s in CultivationStatus if s not in (CultivationStatus.HARVESTED, CultivationStatus.CANCELLED))

logger = logging.getLogger(__name__)


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
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
        )
        if n:
            created.append(n)

    for candidate in evaluate_extreme_weather_alerts(current_reading, settings):
        n = notification_service.create_alert_notification(
            db, farmer_id, candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
        )
        if n:
            created.append(n)

    spray_candidate = evaluate_spray_condition_warning(current_reading, settings)
    if spray_candidate:
        n = notification_service.create_alert_notification(
            db, farmer_id, spray_candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
        )
        if n:
            created.append(n)

    frost_candidate = evaluate_frost_risk(current_reading, settings)
    if frost_candidate:
        n = notification_service.create_alert_notification(
            db, farmer_id, frost_candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
        )
        if n:
            created.append(n)

    severe_candidate = evaluate_severe_weather_co_occurrence(current_reading, forecast_today, settings)
    if severe_candidate:
        n = notification_service.create_alert_notification(
            db, farmer_id, severe_candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
        )
        if n:
            created.append(n)

    # D15-08/D15-09/D17-04/D17-05 (docs/audit/FINAL_CANONICAL_group_A.md):
    # cumulative-rainfall/consecutive-dry-days risk, computed here (DB
    # history query) and evaluated by the pure rule functions - the
    # buildable increment this project's own weather_snapshots history
    # already supports, not real hydrological/soil-moisture modeling.
    now = datetime.now(timezone.utc)
    history = weather_repository.list_current_since(
        db, farm.id, now - timedelta(days=max(settings.weather_cumulative_rainfall_window_days, settings.weather_drought_risk_consecutive_dry_days_threshold + 1))
    )
    total_rainfall_mm = sum(
        s.rainfall_mm or 0.0 for s in history if s.fetched_at >= now - timedelta(days=settings.weather_cumulative_rainfall_window_days)
    )
    for candidate in evaluate_cumulative_rainfall_risk(total_rainfall_mm, settings):
        n = notification_service.create_alert_notification(
            db, farmer_id, candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
        )
        if n:
            created.append(n)

    dry_days = _count_consecutive_dry_days(history, today=now.date(), dry_threshold_mm=settings.weather_dry_day_rainfall_mm_threshold)
    drought_candidate = evaluate_consecutive_dry_days_risk(dry_days, settings)
    if drought_candidate:
        n = notification_service.create_alert_notification(
            db, farmer_id, drought_candidate, dedup_scope=dedup_scope, language_code=language_code,
            related_entity_type="farm", related_entity_id=str(farm.id), rule_version=RULE_VERSION,
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
                related_entity_type="crop_cycle", related_entity_id=str(cycle.id), rule_version=RULE_VERSION,
            )
            if n:
                created.append(n)

    return created


def run_proactive_weather_alert_sweep(
    db: Session, weather_provider: WeatherProvider, settings: Settings, *, farm_ids: list | None = None
) -> int:
    """D16-10: called by the background scheduler, not a farmer request.
    Reuses weather_service.get_farm_weather (the same cache-aware fetch
    the pull-based endpoint uses - a farm whose weather was already
    fetched recently by the farmer just serves the cached reading, no
    duplicate provider call) and the exact same alert-generation function
    as the pull-based path. `farm_ids` narrows the sweep to a specific set
    (a targeted manual re-run, or a test) - the real scheduled job omits it."""
    from app.services import weather_service

    total_created = 0
    for farm in farm_repository.list_active_with_location(db, farm_ids=farm_ids):
        try:
            weather = weather_service.get_farm_weather(db, str(farm.farmer_id), farm.id, weather_provider, settings)
            language_code = _language_for(db, farm.farmer_id)
            created = generate_alerts_for_farm_weather(db, str(farm.farmer_id), farm, weather, language_code, settings)
            total_created += len(created)
        except Exception:
            logger.exception("proactive_weather_alert_sweep failed for farm %s - continuing with the rest", farm.id)
            db.rollback()
    return total_created


def _count_consecutive_dry_days(history: list, *, today, dry_threshold_mm: float) -> int:
    """Counts trailing consecutive calendar days (ending yesterday - today's
    data may be partial, so it's never counted either way) where the
    summed rainfall across every CURRENT snapshot fetched that day stayed
    under the dry threshold. Stops at the first day with NO snapshot data
    at all (unknown, never assumed dry) or with rainfall at/above the
    threshold - conservative by design, never overcounts from missing
    history."""
    by_date: dict = {}
    for snapshot in history:
        # The DB driver can return an aware datetime expressed in the
        # session/connection's local timezone rather than UTC (observed:
        # IST) - calling .date() on it directly would bucket it under the
        # wrong calendar day whenever the local time-of-day crosses
        # midnight relative to UTC. Always normalize to UTC first, matching
        # `today`'s own UTC basis exactly.
        day = snapshot.fetched_at.astimezone(timezone.utc).date()
        by_date[day] = by_date.get(day, 0.0) + (snapshot.rainfall_mm or 0.0)

    count = 0
    day = today - timedelta(days=1)
    while day in by_date and by_date[day] < dry_threshold_mm:
        count += 1
        day -= timedelta(days=1)
    return count


def _language_for(db: Session, farmer_id) -> str:
    user = user_repository.get_by_id(db, farmer_id)
    if user and getattr(user, "farmer_profile", None):
        return user.farmer_profile.preferred_language_code
    return "en"


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
