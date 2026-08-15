"""
FakeWeatherProvider - TEST-ONLY, mirrors the FakeModelProvider pattern
from the AI phase. Injected via FastAPI's dependency_overrides only; the
production default remains OpenMeteoProvider/NotConfiguredWeatherProvider
per app/core/weather_provider_dependency.py.
"""
from datetime import date, timedelta

from app.services.weather.weather_provider import ForecastDay, WeatherProvider, WeatherReading, WeatherResult


class FakeWeatherProvider(WeatherProvider):
    def __init__(self, *, available: bool = True, current: WeatherReading | None = None, forecast: list[ForecastDay] | None = None):
        self._available = available
        self._current = current or WeatherReading(temperature_c=28.0, humidity_percent=60.0)
        self._forecast = forecast if forecast is not None else [
            ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=20.0)),
            ForecastDay(forecast_date=date.today() + timedelta(days=1), reading=WeatherReading(rain_probability_percent=30.0)),
        ]

    @property
    def provider_name(self) -> str:
        return "fake_test_provider"

    def get_weather(self, *, latitude: float, longitude: float, forecast_days: int) -> WeatherResult:
        if not self._available:
            return WeatherResult(available=False, provider_name=self.provider_name, unavailable_reason="fake provider marked unavailable")
        return WeatherResult(available=True, provider_name=self.provider_name, current=self._current, forecast=self._forecast)
