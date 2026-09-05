import uuid

from tests.conftest import auth_headers, override_model_provider, override_weather_provider
from tests.fake_model_provider import FakeModelProvider
from tests.fake_weather_provider import FakeWeatherProvider
from tests.professional_factories import valid_case_payload
from app.services.ai.model_provider import TopKPrediction
from app.services.weather.weather_provider import WeatherReading


def _upload_and_analyze(client, tokens, crop_cycle_id, top_predictions):
    import io

    from tests.photo_factories import make_test_jpeg, valid_photo_session_payload

    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()

    with override_model_provider(FakeModelProvider(top_predictions=top_predictions)):
        return client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens)).json()


def test_no_data_at_all_returns_insufficient_data_not_fabricated_low(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["overall_risk"] == "insufficient_data"
    assert all(f["value"] == "unknown" for f in body["factors"])
    treatment_factor = next(f for f in body["factors"] if f["factor_name"] == "Treatment Response")
    assert treatment_factor["value"] == "unknown"
    # D88-07: the rule version that produced this score must always be present.
    assert body["rule_version"] == "crop_risk_v1"


def test_disease_detected_analysis_produces_high_risk_factor(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])

    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    disease_factor = next(f for f in body["factors"] if f["factor_name"] == "Recent Disease Detection")
    assert disease_factor["value"] == "high"
    assert disease_factor["source"] == "AI crop photo analysis"
    assert body["overall_risk"] == "high"
    assert body["recommendation"] is not None


def test_healthy_analysis_produces_low_risk_factor(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])

    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    disease_factor = next(f for f in body["factors"] if f["factor_name"] == "Recent Disease Detection")
    assert disease_factor["value"] == "low"


def test_disease_recurrence_high_after_three_detections(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    for _ in range(3):
        _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])

    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    recurrence_factor = next(f for f in body["factors"] if f["factor_name"] == "Disease Recurrence")
    assert recurrence_factor["value"] == "high"
    assert "3" in recurrence_factor["explanation"]


def test_expert_case_escalated_produces_high_risk_factor(client, farmer_with_crop_cycle, db_session):
    from app.models.crop_health_case import CaseStatus, CropHealthCase

    tokens, crop_cycle_id = farmer_with_crop_cycle
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    case_row = db_session.get(CropHealthCase, uuid.UUID(case["id"]))
    case_row.status = CaseStatus.ESCALATED
    db_session.commit()

    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    case_factor = next(f for f in body["factors"] if f["factor_name"] == "Expert-Verified Case Status")
    assert case_factor["value"] == "high"


def test_no_expert_case_is_unknown_not_low(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    case_factor = next(f for f in body["factors"] if f["factor_name"] == "Expert-Verified Case Status")
    assert case_factor["value"] == "unknown"


def test_overdue_tasks_produce_operational_risk_factor(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    for i in range(2):
        client.post(
            f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
            json={"task_type": "general", "title": f"Task {i}", "due_date": "2020-01-01"},
            headers=auth_headers(tokens),
        )

    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    task_factor = next(f for f in body["factors"] if f["factor_name"] == "Operational Task Risk")
    assert task_factor["value"] == "high"


def test_no_overdue_tasks_is_low_not_unknown_when_tasks_exist(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"task_type": "general", "title": "Future task", "due_date": "2030-01-01"},
        headers=auth_headers(tokens),
    )
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    task_factor = next(f for f in body["factors"] if f["factor_name"] == "Operational Task Risk")
    assert task_factor["value"] == "low"


def test_financial_overspend_produces_high_risk_factor(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/cost-estimates",
        json={"category": "seed", "estimated_amount": "500.00"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "700.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    financial_factor = next(f for f in body["factors"] if f["factor_name"] == "Financial Execution Risk")
    assert financial_factor["value"] == "high"


def test_no_cost_estimate_is_unknown_not_zero_risk(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    financial_factor = next(f for f in body["factors"] if f["factor_name"] == "Financial Execution Risk")
    assert financial_factor["value"] == "unknown"


def test_weather_spray_condition_produces_medium_risk_factor(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    weather_factor = next(f for f in body["factors"] if f["factor_name"] == "Current Weather Risk")
    assert weather_factor["value"] == "medium"


def test_weather_unavailable_is_unknown(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    weather_factor = next(f for f in body["factors"] if f["factor_name"] == "Current Weather Risk")
    assert weather_factor["value"] == "unknown"


def test_two_medium_factors_aggregate_to_overall_high(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/cost-estimates",
        json={"category": "seed", "estimated_amount": "500.00"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "550.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=45.0))):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens))
    body = response.json()
    assert body["overall_risk"] == "high"


def test_cannot_access_another_farmers_risk_score(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_invalid_crop_cycle_id_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{uuid.uuid4()}/risk-score", headers=auth_headers(tokens))
    assert response.status_code == 404


def test_unauthenticated_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score")
    assert response.status_code == 401


def test_multiple_crop_cycles_never_combine_risk_data(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    _upload_and_analyze(client, tokens, crop_cycle_id_1, [TopKPrediction("Early Blight", 0.92)])

    with override_weather_provider(FakeWeatherProvider(available=False)):
        risk_1 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/risk-score", headers=headers).json()
        risk_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/risk-score", headers=headers).json()

    disease_1 = next(f for f in risk_1["factors"] if f["factor_name"] == "Recent Disease Detection")
    disease_2 = next(f for f in risk_2["factors"] if f["factor_name"] == "Recent Disease Detection")
    assert disease_1["value"] == "high"
    assert disease_2["value"] == "unknown"


def test_risk_score_is_deterministic_for_the_same_data(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])

    with override_weather_provider(FakeWeatherProvider(available=False)):
        first = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens)).json()
        second = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score", headers=auth_headers(tokens)).json()
    assert first["overall_risk"] == second["overall_risk"]
    assert first["factors"] == second["factors"]
