"""
WeatherProvider: the abstraction every weather source sits behind
(Requirement 11/40). Flutter never calls a weather provider directly -
only FastAPI does, through this interface - which is what protects API
keys (Requirement 12) and lets the provider be swapped without touching
any endpoint.

Like ModelProvider in the AI phase, every method reports availability
explicitly rather than raising for the expected "no data" case - weather
being unavailable is a normal, safety-relevant outcome the caller must
handle (WEATHER_NOT_CONFIGURED / "temporarily unavailable"), never masked
by an exception someone forgot to catch.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class WeatherReading:
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


@dataclass(frozen=True)
class ForecastDay:
    forecast_date: date
    reading: WeatherReading


@dataclass(frozen=True)
class WeatherResult:
    available: bool
    provider_name: str
    current: WeatherReading | None = None
    forecast: list[ForecastDay] | None = None
    unavailable_reason: str | None = None


class WeatherProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_weather(self, *, latitude: float, longitude: float, forecast_days: int) -> WeatherResult:
        """Fetches current weather + an N-day forecast in one call - never
        fabricates data; returns available=False with a reason on any
        failure (network error, provider down, no provider configured)."""
