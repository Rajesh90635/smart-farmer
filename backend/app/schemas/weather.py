from datetime import date, datetime

from pydantic import BaseModel


class WeatherReadingResponse(BaseModel):
    temperature_c: float | None = None
    feels_like_c: float | None = None
    temperature_min_c: float | None = None
    temperature_max_c: float | None = None
    humidity_percent: float | None = None
    rain_probability_percent: float | None = None
    rainfall_mm: float | None = None
    wind_speed_kmh: float | None = None
    wind_direction_degrees: float | None = None
    condition_code: str | None = None
    sunrise: datetime | None = None
    sunset: datetime | None = None

    model_config = {"from_attributes": True}


class ForecastDayResponse(BaseModel):
    forecast_date: date
    reading: WeatherReadingResponse


class CropActionAdvisoryResponse(BaseModel):
    """A live, DISPLAY-ONLY re-evaluation of the exact same deterministic
    rule already used for the background notification pipeline
    (app/services/weather_alert_rules.py:evaluate_spray_condition_warning)
    - no new agronomic rule was invented for this. `None` on
    FarmWeatherResponse.crop_action covers BOTH "conditions are fine,
    nothing to warn about" and "weather data itself unavailable" (in the
    latter case FarmWeatherResponse.available is already False, so the
    farmer sees the unavailable state, not a false "all clear")."""
    action: str  # e.g. "avoid_spraying" - a stable code, never free text
    reason_message_key: str  # the SAME message_key the notification system already uses (farmer_messages.py) - one wording, not two
    basis: str  # e.g. "high_wind" | "rain_expected" - which condition triggered this, for transparency


class FarmWeatherResponse(BaseModel):
    available: bool
    provider: str | None = None
    unavailable_reason: str | None = None
    is_stale: bool = False
    fetched_at: datetime | None = None
    current: WeatherReadingResponse | None = None
    forecast: list[ForecastDayResponse] = []
    crop_action: CropActionAdvisoryResponse | None = None
