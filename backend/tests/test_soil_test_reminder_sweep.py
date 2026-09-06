"""
D20-13/D78-10 (docs/audit/FINAL_CANONICAL_group_D.md): soil test reminder
sweep - mirrors test_input_inventory.py's expiry-sweep test pattern
exactly (same "fires once per episode, never a hidden duplicate" contract).
"""
import uuid
from datetime import date, timedelta

from app.core.config import get_settings
from app.models.soil_test_result import SoilTestResult
from app.services.soil_testing_service import run_soil_test_reminder_sweep
from tests.conftest import auth_headers


def _create_plot_and_sample(client, tokens, **overrides):
    from tests.farm_factories import valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    payload = {"collection_date": "2026-06-01"}
    payload.update(overrides)
    sample = client.post(f"/api/v1/plots/{plot['id']}/soil-samples", json=payload, headers=headers).json()
    return plot, sample


def _create_result(client, tokens, sample_id, test_date: date):
    return client.post(
        f"/api/v1/soil-samples/{sample_id}/results", json={"test_date": test_date.isoformat()}, headers=auth_headers(tokens)
    ).json()


def test_reminder_sweep_alerts_once_for_a_stale_result_and_never_duplicates(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)
    settings = get_settings()
    stale_date = date.today() - timedelta(days=settings.soil_test_max_age_days + 30)
    result = _create_result(client, tokens, sample["id"], stale_date)

    run_soil_test_reminder_sweep(db_session, settings)
    stored = db_session.get(SoilTestResult, uuid.UUID(result["id"]))
    assert stored.reminder_alerted_at is not None

    run_soil_test_reminder_sweep(db_session, settings)  # must never duplicate

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    reminders = [n for n in notifications if n["category"] == "soil_test_reminder"]
    assert len(reminders) == 1


def test_reminder_sweep_ignores_a_recent_result(client, registered_farmer, db_session):
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)
    result = _create_result(client, tokens, sample["id"], date.today() - timedelta(days=30))

    settings = get_settings()
    run_soil_test_reminder_sweep(db_session, settings)

    stored = db_session.get(SoilTestResult, uuid.UUID(result["id"]))
    assert stored.reminder_alerted_at is None


def test_reminder_sweep_only_considers_a_plots_latest_result(client, registered_farmer, db_session):
    """An older, stale result is correctly ignored once a plot has a newer
    (non-stale) result - only the LATEST result per plot matters."""
    _, tokens = registered_farmer
    _, sample = _create_plot_and_sample(client, tokens)
    settings = get_settings()
    stale_date = date.today() - timedelta(days=settings.soil_test_max_age_days + 30)
    old_result = _create_result(client, tokens, sample["id"], stale_date)
    new_result = _create_result(client, tokens, sample["id"], date.today() - timedelta(days=10))

    run_soil_test_reminder_sweep(db_session, settings)

    stored_old = db_session.get(SoilTestResult, uuid.UUID(old_result["id"]))
    stored_new = db_session.get(SoilTestResult, uuid.UUID(new_result["id"]))
    assert stored_old.reminder_alerted_at is None, "the superseded old result must never be alerted on directly"
    assert stored_new.reminder_alerted_at is None, "the new result is not stale yet"
