"""
D16-10 (docs/audit/c03_weather_water_soil.md): the proactive weather
alert sweep - a farm with dangerous weather must be checked even if the
farmer never opens the weather screen. Runs on the background scheduler
in production (disabled in `testing`, see scheduler.py) - tests call
`run_proactive_weather_alert_sweep` directly, exactly like the scheduler's
own job function does.

Every test passes `farm_ids=[...]` scoped to just the farm it created -
the shared test database accumulates farms across the whole session
(tens of thousands by now), so an unscoped sweep here would iterate all
of them and take unreasonably long for a unit test. The real scheduled
job (scheduler.py) omits `farm_ids` and sweeps every eligible farm.
"""
import uuid

from app.core.config import get_settings
from app.services.weather_alert_orchestration_service import run_proactive_weather_alert_sweep
from tests.conftest import auth_headers
from tests.weather_factories import heavy_rain_provider


def test_sweep_creates_a_notification_without_any_farmer_request(client, farmer_with_located_farm, db_session):
    tokens, farm_id = farmer_with_located_farm

    settings = get_settings()
    created = run_proactive_weather_alert_sweep(db_session, heavy_rain_provider(), settings, farm_ids=[uuid.UUID(farm_id)])
    assert created >= 1

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    categories = {n["category"] for n in notifications["items"]}
    assert "heavy_rain_alert" in categories

    # D89-01/02/07 (docs/FINAL_GAP_REPORT.md): every weather-alert-rule
    # notification records which rule version produced it.
    heavy_rain = next(n for n in notifications["items"] if n["category"] == "heavy_rain_alert")
    assert heavy_rain["rule_version"] == "weather_alert_rules_v1"


def test_sweep_never_duplicates_across_repeated_ticks(client, farmer_with_located_farm, db_session):
    tokens, farm_id = farmer_with_located_farm
    settings = get_settings()
    farm_ids = [uuid.UUID(farm_id)]

    run_proactive_weather_alert_sweep(db_session, heavy_rain_provider(), settings, farm_ids=farm_ids)
    run_proactive_weather_alert_sweep(db_session, heavy_rain_provider(), settings, farm_ids=farm_ids)
    run_proactive_weather_alert_sweep(db_session, heavy_rain_provider(), settings, farm_ids=farm_ids)

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    heavy_rain_notifications = [n for n in notifications["items"] if n["category"] == "heavy_rain_alert"]
    assert len(heavy_rain_notifications) == 1


def test_sweep_skips_a_farm_with_no_location(client, registered_farmer, db_session):
    from tests.farm_factories import valid_farm_payload

    _, tokens = registered_farmer
    farm = client.post(
        "/api/v1/farms", json={**valid_farm_payload(), "latitude": None, "longitude": None}, headers=auth_headers(tokens)
    ).json()

    settings = get_settings()
    created = run_proactive_weather_alert_sweep(
        db_session, heavy_rain_provider(), settings, farm_ids=[uuid.UUID(farm["id"])]
    )
    assert created == 0
