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
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models.weather_snapshot import WeatherSnapshot, WeatherSnapshotType
from app.services.weather_alert_orchestration_service import run_proactive_weather_alert_sweep
from tests.conftest import auth_headers
from tests.weather_factories import calm_dry_provider, frost_risk_provider, heavy_rain_provider


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


def test_sweep_that_creates_a_notification_audit_logs_which_rule_and_version_fired(client, farmer_with_located_farm, db_session):
    """D89-07 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    tokens, farm_id = farmer_with_located_farm
    settings = get_settings()
    run_proactive_weather_alert_sweep(db_session, heavy_rain_provider(), settings, farm_ids=[uuid.UUID(farm_id)])

    entries = db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "RULE_EVALUATED", AuditLog.entity == "rule", AuditLog.entity_id == "weather_alert_rules:weather_alert_rules_v1"
        )
    ).scalars().all()
    assert len(entries) >= 1


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


def test_sweep_detects_frost_risk(client, farmer_with_located_farm, db_session):
    """D15-04 (docs/audit/FINAL_CANONICAL_group_A.md)."""
    tokens, farm_id = farmer_with_located_farm
    settings = get_settings()
    run_proactive_weather_alert_sweep(db_session, frost_risk_provider(), settings, farm_ids=[uuid.UUID(farm_id)])

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    categories = {n["category"] for n in notifications["items"]}
    assert "weather_alert" in categories
    frost = next(n for n in notifications["items"] if "frost" in n["body"].lower())
    assert frost is not None


def test_sweep_detects_flood_risk_from_cumulative_rainfall_history(client, farmer_with_located_farm, db_session):
    """D15-08/D75-01 (docs/audit/FINAL_CANONICAL_group_{A,D}.md): a
    single fetch's own rainfall_mm is 0 (calm_dry_provider) - the flood
    signal comes entirely from pre-seeded weather_snapshots history,
    proving the cumulative-window query itself, not just today's reading."""
    tokens, farm_id = farmer_with_located_farm
    settings = get_settings()
    now = datetime.now(timezone.utc)

    per_snapshot_mm = settings.weather_flood_risk_cumulative_rainfall_mm_threshold / 2
    for hours_ago in (2, 6):
        db_session.add(WeatherSnapshot(
            farm_id=uuid.UUID(farm_id), snapshot_type=WeatherSnapshotType.CURRENT, provider="test",
            rainfall_mm=per_snapshot_mm, fetched_at=now - timedelta(hours=hours_ago), expires_at=now + timedelta(hours=1),
        ))
    db_session.commit()

    run_proactive_weather_alert_sweep(db_session, calm_dry_provider(), settings, farm_ids=[uuid.UUID(farm_id)])

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    flood = [n for n in notifications["items"] if "flood" in n["body"].lower()]
    assert len(flood) == 1


def test_sweep_detects_drought_risk_from_consecutive_dry_days_history(client, farmer_with_located_farm, db_session):
    """D15-09/D17-05/D75-02 (docs/audit/FINAL_CANONICAL_group_{A,D}.md)."""
    tokens, farm_id = farmer_with_located_farm
    settings = get_settings()
    now = datetime.now(timezone.utc)

    for days_ago in range(1, settings.weather_drought_risk_consecutive_dry_days_threshold + 1):
        db_session.add(WeatherSnapshot(
            farm_id=uuid.UUID(farm_id), snapshot_type=WeatherSnapshotType.CURRENT, provider="test",
            rainfall_mm=0.0, fetched_at=now - timedelta(days=days_ago), expires_at=now + timedelta(hours=1),
        ))
    db_session.commit()

    run_proactive_weather_alert_sweep(db_session, calm_dry_provider(), settings, farm_ids=[uuid.UUID(farm_id)])

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    drought = [n for n in notifications["items"] if "drought" in n["body"].lower()]
    assert len(drought) == 1


def test_sweep_does_not_flag_drought_with_too_few_dry_days(client, farmer_with_located_farm, db_session):
    tokens, farm_id = farmer_with_located_farm
    settings = get_settings()
    now = datetime.now(timezone.utc)

    for days_ago in range(1, settings.weather_drought_risk_consecutive_dry_days_threshold - 1):
        db_session.add(WeatherSnapshot(
            farm_id=uuid.UUID(farm_id), snapshot_type=WeatherSnapshotType.CURRENT, provider="test",
            rainfall_mm=0.0, fetched_at=now - timedelta(days=days_ago), expires_at=now + timedelta(hours=1),
        ))
    db_session.commit()

    run_proactive_weather_alert_sweep(db_session, calm_dry_provider(), settings, farm_ids=[uuid.UUID(farm_id)])

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()
    drought = [n for n in notifications["items"] if "drought" in n["body"].lower()]
    assert len(drought) == 0


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
