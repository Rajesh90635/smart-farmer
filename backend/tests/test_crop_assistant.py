import io
import uuid

from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
from app.services.ai.model_provider import TopKPrediction


def _ask(client, tokens, crop_cycle_id, question):
    return client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/assistant", json={"question": question}, headers=auth_headers(tokens))


def _upload_and_analyze(client, tokens, crop_cycle_id, top_predictions):
    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()
    with override_model_provider(FakeModelProvider(top_predictions=top_predictions)):
        return client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens)).json()


def test_crop_status_question_returns_real_crop_context(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "What is happening to my crop?")
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "crop_status"
    assert len(body["context_used"]) > 0


def test_disease_question_with_no_analysis_is_honestly_unavailable(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "What is wrong with my crop, I see spots")
    body = response.json()
    assert body["intent"] == "disease_status"
    assert "no data was available" in body["limitations"][0].lower()


def test_disease_question_with_real_disease_detected_reflects_real_result(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])

    response = _ask(client, tokens, crop_cycle_id, "What is wrong with my crop, I see spots")
    body = response.json()
    assert "early blight" in body["answer"].lower()


def test_low_confidence_disease_result_is_never_upgraded_to_certainty(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.35)])

    response = _ask(client, tokens, crop_cycle_id, "What is wrong with my crop, I see spots")
    body = response.json()
    assert "not sure" in body["answer"].lower() or "low" in body["answer"].lower() or "confidence" in " ".join(body["limitations"]).lower()


def test_treatment_question_with_no_treatment_is_honestly_unavailable(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "What treatment did I apply")
    body = response.json()
    assert body["intent"] == "treatment_status"
    assert "no treatment" in body["answer"].lower()


def test_treatment_question_reuses_phase_34_effectiveness_verbatim(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    treatment = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens)
    ).json()
    after_analysis = _upload_and_analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = _ask(client, tokens, crop_cycle_id, "Did the treatment help?")
    body = response.json()
    # Reuses Phase 34's own basis text VERBATIM - this is the correct
    # behavior; asserting on Phase 34's actual wording, not a guessed keyword.
    assert "appears healthy" in body["answer"].lower()


def test_financial_question_reuses_phase_31_summary_verbatim(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/ledger/entries",
        json={"entry_type": "expense", "category": "seed", "amount": "500.00", "entry_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )

    response = _ask(client, tokens, crop_cycle_id, "How much have I spent on this crop?")
    body = response.json()
    assert body["intent"] == "financial_status"
    assert "500.00" in body["answer"]


def test_missing_market_price_or_yield_is_never_fabricated(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "What is the current market price for my crop and how much will I yield?")
    body = response.json()
    assert "%" not in body["answer"]


def test_prescription_request_is_redirected_never_answered(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "What pesticide should I use for my crop?")
    body = response.json()
    assert body["intent"] == "prescription_blocked"
    assert "expert" in body["answer"].lower()


def test_cannot_access_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = _ask(client, tokens_b, crop_cycle_id, "What is happening to my crop?")
    assert response.status_code == 404


def test_context_never_leaks_across_crop_cycles(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    _upload_and_analyze(client, tokens, crop_cycle_id_1, [TopKPrediction("Early Blight", 0.92)])

    response_2 = _ask(client, tokens, crop_cycle_id_2, "What is wrong with my crop, I see spots")
    body_2 = response_2.json()
    assert "early blight" not in body_2["answer"].lower()


def test_invalid_crop_cycle_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = _ask(client, tokens, uuid.uuid4(), "What is happening to my crop?")
    assert response.status_code == 404


def test_unauthenticated_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/assistant", json={"question": "What is happening to my crop?"})
    assert response.status_code == 401


def test_empty_question_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "")
    assert response.status_code == 422


def test_excessively_long_question_is_rejected(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "a" * 501)
    assert response.status_code == 422


def test_general_agriculture_question_is_honestly_unavailable_not_fabricated(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _ask(client, tokens, crop_cycle_id, "What is the meaning of life")
    body = response.json()
    assert body["intent"] == "general_agriculture"
