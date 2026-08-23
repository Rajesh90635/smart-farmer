"""
Phase 40: Full System Integration & Release Validation.

These tests exercise COMPLETE business journeys across multiple phases
in a single flow, proving the system works together - not just that
each phase's own isolated unit tests pass. Every flow ends with exact
arithmetic assertions or exact state assertions, never a bare HTTP 200
check.
"""
import io
import uuid

from tests.conftest import auth_headers, override_model_provider, override_weather_provider
from tests.fake_model_provider import FakeModelProvider
from tests.fake_weather_provider import FakeWeatherProvider
from tests.harvest_factories import valid_harvest_listing_payload, valid_offer_payload
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
from tests.professional_factories import valid_case_payload
from app.services.ai.model_provider import TopKPrediction
from app.services.weather.weather_provider import WeatherReading


def _upload_and_analyze(client, tokens, crop_cycle_id, top_predictions):
    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()
    with override_model_provider(FakeModelProvider(top_predictions=top_predictions)):
        return client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens)).json()


def test_flow_a_crop_health_treatment_timeline_end_to_end(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    analysis = _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    assert analysis["result_status"] == "disease_detected"

    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=headers).json()
    assert case is not None

    treatment = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=headers).json()
    assert treatment["before_result_status"] == "disease_detected"

    after_analysis = _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=headers,
    )

    effectiveness = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=headers).json()
    assert effectiveness["result"] == "improved"

    timeline = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/health-timeline", headers=headers).json()
    event_types = {e["event_type"] for e in timeline["events"]}
    assert "ai_analysis" in event_types
    assert "health_case_created" in event_types
    assert "treatment_applied" in event_types
    assert "treatment_follow_up" in event_types
    improvement_event = next(e for e in timeline["events"] if e["event_type"] == "treatment_follow_up")
    assert "improvement" in improvement_event["description"].lower()


def test_flow_a_never_leaks_to_another_farmer(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens))

    assert client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/health-timeline", headers=auth_headers(tokens_b)).status_code == 404
    assert client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", headers=auth_headers(tokens_b)).status_code == 404


def test_flow_b_financial_journey_manual_expense_to_profit_with_exact_arithmetic(client, farmer_with_crop_cycle, verified_buyer, db_session):
    from app.models.sale_order import SaleOrder, SaleOrderStatus

    tokens, crop_cycle_id = farmer_with_crop_cycle
    buyer_tokens, _ = verified_buyer
    headers = auth_headers(tokens)

    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/cost-estimates", json={"category": "seed", "estimated_amount": "1000.00"}, headers=headers)
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "600.00", "entry_date": "2026-01-01"},
        headers=headers,
    )

    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=headers).json()
    listing = client.post(f"/api/v1/harvests/{harvest['id']}/listing", json=valid_harvest_listing_payload(), headers=headers).json()
    offer = client.post(f"/api/v1/marketplace/listings/{listing['id']}/offers", json=valid_offer_payload(), headers=auth_headers(buyer_tokens)).json()
    sale = client.post(f"/api/v1/marketplace/offers/{offer['id']}/accept", headers=headers).json()

    sale_row = db_session.get(SaleOrder, uuid.UUID(sale["id"]))
    sale_row.status = SaleOrderStatus.COMPLETED
    db_session.commit()

    import_result = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=headers).json()
    assert import_result["imported_count"] == 1

    second_import = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/import-sales", headers=headers).json()
    assert second_import["imported_count"] == 0

    summary = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary", headers=headers).json()
    from decimal import Decimal

    assert Decimal(summary["actual_cost"]) == Decimal("600.00")
    assert Decimal(summary["actual_revenue"]) == Decimal(sale["net_value"])
    assert Decimal(summary["actual_profit_loss"]) == Decimal(sale["net_value"]) - Decimal("600.00")

    forecast = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast", headers=headers).json()
    assert Decimal(forecast["actual_revenue"]) == Decimal(sale["net_value"])
    assert Decimal(forecast["committed_revenue"]) == Decimal("0")


def test_flow_b_invoice_ocr_never_auto_creates_ledger_entry(client, farmer_with_crop_cycle):
    from PIL import Image, ImageDraw

    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Test Vendor", fill="black")
    draw.text((20, 200), "Total Amount: Rs 750.00", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    files = {"file": ("invoice.png", io.BytesIO(buf.getvalue()), "image/png")}
    invoice = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/invoices", files=files, headers=headers).json()

    ledger_before = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=headers).json()
    assert ledger_before["entries"] == []

    client.post(
        f"/api/v1/invoices/{invoice['id']}/confirm",
        json={"amount": "800.00", "entry_date": "2026-01-01", "category": "fertilizer"},
        headers=headers,
    )

    ledger_after = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/ledger", headers=headers).json()
    assert len(ledger_after["entries"]) == 1
    from decimal import Decimal

    assert Decimal(ledger_after["entries"][0]["amount"]) == Decimal("800.00")


def test_flow_c_weather_action_feedback_personalization_evidence_floor(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)

    with override_weather_provider(FakeWeatherProvider(current=WeatherReading(wind_speed_kmh=50))):
        weather_actions = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/weather-actions", headers=headers).json()
    assert weather_actions["weather_available"] is True

    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/advisory-feedback",
        json={"source_type": "weather_action", "feedback_type": "helpful"},
        headers=headers,
    )

    profile = client.get("/api/v1/farmers/me/personalization", headers=headers).json()
    feedback_signal = next(p for p in profile["preferences"] if p["signal_name"] == "advisory_feedback_ratio")
    assert feedback_signal["evidence_count"] == 1
    assert feedback_signal["confidence"] is None


def test_temporal_leakage_never_occurs_across_the_full_integrated_flow(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    headers = auth_headers(tokens)
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=headers,
    )
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])

    summary = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary", headers=headers).json()
    assert summary["feature_snapshot"]["outcome_label"] is None
    assert summary["ml_training_justified"] is False


def test_cross_farmer_isolation_holds_across_the_entire_integrated_surface(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    headers_b = auth_headers(tokens_b)

    endpoints = [
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger",
        f"/api/v1/crop-cycles/{crop_cycle_id}/financial-summary",
        f"/api/v1/crop-cycles/{crop_cycle_id}/profit-forecast",
        f"/api/v1/crop-cycles/{crop_cycle_id}/risk-score",
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        f"/api/v1/crop-cycles/{crop_cycle_id}/health-timeline",
        f"/api/v1/crop-cycles/{crop_cycle_id}/performance",
        f"/api/v1/crop-cycles/{crop_cycle_id}/input-roi",
        f"/api/v1/crop-cycles/{crop_cycle_id}/learning-summary",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint, headers=headers_b)
        assert response.status_code == 404, f"{endpoint} did not reject farmer B (got {response.status_code})"
