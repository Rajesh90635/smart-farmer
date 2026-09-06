"""D89-01/D89-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from app.services import crop_risk_service, weather_action_rules, weather_alert_rules


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
