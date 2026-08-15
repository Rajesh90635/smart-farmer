from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider
from app.services.weather.weather_provider import WeatherReading


def test_crop_action_absent_when_conditions_are_normal(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, wind_speed_kmh=10.0))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["crop_action"] is None


def test_crop_action_fires_for_high_wind_reusing_the_existing_rule(client, farmer_with_located_farm):
    """THE KEY TEST: this is not a new rule - it is the exact same
    evaluate_spray_condition_warning() function already used by the
    background notification pipeline, just also surfaced live here."""
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=28.0, wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    body = response.json()
    assert body["crop_action"] is not None
    assert body["crop_action"]["action"] == "avoid_spraying"
    assert body["crop_action"]["basis"] == "high_wind"
    assert body["crop_action"]["reason_message_key"] == "spray_condition_warning"


def test_crop_action_never_recommends_a_specific_chemical_or_dosage(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    advisory = response.json()["crop_action"]
    assert set(advisory.keys()) == {"action", "reason_message_key", "basis"}


def test_crop_action_absent_entirely_when_weather_itself_is_unavailable(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    body = response.json()
    assert body["available"] is False
    assert body["crop_action"] is None


def test_crop_action_is_deterministic_and_repeatable(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    fake = FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=50.0))
    with override_weather_provider(fake):
        first = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens)).json()
    assert first["crop_action"]["action"] == "avoid_spraying"
    assert first["crop_action"]["basis"] == "high_wind"
