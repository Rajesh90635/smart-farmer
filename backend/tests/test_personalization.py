import uuid

from tests.conftest import auth_headers


def _submit_feedback(client, tokens, crop_cycle_id, source_type="crop_assistant", feedback_type="helpful"):
    return client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/advisory-feedback",
        json={"source_type": source_type, "feedback_type": feedback_type},
        headers=auth_headers(tokens),
    )


def _create_second_crop_cycle(client, tokens, sample_crop_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    return cycle["id"]


# --- Personalization Profile ---

def test_no_history_produces_insufficient_data_for_all_signals(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    treatment_signal = next(p for p in body["preferences"] if p["signal_name"] == "treatment_follow_up_consistency")
    assert treatment_signal["confidence"] is None
    assert treatment_signal["observation"] is None
    assert treatment_signal["evidence_count"] == 0


def test_one_treatment_does_not_create_a_strong_permanent_preference(client, farmer_with_crop_cycle):
    """A single historical event must never become a stated preference -
    the minimum evidence floor of 3 must be enforced."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens))

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    body = response.json()
    treatment_signal = next(p for p in body["preferences"] if p["signal_name"] == "treatment_follow_up_consistency")
    assert treatment_signal["confidence"] is None
    assert treatment_signal["evidence_count"] == 1


def test_multiple_consistent_treatment_follow_ups_strengthen_the_preference(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    for i in range(4):
        treatment = client.post(
            f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens)
        ).json()
        client.post(
            f"/api/v1/treatments/{treatment['id']}/follow-ups",
            json={"observation_date": "2026-01-10"},
            headers=auth_headers(tokens),
        )

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    body = response.json()
    treatment_signal = next(p for p in body["preferences"] if p["signal_name"] == "treatment_follow_up_consistency")
    assert treatment_signal["evidence_count"] == 4
    assert treatment_signal["confidence"] == "low"  # 4 falls in the 3-6 range
    assert "consistently" in treatment_signal["observation"]


def test_cost_pattern_signal_needs_at_least_three_cycles_with_recorded_cost(client, farmer_with_crop_cycle):
    """D98-03 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "100.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    body = response.json()
    cost_signal = next(p for p in body["preferences"] if p["signal_name"] == "cost_pattern")
    assert cost_signal["confidence"] is None
    assert cost_signal["evidence_count"] == 1


def test_cost_pattern_signal_reports_a_trend_once_enough_cycles_have_recorded_cost(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)
    crop_cycle_id_3 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    for cycle_id, amount in ((crop_cycle_id_1, "100.00"), (crop_cycle_id_2, "100.00"), (crop_cycle_id_3, "100.00")):
        client.post(
            f"/api/v1/crop-cycles/{cycle_id}/ledger/entries",
            json={"entry_type": "expense", "category": "seed", "amount": amount, "entry_date": "2026-01-01"},
            headers=auth_headers(tokens),
        )

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    body = response.json()
    cost_signal = next(p for p in body["preferences"] if p["signal_name"] == "cost_pattern")
    assert cost_signal["evidence_count"] == 3
    assert cost_signal["confidence"] == "low"
    assert "stable" in cost_signal["observation"]


def test_disease_pattern_signal_needs_at_least_three_analyses(client, farmer_with_crop_cycle):
    """D98-04 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    from tests.test_crop_performance import _upload_and_analyze
    from app.services.ai.model_provider import TopKPrediction

    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Healthy", 0.95)])

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    disease_signal = next(p for p in response.json()["preferences"] if p["signal_name"] == "disease_pattern")
    assert disease_signal["confidence"] is None
    assert disease_signal["evidence_count"] == 1


def test_disease_pattern_signal_reports_a_pattern_once_enough_analyses_exist(client, farmer_with_crop_cycle):
    from tests.test_crop_performance import _upload_and_analyze
    from app.services.ai.model_provider import TopKPrediction

    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.90)])
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Healthy", 0.95)])
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Healthy", 0.95)])

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    disease_signal = next(p for p in response.json()["preferences"] if p["signal_name"] == "disease_pattern")
    assert disease_signal["evidence_count"] == 3
    assert disease_signal["confidence"] == "low"
    assert "occasionally" in disease_signal["observation"]


def test_weather_impact_signal_needs_at_least_three_alerts(client, farmer_with_located_farm):
    """D98-05 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    from tests.conftest import override_weather_provider
    from tests.weather_factories import heavy_rain_provider

    tokens, farm_id = farmer_with_located_farm
    with override_weather_provider(heavy_rain_provider()):
        client.get(f"/api/v1/farms/{farm_id}/weather", headers=auth_headers(tokens))

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    weather_signal = next(p for p in response.json()["preferences"] if p["signal_name"] == "weather_impact")
    assert weather_signal["confidence"] is None
    assert weather_signal["evidence_count"] == 1


def test_weather_impact_signal_reports_a_pattern_once_enough_alerts_exist(client, farmer_with_located_farm, db_session):
    """D98-05: real notification rows (a farmer genuinely can't generate
    3 distinct dated weather alerts in one test run - the pipeline dedups
    by calendar day) inserted directly, same as this project's other
    tests that simulate a future/batch write path."""
    import uuid as uuid_mod
    from datetime import datetime, timezone

    from app.core.jwt import decode_access_token
    from app.models.notification import Notification, NotificationCategory, NotificationPriority

    tokens, farm_id = farmer_with_located_farm
    farmer_id = uuid_mod.UUID(decode_access_token(tokens["access_token"])["sub"])

    for i in range(3):
        db_session.add(Notification(
            farmer_id=farmer_id, category=NotificationCategory.HEAVY_RAIN_ALERT, priority=NotificationPriority.HIGH,
            title="Heavy Rain Warning", body="test", language_code="en", dedup_key=f"heavy_rain_alert:test:{i}",
        ))
    db_session.commit()

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    weather_signal = next(p for p in response.json()["preferences"] if p["signal_name"] == "weather_impact")
    assert weather_signal["evidence_count"] == 3
    assert weather_signal["confidence"] == "low"
    assert "frequently" in weather_signal["observation"]


def test_personalization_evidence_count_reflects_real_task_data(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    for i in range(5):
        task = client.post(
            f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
            json={"task_type": "general", "title": f"Task {i}", "due_date": "2026-01-01"},
            headers=auth_headers(tokens),
        ).json()
        client.post(f"/api/v1/tasks/{task['id']}/complete", headers=auth_headers(tokens))

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    body = response.json()
    task_signal = next(p for p in body["preferences"] if p["signal_name"] == "task_completion_consistency")
    assert task_signal["evidence_count"] == 5
    assert task_signal["confidence"] == "low"


def test_personalization_is_deterministic(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    first = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens)).json()
    second = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens)).json()
    assert first == second


def test_personalization_never_leaks_another_farmers_history(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    for i in range(4):
        client.post(
            f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
            json={"task_type": "general", "title": f"Task {i}", "due_date": "2026-01-01"},
            headers=auth_headers(tokens),
        )

    response_b = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens_b))
    body_b = response_b.json()
    task_signal_b = next(p for p in body_b["preferences"] if p["signal_name"] == "task_completion_consistency")
    assert task_signal_b["evidence_count"] == 0


def test_unauthenticated_personalization_request_is_rejected(client, farmer_with_crop_cycle):
    response = client.get("/api/v1/farmers/me/personalization")
    assert response.status_code == 401


# --- Advisory Feedback ---

def test_submit_feedback_and_retrieve_it(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _submit_feedback(client, tokens, crop_cycle_id)
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "crop_assistant"
    assert body["feedback_type"] == "helpful"


def test_cannot_submit_feedback_against_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = _submit_feedback(client, tokens_b, crop_cycle_id)
    assert response.status_code == 404


def test_feedback_ratio_reflects_real_submitted_feedback(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _submit_feedback(client, tokens, crop_cycle_id, feedback_type="helpful")
    _submit_feedback(client, tokens, crop_cycle_id, feedback_type="helpful")
    _submit_feedback(client, tokens, crop_cycle_id, feedback_type="not_helpful")

    response = client.get("/api/v1/farmers/me/personalization", headers=auth_headers(tokens))
    body = response.json()
    feedback_signal = next(p for p in body["preferences"] if p["signal_name"] == "advisory_feedback_ratio")
    assert feedback_signal["evidence_count"] == 3
    assert "2 of 3" in feedback_signal["explanation"]


def test_invalid_crop_cycle_for_feedback_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = _submit_feedback(client, tokens, uuid.uuid4())
    assert response.status_code == 404


def test_unauthenticated_feedback_submission_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/advisory-feedback", json={"source_type": "crop_assistant", "feedback_type": "helpful"})
    assert response.status_code == 401


# --- Learning Summary (ML Foundation) ---

def test_learning_summary_always_discloses_ml_not_yet_justified(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["ml_training_justified"] is False
    assert "not yet justified" in body["ml_readiness_note"]


def test_learning_summary_has_no_outcome_label_for_an_in_progress_crop(client, farmer_with_crop_cycle):
    """Temporal leakage prevention: an in-progress crop cycle must never
    have an outcome_label, since the outcome hasn't happened yet."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=auth_headers(tokens))
    body = response.json()
    assert body["feature_snapshot"]["outcome_label"] is None
    assert body["feature_snapshot"]["outcome_known_only_after"] is None


def test_learning_summary_feature_snapshot_has_a_real_version_and_timestamp(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=auth_headers(tokens))
    body = response.json()
    assert body["feature_snapshot"]["feature_version"]
    assert body["feature_snapshot"]["extracted_at"]
    assert body["feature_snapshot"]["crop_cycle_id"] == crop_cycle_id


def test_learning_summary_is_deterministic_in_structure(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    first = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=auth_headers(tokens)).json()
    second = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=auth_headers(tokens)).json()
    assert first["feature_snapshot"]["available_at_time"] == second["feature_snapshot"]["available_at_time"]
    assert first["ml_training_justified"] == second["ml_training_justified"]


def test_cannot_access_another_farmers_learning_summary(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_invalid_crop_cycle_returns_404_for_learning_summary(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{uuid.uuid4()}/learning-summary", headers=auth_headers(tokens))
    assert response.status_code == 404


def test_unauthenticated_learning_summary_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary")
    assert response.status_code == 401


def test_learning_summary_never_leaks_across_crop_cycles(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_1}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )

    summary_1 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/learning-summary", headers=auth_headers(tokens)).json()
    summary_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/learning-summary", headers=auth_headers(tokens)).json()
    assert summary_1["feature_snapshot"]["available_at_time"]["actual_cost_so_far"] == "500.00"
    assert summary_2["feature_snapshot"]["available_at_time"]["actual_cost_so_far"] == "0"
