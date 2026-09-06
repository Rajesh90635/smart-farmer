"""
Weather alert rule engine. Pure functions over already-fetched weather +
crop-cycle data - no I/O, no side effects, fully unit-testable without a
live weather provider or database.

HARD RULES enforced here:
- Never claims certainty from a probability ("rain is likely", never
  "it will rain").
- Never issues a pesticide/chemical recommendation - spray warnings are
  weather-condition-only ("conditions may not be suitable"), never
  "safe to spray".
- Never issues an irrigation instruction - only weather-based information.
- All thresholds come from Settings, never a literal buried in a
  conditional.
"""
import math
from dataclasses import dataclass

from app.core.config import Settings
from app.models.notification import NotificationCategory, NotificationPriority
from app.services.weather.weather_provider import WeatherReading

# D89-01/02/07 (docs/FINAL_GAP_REPORT.md): bump whenever any evaluate_*
# function's actual logic changes, so a historical notification stays
# explainable/reproducible even after the rule itself evolves - mirrors
# crop_risk_service.RULE_VERSION's existing pattern.
RULE_VERSION = "weather_alert_rules_v1"


@dataclass(frozen=True)
class AlertCandidate:
    category: NotificationCategory
    priority: NotificationPriority
    message_key: str
    message_params: dict
    dedup_suffix: str  # combined with farm/date by the caller to build the full dedup_key


def evaluate_rain_alerts(forecast_today: WeatherReading | None, settings: Settings) -> list[AlertCandidate]:
    if forecast_today is None or forecast_today.rain_probability_percent is None:
        return []

    prob = forecast_today.rain_probability_percent
    candidates: list[AlertCandidate] = []

    if prob >= settings.weather_heavy_rain_probability_threshold or (
        forecast_today.rainfall_mm is not None and forecast_today.rainfall_mm >= settings.weather_heavy_rain_mm_threshold
    ):
        candidates.append(
            AlertCandidate(
                category=NotificationCategory.HEAVY_RAIN_ALERT,
                priority=NotificationPriority.HIGH,
                message_key="heavy_rain_alert",
                message_params={"probability": prob},
                dedup_suffix="heavy_rain",
            )
        )
    elif prob >= settings.weather_rain_probability_threshold:
        candidates.append(
            AlertCandidate(
                category=NotificationCategory.RAIN_ALERT,
                priority=NotificationPriority.LOW,
                message_key="rain_alert",
                message_params={"probability": prob},
                dedup_suffix="rain",
            )
        )

    return candidates


def evaluate_extreme_weather_alerts(current: WeatherReading | None, settings: Settings) -> list[AlertCandidate]:
    if current is None:
        return []

    candidates: list[AlertCandidate] = []

    if current.wind_speed_kmh is not None and current.wind_speed_kmh >= settings.weather_high_wind_kmh_threshold:
        candidates.append(
            AlertCandidate(
                category=NotificationCategory.WEATHER_ALERT,
                priority=NotificationPriority.HIGH,
                message_key="high_wind_alert",
                message_params={"wind_speed": current.wind_speed_kmh},
                dedup_suffix="high_wind",
            )
        )

    if current.temperature_c is not None:
        if current.temperature_c >= settings.weather_extreme_heat_celsius_threshold:
            candidates.append(
                AlertCandidate(
                    category=NotificationCategory.WEATHER_ALERT,
                    priority=NotificationPriority.MEDIUM,
                    message_key="extreme_heat_alert",
                    message_params={"temperature": current.temperature_c},
                    dedup_suffix="extreme_heat",
                )
            )
        elif current.temperature_c <= settings.weather_extreme_cold_celsius_threshold:
            candidates.append(
                AlertCandidate(
                    category=NotificationCategory.WEATHER_ALERT,
                    priority=NotificationPriority.MEDIUM,
                    message_key="extreme_cold_alert",
                    message_params={"temperature": current.temperature_c},
                    dedup_suffix="extreme_cold",
                )
            )

    return candidates


def evaluate_severe_weather_co_occurrence(
    current: "WeatherReading | None", forecast_today: "WeatherReading | None", settings: Settings
) -> "AlertCandidate | None":
    """D14-09 (docs/audit/FINAL_CANONICAL_group_A.md): escalates when 2 or
    more of the already-independently-validated conditions below (high
    wind, extreme heat/cold, heavy rain) co-occur - reuses each
    condition's own existing threshold exactly, invents no new
    meteorological classification (storm/cyclone/hail/flood, D15-05..08,
    remain correctly unclassified pending a real external data source)."""
    active_conditions = 0

    if current is not None and current.wind_speed_kmh is not None and current.wind_speed_kmh >= settings.weather_high_wind_kmh_threshold:
        active_conditions += 1

    if current is not None and current.temperature_c is not None and (
        current.temperature_c >= settings.weather_extreme_heat_celsius_threshold
        or current.temperature_c <= settings.weather_extreme_cold_celsius_threshold
    ):
        active_conditions += 1

    if forecast_today is not None and forecast_today.rain_probability_percent is not None and (
        forecast_today.rain_probability_percent >= settings.weather_heavy_rain_probability_threshold
        or (forecast_today.rainfall_mm is not None and forecast_today.rainfall_mm >= settings.weather_heavy_rain_mm_threshold)
    ):
        active_conditions += 1

    if active_conditions < 2:
        return None

    return AlertCandidate(
        category=NotificationCategory.SEVERE_WEATHER_ALERT,
        priority=NotificationPriority.CRITICAL,
        message_key="severe_weather_co_occurrence_alert",
        message_params={},
        dedup_suffix="severe_weather_co_occurrence",
    )


def _magnus_dew_point_c(temperature_c: float, humidity_percent: float) -> float | None:
    """Magnus-formula dew-point approximation - standard meteorological
    formula, not an invented one. Undefined/meaningless below 0% humidity."""
    if humidity_percent <= 0:
        return None
    a, b = 17.27, 237.7
    alpha = (a * temperature_c) / (b + temperature_c) + math.log(humidity_percent / 100.0)
    return (b * alpha) / (a - alpha)


def evaluate_frost_risk(current: WeatherReading | None, settings: Settings) -> "AlertCandidate | None":
    """D15-04 (docs/audit/FINAL_CANONICAL_group_A.md): frost forms when
    the dew point itself is at/below freezing (regardless of the
    reported air temperature, which is measured at a height above the
    colder near-surface layer where frost actually forms) - buildable
    from already-fetched temperature_c/humidity_percent, no new data."""
    if current is None or current.temperature_c is None or current.humidity_percent is None:
        return None
    dew_point_c = _magnus_dew_point_c(current.temperature_c, current.humidity_percent)
    if dew_point_c is None or dew_point_c > settings.weather_frost_dewpoint_celsius_threshold:
        return None

    return AlertCandidate(
        category=NotificationCategory.WEATHER_ALERT,
        priority=NotificationPriority.HIGH,
        message_key="frost_risk_alert",
        message_params={"dew_point": round(dew_point_c, 1)},
        dedup_suffix="frost_risk",
    )


def evaluate_cumulative_rainfall_risk(total_rainfall_mm: float, settings: Settings) -> list["AlertCandidate"]:
    """D15-08/D17-04/D75-01 (docs/audit/FINAL_CANONICAL_group_{A,D}.md):
    flood and waterlogging share the same underlying signal (excess
    cumulative rainfall over a rolling window) at different severity
    thresholds - a basic buildable increment, not real hydrological/
    river-level modeling. Caller (weather_alert_orchestration_service.py)
    computes total_rainfall_mm from weather_snapshots history; this stays
    a pure function over the already-computed number."""
    if total_rainfall_mm >= settings.weather_flood_risk_cumulative_rainfall_mm_threshold:
        return [
            AlertCandidate(
                category=NotificationCategory.WEATHER_ALERT,
                priority=NotificationPriority.HIGH,
                message_key="flood_risk_alert",
                message_params={"total_rainfall_mm": round(total_rainfall_mm, 1)},
                dedup_suffix="flood_risk",
            )
        ]
    if total_rainfall_mm >= settings.weather_waterlogging_risk_cumulative_rainfall_mm_threshold:
        return [
            AlertCandidate(
                category=NotificationCategory.WEATHER_ALERT,
                priority=NotificationPriority.MEDIUM,
                message_key="waterlogging_risk_alert",
                message_params={"total_rainfall_mm": round(total_rainfall_mm, 1)},
                dedup_suffix="waterlogging_risk",
            )
        ]
    return []


def evaluate_consecutive_dry_days_risk(dry_days: int, settings: Settings) -> "AlertCandidate | None":
    """D15-09/D17-05/D75-02 (docs/audit/FINAL_CANONICAL_group_{A,D}.md):
    consecutive-dry-days tracking, a basic buildable increment - true
    soil-moisture-based drought detection needs D18-10's disclosed-absent
    IoT sensor data and stays out of scope until then. Caller computes
    dry_days from weather_snapshots history."""
    if dry_days < settings.weather_drought_risk_consecutive_dry_days_threshold:
        return None
    return AlertCandidate(
        category=NotificationCategory.WEATHER_ALERT,
        priority=NotificationPriority.MEDIUM,
        message_key="drought_risk_alert",
        message_params={"dry_days": dry_days},
        dedup_suffix="drought_risk",
    )


def evaluate_crop_weather_alert(
    *, crop_name: str, cultivation_status: str, forecast_today: WeatherReading | None, settings: Settings
) -> "AlertCandidate | None":
    """Combines crop + stage + weather into one contextual alert. Only
    fires for a heavy-rain scenario currently - the simplest, clearest
    case supportable without inventing agricultural logic that hasn't
    been validated. Additional crop-stage-specific rules should be added
    here as they're actually validated, not guessed."""
    if forecast_today is None or forecast_today.rain_probability_percent is None:
        return None
    if forecast_today.rain_probability_percent < settings.weather_heavy_rain_probability_threshold:
        return None

    return AlertCandidate(
        category=NotificationCategory.CROP_ALERT,
        priority=NotificationPriority.MEDIUM,
        message_key="crop_weather_heavy_rain",
        message_params={"crop_name": crop_name, "stage": cultivation_status},
        dedup_suffix=f"crop_weather:{crop_name}:{cultivation_status}",
    )


def evaluate_spray_condition_warning(current: WeatherReading | None, settings: Settings) -> "AlertCandidate | None":
    """Weather-condition-only warning. NEVER recommends a pesticide,
    dosage, or guarantees effectiveness - only whether the weather itself
    (wind, imminent rain) is unsuitable for spraying anything at all."""
    if current is None:
        return None

    unsuitable = (current.wind_speed_kmh is not None and current.wind_speed_kmh >= settings.weather_high_wind_kmh_threshold) or (
        current.rain_probability_percent is not None and current.rain_probability_percent >= settings.weather_rain_probability_threshold
    )
    if not unsuitable:
        return None

    return AlertCandidate(
        category=NotificationCategory.WEATHER_ALERT,
        priority=NotificationPriority.LOW,
        message_key="spray_condition_warning",
        message_params={},
        dedup_suffix="spray_condition",
    )
