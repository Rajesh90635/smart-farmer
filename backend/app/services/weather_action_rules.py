"""
Phase 37: Weather -> Action Engine deterministic rules.

THE CRITICAL GAP THIS FIXES: the existing evaluate_spray_condition_warning
(weather_alert_rules.py) is a one-way "warn if bad" function - it returns
None both when conditions are genuinely fine AND when data is missing,
conflating SAFE with UNKNOWN. That function is LEFT UNTOUCHED (the
background notification pipeline still calls it exactly as before) -
these are NEW, separate, fuller classifiers for the farmer-facing
advisor, reusing the EXACT SAME Settings thresholds so both systems
agree on what counts as risky.

Every classifier explicitly returns UNKNOWN (never SAFE) when the
specific reading it depends on is None - missing data must never be
silently treated as "no risk."

No LLM anywhere in this decision path - purely deterministic rule
evaluation.
"""
import enum
from dataclasses import dataclass, field

from app.core.config import Settings
from app.services.weather.weather_provider import WeatherReading


class ActionStatus(str, enum.Enum):
    SAFE = "safe"
    CAUTION = "caution"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ActionAssessment:
    action_type: str
    status: ActionStatus
    reason: str
    evidence: dict = field(default_factory=dict)


def assess_spray_conditions(reading: WeatherReading | None, settings: Settings) -> ActionAssessment:
    if reading is None:
        return ActionAssessment("spray", ActionStatus.UNKNOWN, "No weather data is available.", {})

    wind = reading.wind_speed_kmh
    rain = reading.rain_probability_percent

    if wind is None and rain is None:
        return ActionAssessment("spray", ActionStatus.UNKNOWN, "Wind speed and rain probability are both unavailable.", {})

    evidence = {}
    if wind is not None:
        evidence["wind_speed_kmh"] = wind
    if rain is not None:
        evidence["rain_probability_percent"] = rain

    if rain is not None and rain >= settings.weather_heavy_rain_probability_threshold:
        return ActionAssessment("spray", ActionStatus.UNSAFE, "Heavy rain is likely - spray would likely wash off.", evidence)
    if wind is not None and wind >= settings.weather_high_wind_kmh_threshold:
        return ActionAssessment("spray", ActionStatus.UNSAFE, "Wind is too strong for safe, accurate spraying.", evidence)
    if rain is not None and rain >= settings.weather_rain_probability_threshold:
        return ActionAssessment("spray", ActionStatus.CAUTION, "There is a moderate chance of rain interfering with spraying.", evidence)

    if wind is None or rain is None:
        missing = "wind speed" if wind is None else "rain probability"
        return ActionAssessment("spray", ActionStatus.CAUTION, f"Conditions look acceptable, but {missing} data is missing to be fully certain.", evidence)

    return ActionAssessment("spray", ActionStatus.SAFE, "Wind and rain conditions look suitable for spraying.", evidence)


def assess_irrigation_conditions(reading: WeatherReading | None, settings: Settings) -> ActionAssessment:
    if reading is None or reading.rain_probability_percent is None:
        return ActionAssessment("irrigation", ActionStatus.UNKNOWN, "Rain probability data is unavailable.", {})

    rain = reading.rain_probability_percent
    evidence = {"rain_probability_percent": rain}
    if rain >= settings.weather_heavy_rain_probability_threshold:
        return ActionAssessment("irrigation", ActionStatus.UNSAFE, "Heavy rain is likely - delay irrigation to avoid waterlogging.", evidence)
    if rain >= settings.weather_rain_probability_threshold:
        return ActionAssessment("irrigation", ActionStatus.CAUTION, "Rain is fairly likely - consider waiting before irrigating.", evidence)
    return ActionAssessment("irrigation", ActionStatus.SAFE, "No significant rain expected - irrigation timing is your own call.", evidence)


def assess_harvest_conditions(reading: WeatherReading | None, settings: Settings) -> ActionAssessment:
    if reading is None or reading.rain_probability_percent is None:
        return ActionAssessment("harvest", ActionStatus.UNKNOWN, "Rain probability data is unavailable.", {})

    rain = reading.rain_probability_percent
    evidence = {"rain_probability_percent": rain}
    if rain >= settings.weather_heavy_rain_probability_threshold:
        return ActionAssessment("harvest", ActionStatus.UNSAFE, "Heavy rain is likely - postpone harvest to avoid crop/quality loss.", evidence)
    if rain >= settings.weather_rain_probability_threshold:
        return ActionAssessment("harvest", ActionStatus.CAUTION, "Rain is fairly likely - harvesting today carries some risk.", evidence)
    return ActionAssessment("harvest", ActionStatus.SAFE, "No significant rain expected - conditions look suitable for harvest.", evidence)
