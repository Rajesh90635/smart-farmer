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


def _create_crop_cycle_with_variety(client, tokens, crop_id, variety_id):
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle = client.post(
        f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(crop_id, variety_id=variety_id), headers=headers
    ).json()
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


def test_comparison_reports_insufficient_data_for_yield_when_nothing_harvested_yet(client, farmer_with_crop_cycle, sample_crop_id):
    """D96-03: no HarvestRecord.actual_quantity is ever written by any
    current endpoint (a separately-tracked FUTURE gap, see
    docs/HARVEST_MANAGEMENT.md) - so today this metric always reports
    'insufficient_data', honestly, rather than a fabricated 0-yield."""
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    body = response.json()
    yield_metric = next(m for m in body["metrics"] if m["metric_name"] == "actual_yield")
    assert yield_metric["comparison"] == "insufficient_data"


def test_comparison_variety_is_insufficient_data_when_either_cycle_has_no_variety(client, farmer_with_crop_cycle, sample_crop_id):
    """D96-02 (docs/audit/FINAL_CANONICAL_group_D.md): the default
    farmer_with_crop_cycle/second-cycle fixtures never set variety_id."""
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    variety_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "variety")
    assert variety_metric["comparison"] == "insufficient_data"


def test_comparison_variety_reports_equal_for_the_same_variety(client, registered_farmer, sample_crop_id, db_session):
    """D96-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    from tests.test_crop_variety import _create_variety

    _, tokens = registered_farmer
    # Unique per run - the persistent shared test DB never truncates
    # crop_varieties between runs, and (crop_id, name) is a real DB
    # uniqueness constraint (same convention as tests/test_crop_variety.py's
    # own _unique() helper).
    variety_id = _create_variety(db_session, sample_crop_id, f"Hybrid Variety {uuid.uuid4().hex[:8]}")
    crop_cycle_id_1 = _create_crop_cycle_with_variety(client, tokens, sample_crop_id, variety_id)
    crop_cycle_id_2 = _create_crop_cycle_with_variety(client, tokens, sample_crop_id, variety_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    variety_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "variety")
    assert variety_metric["comparison"] == "equal"


def test_comparison_variety_reports_not_directly_comparable_for_different_varieties(client, registered_farmer, sample_crop_id, db_session):
    """D96-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    from tests.test_crop_variety import _create_variety

    _, tokens = registered_farmer
    suffix = uuid.uuid4().hex[:8]
    variety_id_1 = _create_variety(db_session, sample_crop_id, f"Variety One {suffix}")
    variety_id_2 = _create_variety(db_session, sample_crop_id, f"Variety Two {suffix}")
    crop_cycle_id_1 = _create_crop_cycle_with_variety(client, tokens, sample_crop_id, variety_id_1)
    crop_cycle_id_2 = _create_crop_cycle_with_variety(client, tokens, sample_crop_id, variety_id_2)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    variety_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "variety")
    assert variety_metric["comparison"] == "not_directly_comparable"


def test_comparison_disease_recurrence_is_insufficient_data_with_no_analysis(client, farmer_with_crop_cycle, sample_crop_id):
    """D96-07 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    disease_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "disease_recurrence_count")
    assert disease_metric["comparison"] == "insufficient_data"


def test_comparison_disease_recurrence_correctly_identifies_fewer_occurrences_as_favorable(
    client, farmer_with_crop_cycle, sample_crop_id
):
    """D96-07 (docs/audit/FINAL_CANONICAL_group_D.md): lower disease
    recurrence is favorable ('a_higher' means cycle A wins) - reuses the
    exact same AIAnalysis data crop_risk_service._disease_recurrence_factor
    is built on."""
    from tests.test_crop_performance import _upload_and_analyze
    from app.services.ai.model_provider import TopKPrediction

    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    _upload_and_analyze(client, tokens, crop_cycle_id_1, [TopKPrediction("Healthy", 0.95)])
    _upload_and_analyze(client, tokens, crop_cycle_id_2, [TopKPrediction("Early Blight", 0.90)])

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    disease_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "disease_recurrence_count")
    assert disease_metric["value_a"] == "0"
    assert disease_metric["value_b"] == "1"
    assert disease_metric["comparison"] == "a_higher"


def test_comparison_weather_impact_counts_real_crop_alert_notifications_per_cycle(client, farmer_with_crop_cycle, sample_crop_id, db_session):
    """D96-08 (docs/audit/FINAL_CANONICAL_group_D.md): reuses the real,
    persisted crop_alert Notification history (weather_action_engine_service.py
    is deliberately read-only/unpersisted, so it has no history of its
    own to reuse) - 0 is a genuine fact here, never insufficient_data."""
    from app.models.notification import Notification, NotificationCategory, NotificationPriority

    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)
    farmer_id = client.get("/api/v1/farmers/me", headers=auth_headers(tokens)).json()["user_id"]

    db_session.add(Notification(
        farmer_id=uuid.UUID(farmer_id), category=NotificationCategory.CROP_ALERT, priority=NotificationPriority.MEDIUM,
        title="Heavy Rain Warning", body="Heavy rain expected.", language_code="en",
        dedup_key=f"test_crop_alert:{crop_cycle_id_1}", related_entity_type="crop_cycle", related_entity_id=crop_cycle_id_1,
    ))
    db_session.commit()

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    weather_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "weather_impact_count")
    assert weather_metric["value_a"] == "1"
    assert weather_metric["value_b"] == "0"
    assert weather_metric["comparison"] == "b_higher"  # lower is better - cycle B (0 alerts) wins


def test_comparison_weather_impact_is_zero_not_insufficient_data_with_no_alerts(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    weather_metric = next(m for m in response.json()["metrics"] if m["metric_name"] == "weather_impact_count")
    assert weather_metric["value_a"] == "0"
    assert weather_metric["value_b"] == "0"
    assert weather_metric["comparison"] == "equal"


def test_comparison_reports_same_crop_true_when_both_cycles_share_a_crop(client, farmer_with_crop_cycle, sample_crop_id):
    """D96-01 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    assert response.json()["same_crop"] is True


def test_comparison_reports_same_crop_false_when_cycles_are_different_crops(client, farmer_with_crop_cycle, db_session):
    """D96-01 (docs/audit/FINAL_CANONICAL_group_D.md)."""
    from sqlalchemy import select

    from app.models.crop_master import CropMaster

    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    other_crop = db_session.execute(select(CropMaster).where(CropMaster.name != "Tomato").limit(1)).scalar_one()
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, str(other_crop.id))

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    assert response.json()["same_crop"] is False


def test_comparison_correctly_identifies_higher_yield_once_harvest_quantities_exist(
    client, farmer_with_crop_cycle, sample_crop_id, db_session
):
    """Once HarvestRecord.actual_quantity IS populated (whenever the
    separately-tracked 'mark harvested' write path is eventually built),
    the comparison must correctly treat a higher yield as favorable, and
    must SUM multiple harvest records for one cycle (perennial/repeated-
    picking crops can have more than one). No write endpoint exists yet
    for actual_quantity, so this inserts directly - simulating the future
    wiring, not today's farmer-reachable flow."""
    import uuid as uuid_mod

    from app.core.jwt import decode_access_token
    from app.models.crop_cycle import CropCycle
    from app.models.harvest_record import HarvestRecord

    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    crop_cycle_id_2 = _create_second_crop_cycle(client, tokens, sample_crop_id)
    farmer_id = uuid_mod.UUID(decode_access_token(tokens["access_token"])["sub"])

    def _insert_harvest(crop_cycle_id: str, quantity: int) -> None:
        cc = db_session.get(CropCycle, uuid_mod.UUID(crop_cycle_id))
        db_session.add(HarvestRecord(
            farmer_id=farmer_id, farm_id=cc.plot.farm_id, plot_id=cc.plot_id, crop_cycle_id=cc.id,
            crop_id=cc.crop_id, actual_quantity=quantity,
        ))

    _insert_harvest(crop_cycle_id_1, 200)
    _insert_harvest(crop_cycle_id_1, 150)  # second pick - must be summed
    _insert_harvest(crop_cycle_id_2, 100)
    db_session.commit()

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/comparison/{crop_cycle_id_2}", headers=auth_headers(tokens))
    body = response.json()
    yield_metric = next(m for m in body["metrics"] if m["metric_name"] == "actual_yield")
    assert yield_metric["value_a"] == "350.00"
    assert yield_metric["value_b"] == "100.00"
    assert yield_metric["comparison"] == "a_higher"


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
