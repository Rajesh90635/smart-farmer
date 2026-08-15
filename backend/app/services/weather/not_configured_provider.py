"""
NotConfiguredWeatherProvider: returned when Settings.weather_provider is
"none" or otherwise unresolved. Per Requirement 51's absolute rule, never
returns fabricated weather - always available=False.
"""
from app.services.weather.weather_provider import WeatherProvider, WeatherResult


class NotConfiguredWeatherProvider(WeatherProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    def get_weather(self, *, latitude: float, longitude: float, forecast_days: int) -> WeatherResult:
        return WeatherResult(
            available=False,
            provider_name="none",
            unavailable_reason="No weather provider is configured in this environment.",
        )
