"""
FastAPI dependency providing the configured WeatherProvider. Exactly one
switch point: `Settings.weather_provider`. Swapping providers (or adding a
second free option later) means adding one branch here - no endpoint or
service code changes.
"""
from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.weather.not_configured_provider import NotConfiguredWeatherProvider
from app.services.weather.open_meteo_provider import OpenMeteoProvider
from app.services.weather.weather_provider import WeatherProvider


@lru_cache
def get_weather_provider() -> WeatherProvider:
    settings: Settings = get_settings()
    if settings.weather_provider == "open_meteo":
        return OpenMeteoProvider(base_url=settings.weather_api_base_url, timeout_seconds=settings.weather_request_timeout_seconds)
    return NotConfiguredWeatherProvider()
