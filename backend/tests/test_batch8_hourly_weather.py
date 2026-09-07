"""
Missing Backlog Batch 8 (group 6): D14-02 (docs/audit/FINAL_CANONICAL_group_A.md).
"""
from datetime import datetime, timedelta, timezone

from app.services.weather.open_meteo_provider import OpenMeteoProvider
from app.services.weather.weather_provider import HourlyForecastEntry, WeatherReading
from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider


def _static_open_meteo_response(hours: list[str]) -> dict:
    """The real, publicly documented Open-Meteo response shape - matches
    the module's own stated convention of testing _parse_response against
    a static fixture rather than a live call (network egress to
    api.open-meteo.com is blocked from this build/test environment, per
    open_meteo_provider.py's own docstring)."""
    return {
        "current": {
            "temperature_2m": 28.0,
            "relative_humidity_2m": 60.0,
            "apparent_temperature": 30.0,
            "precipitation": 0.0,
            "weather_code": 0,
            "wind_speed_10m": 10.0,
            "wind_direction_10m": 180.0,
        },
        "daily": {"time": []},
        "hourly": {
            "time": hours,
            "temperature_2m": [26.0 + i for i in range(len(hours))],
            "precipitation_probability": [10.0 * i for i in range(len(hours))],
            "precipitation": [0.0] * len(hours),
            "weather_code": [0] * len(hours),
            "wind_speed_10m": [5.0] * len(hours),
        },
    }


def test_parse_response_only_keeps_upcoming_hours():
    provider = OpenMeteoProvider(base_url="https://example.invalid", timeout_seconds=1.0)
    now = datetime.now(timezone.utc)
    past_hour = (now - timedelta(hours=1)).replace(microsecond=0).isoformat()
    future_hour_1 = (now + timedelta(hours=1)).replace(microsecond=0).isoformat()
    future_hour_2 = (now + timedelta(hours=2)).replace(microsecond=0).isoformat()

    result = provider._parse_response(_static_open_meteo_response([past_hour, future_hour_1, future_hour_2]))

    assert result.available is True
    assert len(result.hourly) == 2
    assert all(entry.timestamp >= now for entry in result.hourly)


def test_parse_response_caps_hourly_at_24_entries():
    provider = OpenMeteoProvider(base_url="https://example.invalid", timeout_seconds=1.0)
    now = datetime.now(timezone.utc)
    hours = [(now + timedelta(hours=i)).replace(microsecond=0).isoformat() for i in range(1, 73)]  # 72 upcoming hours

    result = provider._parse_response(_static_open_meteo_response(hours))

    assert len(result.hourly) == 24


def test_parse_response_hourly_reading_fields_match_the_real_documented_fields():
    provider = OpenMeteoProvider(base_url="https://example.invalid", timeout_seconds=1.0)
    now = datetime.now(timezone.utc)
    future_hour = (now + timedelta(hours=1)).replace(microsecond=0).isoformat()

    result = provider._parse_response(_static_open_meteo_response([future_hour]))

    entry = result.hourly[0]
    assert entry.reading.temperature_c == 26.0
    assert entry.reading.rain_probability_percent == 0.0
    assert entry.reading.condition_code == "0"


# --- End-to-end: FarmWeatherResponse.hourly ---

def test_farm_weather_response_includes_hourly_forecast(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    now = datetime.now(timezone.utc)
    hourly = [
        HourlyForecastEntry(timestamp=now + timedelta(hours=1), reading=WeatherReading(temperature_c=29.0, condition_code="95")),
        HourlyForecastEntry(timestamp=now + timedelta(hours=2), reading=WeatherReading(temperature_c=27.0)),
    ]
    with override_weather_provider(FakeWeatherProvider(hourly=hourly)):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    assert response.status_code == 200
    body = response.json()
    assert len(body["hourly"]) == 2
    assert body["hourly"][0]["reading"]["temperature_c"] == 29.0
    assert body["hourly"][0]["reading"]["is_storm"] is True


def test_farm_weather_response_hourly_defaults_to_empty_list(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    assert response.json()["hourly"] == []


def test_hourly_forecast_is_served_from_cache_on_second_request(client, farmer_with_located_farm):
    """The second call must not re-invoke the provider - proves caching,
    not just that the fake happens to return the same thing twice."""
    tokens, farm_id = farmer_with_located_farm
    now = datetime.now(timezone.utc)
    hourly = [HourlyForecastEntry(timestamp=now + timedelta(hours=1), reading=WeatherReading(temperature_c=31.0))]

    with override_weather_provider(FakeWeatherProvider(hourly=hourly)):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    # A DIFFERENT fake (different hourly data) - if the cache is used, the
    # second response still shows the FIRST fake's data.
    other_hourly = [HourlyForecastEntry(timestamp=now + timedelta(hours=1), reading=WeatherReading(temperature_c=99.0))]
    with override_weather_provider(FakeWeatherProvider(hourly=other_hourly)):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    assert response.json()["hourly"][0]["reading"]["temperature_c"] == 31.0
