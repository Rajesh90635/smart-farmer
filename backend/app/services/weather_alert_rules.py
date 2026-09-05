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
