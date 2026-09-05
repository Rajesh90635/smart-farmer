import io
import uuid

from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
from tests.professional_factories import valid_case_payload
from app.services.ai.model_provider import TopKPrediction


def _analyze(client, tokens, crop_cycle_id, top_predictions, crop_match=True):
    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()

    with override_model_provider(FakeModelProvider(top_predictions=top_predictions, crop_match=crop_match)):
        return client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens))


def _create_treatment(client, tokens, crop_cycle_id, application_date="2026-01-01"):
    return client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": application_date, "notes": "Applied fungicide"},
        headers=auth_headers(tokens),
    )


def test_treatment_creation_snapshots_the_most_recent_existing_analysis(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)]).json()

    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    assert treatment["before_analysis_id"] == analysis["id"]
    assert treatment["before_result_status"] == "disease_detected"


def test_treatment_with_no_prior_analysis_has_null_before_snapshot(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    assert treatment["before_analysis_id"] is None
    assert treatment["before_result_status"] is None


def test_cannot_create_treatment_under_another_farmers_crop_cycle(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = _create_treatment(client, tokens_b, crop_cycle_id)
    assert response.status_code == 404


def test_effectiveness_is_insufficient_evidence_with_no_follow_up(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "insufficient_evidence"
    assert body["has_follow_up"] is False
    assert "follow-up" in body["basis"].lower()


def test_effectiveness_is_insufficient_evidence_with_no_before_analysis(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "insufficient_evidence"
    assert "before" in body["basis"].lower()


def test_effectiveness_improved_disease_to_healthy(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    assert treatment["before_result_status"] == "disease_detected"

    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "improved"
    assert body["before_result_status"] == "disease_detected"
    assert body["after_result_status"] == "healthy"


def test_effectiveness_worsened_healthy_to_disease(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    assert treatment["before_result_status"] == "healthy"

    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "worsened"


def test_effectiveness_no_significant_change_disease_to_disease(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()

    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "no_significant_change"


def test_effectiveness_is_insufficient_evidence_when_follow_up_analysis_is_inconclusive(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)])
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()

    mismatched = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)], crop_match=False).json()
    assert mismatched["result_status"] == "crop_mismatch"

    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": mismatched["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "insufficient_evidence"
    assert "inconclusive" in body["basis"].lower()


def test_farmer_notes_alone_never_produce_a_fabricated_effectiveness_result(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    treatment_response = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-01-01", "notes": "This treatment worked perfectly, crop fully cured!"},
        headers=auth_headers(tokens),
    ).json()

    client.post(
        f"/api/v1/treatments/{treatment_response['id']}/follow-ups",
        json={"observation_date": "2026-01-10", "notes": "Looks great now"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment_response['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "insufficient_evidence"


def test_cannot_access_another_farmers_treatment(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_cannot_create_follow_up_for_another_farmers_treatment(client, farmer_with_crop_cycle, another_farmer):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()

    response = client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"observation_date": "2026-01-10"},
        headers=auth_headers(tokens_b),
    )
    assert response.status_code == 404


def test_multiple_crop_cycles_never_combine_treatment_data(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    _create_treatment(client, tokens, crop_cycle_id_1)

    treatments_1 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/treatments", headers=headers).json()
    treatments_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/treatments", headers=headers).json()
    assert len(treatments_1["items"]) == 1
    assert len(treatments_2["items"]) == 0


def test_invalid_crop_cycle_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = _create_treatment(client, tokens, uuid.uuid4())
    assert response.status_code == 404


def test_unauthenticated_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments")
    assert response.status_code == 401


def test_worsened_outcome_with_no_linked_case_recommends_expert_review(client, farmer_with_crop_cycle):
    """D38-06/D39-07: a worsening outcome must not be a passive label -
    when no expert case is linked yet, the farmer gets an explicit,
    actionable recommendation rather than a silently-created case."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    assert treatment["case_id"] is None

    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "worsened"
    assert body["recommended_action"] == "request_expert_review"


def test_worsened_outcome_with_linked_case_auto_escalates(client, farmer_with_crop_cycle):
    """D38-06/D39-07: when the treatment IS linked to an existing,
    already-consented expert case, a worsening outcome automatically
    escalates that case and sends a CRITICAL notification - no new case
    is fabricated, and no new consent is required since it already exists
    for this case."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(tokens)).json()

    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    treatment = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"case_id": case["id"], "application_date": "2026-01-01"},
        headers=auth_headers(tokens),
    ).json()

    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    response = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    body = response.json()
    assert body["result"] == "worsened"
    assert body["recommended_action"] == "case_escalated"

    case_after = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers(tokens)).json()
    assert case_after["status"] == "escalated"

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    critical = [n for n in notifications if n["priority"] == "critical"]
    assert len(critical) == 1


def test_worsened_outcome_escalation_is_idempotent(client, farmer_with_crop_cycle):
    """Re-fetching effectiveness after the case is already escalated must
    not re-escalate or send a second CRITICAL notification - guards
    against a farmer/UI polling the effectiveness endpoint repeatedly."""
    tokens, crop_cycle_id = farmer_with_crop_cycle
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(tokens)).json()

    _analyze(client, tokens, crop_cycle_id, [TopKPrediction("healthy", 0.95)])
    treatment = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"case_id": case["id"], "application_date": "2026-01-01"},
        headers=auth_headers(tokens),
    ).json()

    after_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.92)]).json()
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    second = client.get(f"/api/v1/treatments/{treatment['id']}/effectiveness", headers=auth_headers(tokens))
    assert second.json()["recommended_action"] == "case_escalated"

    notifications = client.get("/api/v1/notifications", headers=auth_headers(tokens)).json()["items"]
    critical = [n for n in notifications if n["priority"] == "critical"]
    assert len(critical) == 1


def test_list_follow_ups_for_treatment(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    treatment = _create_treatment(client, tokens, crop_cycle_id).json()
    client.post(f"/api/v1/treatments/{treatment['id']}/follow-ups", json={"observation_date": "2026-01-05"}, headers=auth_headers(tokens))
    client.post(f"/api/v1/treatments/{treatment['id']}/follow-ups", json={"observation_date": "2026-01-10"}, headers=auth_headers(tokens))

    response = client.get(f"/api/v1/treatments/{treatment['id']}/follow-ups", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
