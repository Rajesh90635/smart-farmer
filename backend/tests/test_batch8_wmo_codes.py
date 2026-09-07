"""
Missing Backlog Batch 8 (group 3): D15-05 (storm), D15-07 (hail)
(docs/audit/FINAL_CANONICAL_group_A.md). D15-06 (cyclone) is deliberately
NOT attempted - see app/services/weather/wmo_codes.py's own docstring.
"""
from app.services.weather.weather_provider import WeatherReading
from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider


def test_condition_code_none_yields_no_storm_or_hail_classification(client, farmer_with_located_farm):
    """Honestly None (unavailable), never fabricated False."""
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, condition_code=None))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    current = response.json()["current"]
    assert current["is_storm"] is None
    assert current["is_hail"] is None


def test_clear_sky_code_is_not_a_storm_or_hail(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, condition_code="0"))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    current = response.json()["current"]
    assert current["is_storm"] is False
    assert current["is_hail"] is False


def test_thunderstorm_code_95_is_a_storm_but_not_hail(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, condition_code="95"))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    current = response.json()["current"]
    assert current["is_storm"] is True
    assert current["is_hail"] is False


def test_thunderstorm_with_slight_hail_code_96_is_both_storm_and_hail(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, condition_code="96"))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    current = response.json()["current"]
    assert current["is_storm"] is True
    assert current["is_hail"] is True


def test_thunderstorm_with_heavy_hail_code_99_is_both_storm_and_hail(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, condition_code="99"))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    current = response.json()["current"]
    assert current["is_storm"] is True
    assert current["is_hail"] is True


def test_ordinary_rain_code_is_not_a_storm(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, condition_code="61"))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    current = response.json()["current"]
    assert current["is_storm"] is False
    assert current["is_hail"] is False


def test_forecast_days_are_also_classified(client, farmer_with_located_farm):
    from datetime import date

    from app.services.weather.weather_provider import ForecastDay

    tokens, farm_id = farmer_with_located_farm
    forecast = [ForecastDay(forecast_date=date.today(), reading=WeatherReading(condition_code="99"))]
    with override_weather_provider(FakeWeatherProvider(forecast=forecast)):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    assert response.json()["forecast"][0]["reading"]["is_hail"] is True
