from datetime import date, datetime

from pydantic import BaseModel, model_validator

from app.services.weather.wmo_codes import classify_condition_code


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
    # D15-05/D15-07 (docs/audit/FINAL_CANONICAL_group_A.md): decoded from
    # condition_code via the real WMO code table (app/services/weather/
    # wmo_codes.py) - never a separate fabricated classification. None
    # whenever condition_code itself is None.
    is_storm: bool | None = None
    is_hail: bool | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _classify_condition_code(self) -> "WeatherReadingResponse":
        classification = classify_condition_code(self.condition_code)
        self.is_storm = classification.is_storm
        self.is_hail = classification.is_hail
        return self


class ForecastDayResponse(BaseModel):
    forecast_date: date
    reading: WeatherReadingResponse


class HourlyForecastResponse(BaseModel):
    """D14-02 (docs/audit/FINAL_CANONICAL_group_A.md)."""
    timestamp: datetime
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
    # D14-02 (docs/audit/FINAL_CANONICAL_group_A.md): the next 24 real
    # hourly readings, oldest first - empty (never fabricated) whenever
    # the provider/cache has none yet.
    hourly: list[HourlyForecastResponse] = []
    crop_action: CropActionAdvisoryResponse | None = None
    # D88-05 (docs/audit/FINAL_CANONICAL_group_D.md): the farm's already-
    # seeded Mandal/Village master data, surfaced alongside the reading -
    # None whenever the farm has no resolvable mandal/village (never
    # fabricated), never a second/duplicate location dataset.
    region: dict | None = None
