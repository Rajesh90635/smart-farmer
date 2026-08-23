"""
OpenMeteoProvider: real implementation against Open-Meteo's public,
documented, free forecast API (https://open-meteo.com) - no API key
required, generous free-tier limits, CC-BY-4.0 licensed data (attribution
required - see docs/WEATHER_ARCHITECTURE.md).

IMPORTANT HONESTY NOTE: this class was written against Open-Meteo's real,
documented response schema (the exact field names below match the public
API docs), but **could not be exercised against the live API from the
build/test environment** - the sandbox's network egress allowlist returns
403 for api.open-meteo.com (verified directly: `curl` to the real endpoint
returned HTTP 403 from the egress proxy, not from Open-Meteo). The parsing
logic (`_parse_response`) IS tested against a static fixture that matches
the real documented response shape - see
tests/test_weather_provider.py - but the actual HTTP round-trip against
the live service has not been verified. Verify on a machine with normal
internet access before relying on this in a real deployment.
"""
from datetime import date, datetime, timezone

import httpx

from app.services.weather.weather_provider import ForecastDay, WeatherProvider, WeatherReading, WeatherResult


class OpenMeteoProvider(WeatherProvider):
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url
        self._timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "open_meteo"

    def get_weather(self, *, latitude: float, longitude: float, forecast_days: int) -> WeatherResult:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,weather_code,sunrise,sunset,wind_speed_10m_max",
            "timezone": "auto",
            "forecast_days": forecast_days,
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(self._base_url, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return WeatherResult(
                available=False,
                provider_name=self.provider_name,
                unavailable_reason=f"Weather provider request failed: {exc.__class__.__name__}",
            )

        return self._parse_response(data)

    def _parse_response(self, data: dict) -> WeatherResult:
        current_raw = data.get("current") or {}
        current = WeatherReading(
            temperature_c=current_raw.get("temperature_2m"),
            feels_like_c=current_raw.get("apparent_temperature"),
            humidity_percent=current_raw.get("relative_humidity_2m"),
            rainfall_mm=current_raw.get("precipitation"),
            wind_speed_kmh=current_raw.get("wind_speed_10m"),
            wind_direction_degrees=current_raw.get("wind_direction_10m"),
            condition_code=str(current_raw.get("weather_code")) if current_raw.get("weather_code") is not None else None,
        )

        daily_raw = data.get("daily") or {}
        forecast: list[ForecastDay] = []
        dates = daily_raw.get("time") or []
        for i, date_str in enumerate(dates):
            reading = WeatherReading(
                temperature_min_c=_at(daily_raw.get("temperature_2m_min"), i),
                temperature_max_c=_at(daily_raw.get("temperature_2m_max"), i),
                rain_probability_percent=_at(daily_raw.get("precipitation_probability_max"), i),
                rainfall_mm=_at(daily_raw.get("precipitation_sum"), i),
                wind_speed_kmh=_at(daily_raw.get("wind_speed_10m_max"), i),
                condition_code=_str_at(daily_raw.get("weather_code"), i),
                sunrise=_parse_iso(_str_at(daily_raw.get("sunrise"), i)),
                sunset=_parse_iso(_str_at(daily_raw.get("sunset"), i)),
            )
            forecast.append(ForecastDay(forecast_date=date.fromisoformat(date_str), reading=reading))

        return WeatherResult(available=True, provider_name=self.provider_name, current=current, forecast=forecast)


def _at(values: list | None, index: int):
    if values is None or index >= len(values):
        return None
    return values[index]


def _str_at(values: list | None, index: int) -> str | None:
    v = _at(values, index)
    return str(v) if v is not None else None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
