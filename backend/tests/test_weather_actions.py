import uuid
from datetime import date

from tests.conftest import auth_headers, override_weather_provider
from tests.fake_weather_provider import FakeWeatherProvider
from app.services.weather.weather_provider import ForecastDay, WeatherReading


def _get_actions(client, tokens, crop_cycle_id):
    return client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/weather-actions", headers=auth_headers(tokens))


def _assessment(body, action_type):
    return next(a for a in body["assessments"] if a["action_type"] == action_type)


def test_safe_spray_conditions_produce_safe_status(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=10, rain_probability_percent=5))):
        response = _get_actions(client, tokens, crop_cycle_id)
    assert response.status_code == 200
    body = response.json()
    spray = _assessment(body, "spray")
    assert spray["status"] == "safe"
    assert spray["is_deterministic"] is True


def test_high_wind_produces_unsafe_spray_status(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=55, rain_probability_percent=5))):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert _assessment(body, "spray")["status"] == "unsafe"


def test_missing_wind_data_produces_caution_not_safe(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=None, rain_probability_percent=5))):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert _assessment(body, "spray")["status"] == "caution"


def test_missing_all_spray_data_produces_unknown(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    empty_forecast = [ForecastDay(forecast_date=date.today(), reading=WeatherReading())]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=None, rain_probability_percent=None), forecast=empty_forecast)):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert _assessment(body, "spray")["status"] == "unknown"


def test_weather_completely_unavailable_produces_unknown_for_all_actions(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["weather_available"] is False
    assert all(a["status"] == "unknown" for a in body["assessments"])
    assert len(body["data_completeness_notes"]) > 0


def test_heavy_rain_produces_unsafe_irrigation_and_harvest(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    todays_forecast = [ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=85))]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=10), forecast=todays_forecast)):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert _assessment(body, "irrigation")["status"] == "unsafe"
    assert _assessment(body, "harvest")["status"] == "unsafe"


def test_no_forecast_data_produces_no_recommended_window(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=50, rain_probability_percent=5), forecast=[])):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["recommended_spray_window"] is None
    assert any("forecast" in note.lower() for note in body["data_completeness_notes"])


def test_forecast_with_a_safe_day_produces_a_recommended_window(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    forecast = [
        ForecastDay(forecast_date=date(2026, 6, 2), reading=WeatherReading(wind_speed_kmh=60, rain_probability_percent=10)),
        ForecastDay(forecast_date=date(2026, 6, 3), reading=WeatherReading(wind_speed_kmh=15, rain_probability_percent=5)),
    ]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=60, rain_probability_percent=10), forecast=forecast)):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["recommended_spray_window"] is not None
    assert body["recommended_spray_window"]["forecast_date"] == "2026-06-03"


def test_forecast_with_no_safe_day_reports_no_suitable_window(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    forecast = [ForecastDay(forecast_date=date(2026, 6, 2), reading=WeatherReading(wind_speed_kmh=60, rain_probability_percent=90))]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=60, rain_probability_percent=90), forecast=forecast)):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["recommended_spray_window"] is None
    assert any("no suitable" in note.lower() for note in body["data_completeness_notes"])


def test_stale_weather_is_flagged_in_notes(client, farmer_with_crop_cycle, db_session):
    """Staleness is triggered by the REAL fallback path in
    weather_service.py: an expired cached snapshot is returned when the
    live provider is unavailable - reproduced exactly, not assumed."""
    from datetime import datetime, timedelta, timezone

    from app.models.weather_snapshot import WeatherSnapshot

    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=10, rain_probability_percent=5))):
        first = _get_actions(client, tokens, crop_cycle_id)
    assert first.json()["is_stale"] is False

    # Genuinely expire the cached snapshot rather than assuming a hook exists.
    db_session.query(WeatherSnapshot).update({WeatherSnapshot.expires_at: datetime.now(timezone.utc) - timedelta(hours=1)})
    db_session.commit()

    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["is_stale"] is True
    assert any("out of date" in note.lower() or "not current" in note.lower() for note in body["data_completeness_notes"])


def test_pending_spray_task_is_cross_referenced(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    task = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"task_type": "spraying", "title": "Spray fungicide", "due_date": "2026-06-01"},
        headers=auth_headers(tokens),
    ).json()

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=10, rain_probability_percent=5))):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["relevant_pending_spray_task_id"] == task["id"]


def test_no_pending_spray_task_leaves_reference_null(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=10, rain_probability_percent=5))):
        response = _get_actions(client, tokens, crop_cycle_id)
    body = response.json()
    assert body["relevant_pending_spray_task_id"] is None


def test_assessment_is_deterministic_for_the_same_weather_data(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=45, rain_probability_percent=50))):
        first = _get_actions(client, tokens, crop_cycle_id).json()
        second = _get_actions(client, tokens, crop_cycle_id).json()
    assert first["assessments"] == second["assessments"]


def test_cannot_access_another_farmers_weather_actions(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    with override_weather_provider(FakeWeatherProvider()):
        response = _get_actions(client, tokens_b, crop_cycle_id)
    assert response.status_code == 404


def test_context_never_leaks_across_crop_cycles(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_1}/tasks",
        json={"task_type": "spraying", "title": "Spray fungicide", "due_date": "2026-06-01"},
        headers=headers,
    )

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=10, rain_probability_percent=5))):
        response_2 = _get_actions(client, tokens, crop_cycle_id_2)
    body_2 = response_2.json()
    assert body_2["relevant_pending_spray_task_id"] is None


def test_invalid_crop_cycle_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider()):
        response = _get_actions(client, tokens, uuid.uuid4())
    assert response.status_code == 404


def test_unauthenticated_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/weather-actions")
    assert response.status_code == 401
