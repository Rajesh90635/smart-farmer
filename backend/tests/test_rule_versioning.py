"""D89-01/D89-02/D89-03 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from datetime import datetime, timedelta, timezone

from app.services import crop_risk_service, rule_version_service, weather_action_rules, weather_alert_rules


def test_every_rule_module_exposes_a_non_empty_rule_id():
    assert weather_action_rules.RULE_ID
    assert weather_alert_rules.RULE_ID
    assert crop_risk_service.RULE_ID


def test_rule_ids_are_distinct_per_module():
    ids = {weather_action_rules.RULE_ID, weather_alert_rules.RULE_ID, crop_risk_service.RULE_ID}
    assert len(ids) == 3


def test_every_rule_module_also_exposes_a_non_empty_rule_version():
    """D89-02: verifies the rule_version rollout (D88-07) is complete
    across every rule module, not just the two it originally covered."""
    assert weather_action_rules.RULE_VERSION
    assert weather_alert_rules.RULE_VERSION
    assert crop_risk_service.RULE_VERSION


# --- D89-03: effective-date scoping ---

def test_recording_the_same_thresholds_twice_does_not_create_a_second_snapshot(db_session):
    rule_id = "test_rule_no_change"
    first = rule_version_service.record_snapshot_if_changed(db_session, rule_id, "v1", {"threshold": 40.0})
    second = rule_version_service.record_snapshot_if_changed(db_session, rule_id, "v1", {"threshold": 40.0})
    assert first.id == second.id


def test_recording_a_changed_threshold_closes_the_old_snapshot_and_opens_a_new_one(db_session):
    rule_id = "test_rule_changed"
    old = rule_version_service.record_snapshot_if_changed(db_session, rule_id, "v1", {"threshold": 40.0})
    new = rule_version_service.record_snapshot_if_changed(db_session, rule_id, "v1", {"threshold": 55.0})

    assert new.id != old.id
    db_session.refresh(old)
    assert old.effective_to is not None
    assert new.effective_to is None


def test_a_query_for_an_old_date_still_reproduces_the_old_decision_after_a_threshold_change(db_session):
    """The exact scenario the audit row asks for: change a threshold, then
    assert a query for an old date still reproduces the old value - never
    silently rewritten by a later change. Backdates the first snapshot's
    effective_from directly (same technique test_weather.py uses to force
    a deterministic time window) rather than relying on real wall-clock
    gaps between two fast, back-to-back calls."""
    rule_id = "test_rule_reproducibility"
    long_ago = datetime(2020, 1, 1, tzinfo=timezone.utc)

    old = rule_version_service.record_snapshot_if_changed(db_session, rule_id, "v1", {"threshold": 40.0})
    old.effective_from = long_ago
    db_session.commit()

    new = rule_version_service.record_snapshot_if_changed(db_session, rule_id, "v1", {"threshold": 70.0})

    old_snapshot = rule_version_service.get_thresholds_effective_at(db_session, rule_id, long_ago + timedelta(days=1))
    assert old_snapshot.id == old.id
    assert old_snapshot.threshold_values == {"threshold": 40.0}

    current_snapshot = rule_version_service.get_thresholds_effective_at(db_session, rule_id, datetime.now(timezone.utc))
    assert current_snapshot.id == new.id
    assert current_snapshot.threshold_values == {"threshold": 70.0}


def test_lookup_for_a_date_before_any_snapshot_existed_returns_none(db_session):
    rule_id = "test_rule_no_history_yet"
    long_ago = datetime.now(timezone.utc) - timedelta(days=3650)
    assert rule_version_service.get_thresholds_effective_at(db_session, rule_id, long_ago) is None


def test_fetching_weather_records_a_current_snapshot_for_weather_alert_rules(client, farmer_with_located_farm, db_session):
    """Integration: a real weather fetch (which evaluates weather_alert_rules
    against live Settings) actually records/keeps-current a snapshot -
    not just directly-called unit tests."""
    from tests.conftest import auth_headers, override_weather_provider
    from tests.fake_weather_provider import FakeWeatherProvider

    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))
    assert response.status_code == 200

    snapshot = rule_version_service.get_thresholds_effective_at(db_session, weather_alert_rules.RULE_ID, datetime.now(timezone.utc))
    assert snapshot is not None
    assert snapshot.version == weather_alert_rules.RULE_VERSION
    assert snapshot.threshold_values["weather_rain_probability_threshold"] is not None
