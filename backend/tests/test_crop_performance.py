import io
import uuid

from tests.conftest import auth_headers, override_model_provider, override_weather_provider
from tests.fake_model_provider import FakeModelProvider
from tests.fake_weather_provider import FakeWeatherProvider
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
from app.services.ai.model_provider import TopKPrediction
from app.services.weather.weather_provider import WeatherReading


def _upload_and_analyze(client, tokens, crop_cycle_id, top_predictions):
    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()
    with override_model_provider(FakeModelProvider(top_predictions=top_predictions)):
        return client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens)).json()


def _create_second_crop_cycle(client, tokens, sample_crop_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    return cycle["id"]


# --- Performance Score ---

def test_performance_with_no_data_at_all_is_insufficient_data(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["data_completeness_percent"] is not None
    assert body["overall_score"] is not None


def test_performance_score_reuses_treatment_effectiveness_verbatim(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    treatment = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens)).json()
    after_analysis = _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance", headers=auth_headers(tokens))
    body = response.json()
    treatment_component = next(c for c in body["components"] if c["name"] == "treatment_effectiveness")
    assert treatment_component["score"] == 100
    assert "improved" in treatment_component["explanation"]


def test_performance_score_is_deterministic(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    first = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance", headers=auth_headers(tokens)).json()
    second = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance", headers=auth_headers(tokens)).json()
    assert first == second


def test_missing_financial_component_is_excluded_not_guessed(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance", headers=auth_headers(tokens))
    body = response.json()
    financial_component = next(c for c in body["components"] if c["name"] == "financial_performance")
    assert financial_component["score"] is None


def test_cannot_access_another_farmers_performance_score(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_invalid_crop_cycle_returns_404_for_performance(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{uuid.uuid4()}/performance", headers=auth_headers(tokens))
    assert response.status_code == 404


# --- Comparison ---

def test_comparison_treats_zero_actual_cost_as_a_real_equal_comparison_not_missing_data(client, farmer_with_crop_cycle, sample_crop_id):
    """actual_cost is ALWAYS a real number (0 if nothing spent) - unlike
    estimated_cost, it is never None. Two crop cycles with no expenses
    correctly compare as 'equal' (both genuinely spent 0), not
    'insufficient_data' - there IS real data here, it's just zero."""
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    cost_metric = next(m for m in body["metrics"] if m["metric_name"] == "actual_cost")
    assert cost_metric["comparison"] == "equal"
    assert cost_metric["value_a"] == "0"
    assert cost_metric["value_b"] == "0"


def test_comparison_marks_performance_score_insufficient_data_only_when_genuinely_absent(client, farmer_with_crop_cycle, sample_crop_id):
    """overall_score is None only in the (rare) case where literally no
    performance component is available - unlike actual_cost, this really
    can be missing. With only the stage component available for both,
    the comparison must still be real (not insufficient_data)."""
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    body = response.json()
    score_metric = next(m for m in body["metrics"] if m["metric_name"] == "overall_performance_score")
    assert score_metric["comparison"] in ("equal", "a_higher", "b_higher")


def test_comparison_correctly_identifies_lower_cost_as_favorable(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_1}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "100.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_2}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    body = response.json()
    cost_metric = next(m for m in body["metrics"] if m["metric_name"] == "actual_cost")
    assert cost_metric["comparison"] == "a_higher"


def test_comparison_never_leaks_a_crop_cycle_belonging_to_another_farmer(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    # tokens_b doesn't own crop_cycle_id - attempting to compare it against itself as farmer B must fail.
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/comparison/{crop_cycle_id}", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_comparison_rejects_a_nonexistent_second_crop_cycle(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/comparison/{uuid.uuid4()}", headers=auth_headers(tokens))
    assert response.status_code == 404


# --- Input ROI ---

def test_input_roi_with_no_expenses_returns_empty_breakdown(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["categories"] == []
    assert body["roi_attribution_available"] is False


def test_input_roi_never_fabricates_a_roi_percentage(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "fertilizer", "amount": "300.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi", headers=auth_headers(tokens))
    body = response.json()
    assert body["roi_attribution_available"] is False
    for category in body["categories"]:
        assert category["roi_percent"] is None
    assert "cannot be honestly calculated" in body["limitation_note"]


def test_input_roi_correctly_computes_percent_of_total_across_categories(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "300.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "fertilizer", "amount": "700.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi", headers=auth_headers(tokens))
    body = response.json()
    assert body["total_actual_cost"] == "1000.00"
    seed = next(c for c in body["categories"] if c["category"] == "seed")
    fertilizer = next(c for c in body["categories"] if c["category"] == "fertilizer")
    assert seed["percent_of_total_cost"] == "30.00"
    assert fertilizer["percent_of_total_cost"] == "70.00"


def test_input_roi_excludes_revenue_entries_from_cost_breakdown(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "100.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "revenue", "category": "harvest_sale", "amount": "5000.00", "entry_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi", headers=auth_headers(tokens))
    body = response.json()
    assert body["total_actual_cost"] == "100.00"
    assert len(body["categories"]) == 1


def test_input_roi_includes_estimate_comparison_when_available(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/cost-estimates",
        json={"category": "seed", "estimated_amount": "500.00"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "400.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi", headers=auth_headers(tokens))
    body = response.json()
    seed = body["categories"][0]
    assert seed["estimated_cost"] == "500.00"
    assert seed["variance"] == "100.00"


def test_cannot_access_another_farmers_input_roi(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi", headers=auth_headers(tokens_b))
    assert response.status_code == 404


# --- Irrigation Intelligence ---

def test_irrigation_heavy_rain_produces_delay(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    from datetime import date

    from app.services.weather.weather_provider import ForecastDay

    forecast = [ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=85))]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=25), forecast=forecast)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence", headers=auth_headers(tokens))
    body = response.json()
    assert body["recommendation"] == "delay"
    assert body["soil_moisture_available"] is False


def test_irrigation_safe_with_pending_task_produces_irrigate_now(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    from datetime import date

    from app.services.weather.weather_provider import ForecastDay

    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/tasks",
        json={"task_type": "irrigation", "title": "Irrigate field", "due_date": "2026-06-01"},
        headers=auth_headers(tokens),
    )
    forecast = [ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=5))]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=25), forecast=forecast)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence", headers=auth_headers(tokens))
    body = response.json()
    assert body["recommendation"] == "irrigate_now"
    assert body["pending_irrigation_task_id"] is not None


def test_irrigation_safe_with_no_pending_task_produces_no_action(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    from datetime import date

    from app.services.weather.weather_provider import ForecastDay

    forecast = [ForecastDay(forecast_date=date.today(), reading=WeatherReading(rain_probability_percent=5))]
    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(temperature_c=25), forecast=forecast)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence", headers=auth_headers(tokens))
    body = response.json()
    assert body["recommendation"] == "no_action"
    assert body["pending_irrigation_task_id"] is None


def test_irrigation_missing_weather_produces_unknown(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider(available=False)):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence", headers=auth_headers(tokens))
    body = response.json()
    assert body["recommendation"] == "unknown"
    assert body["soil_moisture_available"] is False


def test_irrigation_always_discloses_soil_moisture_unavailable(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence", headers=auth_headers(tokens))
    assert response.json()["soil_moisture_available"] is False


def test_irrigation_never_leaks_task_across_crop_cycles(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id_1}/tasks",
        json={"task_type": "irrigation", "title": "Irrigate field", "due_date": "2026-06-01"},
        headers=auth_headers(tokens),
    )
    with override_weather_provider(FakeWeatherProvider()):
        response_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/irrigation-intelligence", headers=auth_headers(tokens))
    assert response_2.json()["pending_irrigation_task_id"] is None


def test_cannot_access_another_farmers_irrigation_intelligence(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    with override_weather_provider(FakeWeatherProvider()):
        response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_unauthenticated_requests_are_rejected_for_all_four_endpoints(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    assert client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/performance").status_code == 401
    assert client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/comparison/{uuid.uuid4()}").status_code == 401
    assert client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi").status_code == 401
    assert client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/irrigation-intelligence").status_code == 401
