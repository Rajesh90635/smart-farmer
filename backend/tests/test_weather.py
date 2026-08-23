from datetime import date

from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider


def test_get_weather_with_fake_provider(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["provider"] == "fake_test_provider"
    assert body["current"]["temperature_c"] == 28.0
    assert len(body["forecast"]) == 2


def test_weather_is_cached_on_second_request(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    fake = FakeWeatherProvider()
    with override_weather_provider(fake):
        first = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens)).json()
        # Change the fake provider's data - if caching works, the second
        # call should still return the FIRST fetch's data, not a live one.
        fake._current = fake._current.__class__(temperature_c=99.0)
        second = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens)).json()
    assert second["current"]["temperature_c"] == first["current"]["temperature_c"]
    assert second["current"]["temperature_c"] == 28.0


def test_weather_provider_failure_returns_honest_unavailable(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["unavailable_reason"]


def test_weather_falls_back_to_stale_cache_when_provider_fails(client, farmer_with_located_farm):
    tokens, farm_id = farmer_with_located_farm

    # First call succeeds and caches data.
    with override_weather_provider(FakeWeatherProvider()):
        first = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens)).json()
    assert first["available"] is True

    # Force the cache to be treated as stale by manually expiring it, then
    # simulate a provider failure - should fall back to the stale cache
    # rather than showing nothing.
    import uuid as uuid_mod
    from datetime import datetime, timedelta, timezone

    from app.db.session import SessionLocal
    from app.models.weather_snapshot import WeatherSnapshot

    db = SessionLocal()
    snapshots = db.query(WeatherSnapshot).filter(WeatherSnapshot.farm_id == uuid_mod.UUID(farm_id)).all()
    for s in snapshots:
        s.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    db.close()

    with override_weather_provider(FakeWeatherProvider(available=False)):
        second = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens)).json()
    assert second["available"] is True
    assert second["is_stale"] is True


def test_farm_without_location_returns_validation_error(client, registered_farmer):
    from tests.farm_factories import valid_farm_payload

    _, tokens = registered_farmer
    farm = client.post(
        "/api/v1/farms", json=valid_farm_payload(latitude=None, longitude=None), headers=auth_headers(tokens)
    ).json()

    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/farms/{farm['id']}/weather", headers=auth_headers(tokens))
    assert response.status_code == 422


def test_farmer_a_cannot_get_farmer_bs_farm_weather(client, farmer_with_located_farm, another_farmer):
    _, farm_id = farmer_with_located_farm
    _, tokens_b = another_farmer

    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_unauthenticated_weather_request_is_rejected(client, farmer_with_located_farm):
    _, farm_id = farmer_with_located_farm
    response = client.get(f"/api/v1/farms/{farm_id}/weather")
    assert response.status_code == 401
