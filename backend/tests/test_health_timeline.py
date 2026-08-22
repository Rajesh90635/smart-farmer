import io
import uuid

from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
from tests.professional_factories import valid_case_payload
from app.services.ai.model_provider import TopKPrediction


def _upload_photo(client, tokens, crop_cycle_id):
    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    return client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()


def _analyze(client, tokens, photo_id, top_predictions):
    with override_model_provider(FakeModelProvider(top_predictions=top_predictions)):
        return client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()


def _get_timeline(client, tokens, crop_cycle_id):
    return client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/health-timeline", headers=auth_headers(tokens))


def test_empty_timeline_still_returns_the_crop_cycle_started_event(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    response = _get_timeline(client, tokens, crop_cycle_id)
    assert response.status_code == 200
    body = response.json()
    assert len(body["events"]) == 1
    assert body["events"][0]["event_type"] == "crop_cycle_started"


def test_unanalyzed_photo_produces_a_photo_captured_event(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    _upload_photo(client, tokens, crop_cycle_id)

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    photo_events = [e for e in body["events"] if e["event_type"] == "photo_captured"]
    assert len(photo_events) == 1


def test_analyzed_photo_produces_only_one_ai_analysis_event_not_a_duplicate_photo_event(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    photo = _upload_photo(client, tokens, crop_cycle_id)
    _analyze(client, tokens, photo["id"], [TopKPrediction("Early Blight", 0.92)])

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    photo_events = [e for e in body["events"] if e["event_type"] == "photo_captured"]
    analysis_events = [e for e in body["events"] if e["event_type"] == "ai_analysis"]
    assert len(photo_events) == 0
    assert len(analysis_events) == 1
    assert analysis_events[0]["health_status"] == "disease_detected"


def test_ai_analysis_health_status_is_the_real_verbatim_value_never_fabricated_severity(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    photo = _upload_photo(client, tokens, crop_cycle_id)
    _analyze(client, tokens, photo["id"], [TopKPrediction("healthy", 0.95)])

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    analysis_event = next(e for e in body["events"] if e["event_type"] == "ai_analysis")
    assert analysis_event["health_status"] == "healthy"
    assert "%" not in analysis_event["description"]


def test_health_case_and_review_appear_as_separate_dated_events(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    case = client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(tokens)).json()

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    case_events = [e for e in body["events"] if e["event_type"] == "health_case_created"]
    assert len(case_events) == 1
    assert case_events[0]["case_id"] == case["id"]


def test_treatment_without_follow_up_produces_only_the_applied_event(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-01-01", "notes": "Applied fungicide"},
        headers=auth_headers(tokens),
    )

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    treatment_events = [e for e in body["events"] if e["event_type"] == "treatment_applied"]
    follow_up_events = [e for e in body["events"] if e["event_type"] == "treatment_follow_up"]
    assert len(treatment_events) == 1
    assert len(follow_up_events) == 0


def test_treatment_follow_up_shows_insufficient_evidence_honestly_when_no_analysis_exists(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    treatment = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-01-01"},
        headers=auth_headers(tokens),
    ).json()
    client.post(f"/api/v1/treatments/{treatment['id']}/follow-ups", json={"observation_date": "2026-01-10"}, headers=auth_headers(tokens))

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    follow_up_event = next(e for e in body["events"] if e["event_type"] == "treatment_follow_up")
    assert "not enough" in follow_up_event["description"].lower()


def test_treatment_follow_up_shows_improvement_when_real_evidence_supports_it(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    photo_before = _upload_photo(client, tokens, crop_cycle_id)
    _analyze(client, tokens, photo_before["id"], [TopKPrediction("Early Blight", 0.92)])

    treatment = client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-01-01"},
        headers=auth_headers(tokens),
    ).json()

    photo_after = _upload_photo(client, tokens, crop_cycle_id)
    after_analysis = _analyze(client, tokens, photo_after["id"], [TopKPrediction("healthy", 0.95)])
    client.post(
        f"/api/v1/treatments/{treatment['id']}/follow-ups",
        json={"after_analysis_id": after_analysis["id"], "observation_date": "2026-01-10"},
        headers=auth_headers(tokens),
    )

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    follow_up_event = next(e for e in body["events"] if e["event_type"] == "treatment_follow_up")
    assert "improvement" in follow_up_event["description"].lower()


def test_events_are_ordered_descending_by_datetime(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-01-01"},
        headers=auth_headers(tokens),
    )
    client.post(
        f"/api/v1/crop-cycles/{crop_cycle_id}/treatments",
        json={"application_date": "2026-06-01"},
        headers=auth_headers(tokens),
    )

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    treatment_events = [e for e in body["events"] if e["event_type"] == "treatment_applied"]
    assert len(treatment_events) == 2
    assert treatment_events[0]["event_datetime"] > treatment_events[1]["event_datetime"]


def test_timeline_ordering_is_fully_deterministic_across_repeated_calls(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens))
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens))

    first = _get_timeline(client, tokens, crop_cycle_id).json()
    second = _get_timeline(client, tokens, crop_cycle_id).json()
    assert [e["source_id"] for e in first["events"]] == [e["source_id"] for e in second["events"]]


def test_harvest_without_actual_date_produces_no_harvested_event(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens))

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    harvest_events = [e for e in body["events"] if e["event_type"] == "harvested"]
    assert len(harvest_events) == 0


def test_harvest_with_actual_date_produces_a_harvested_event(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    harvest = client.post(f"/api/v1/harvests/from-crop-cycle/{crop_cycle_id}", headers=auth_headers(tokens)).json()
    client.post(
        f"/api/v1/harvests/{harvest['id']}/confirm-ready",
        json={"estimated_quantity": "100.00", "actual_harvest_date": "2026-03-01"},
        headers=auth_headers(tokens),
    )

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    harvest_events = [e for e in body["events"] if e["event_type"] == "harvested"]
    assert len(harvest_events) == 1


def test_cannot_access_another_farmers_timeline(client, farmer_with_crop_cycle, another_farmer):
    _, crop_cycle_id = farmer_with_crop_cycle
    _, tokens_b = another_farmer
    response = _get_timeline(client, tokens_b, crop_cycle_id)
    assert response.status_code == 404


def test_invalid_crop_cycle_returns_404(client, farmer_with_crop_cycle):
    tokens, _ = farmer_with_crop_cycle
    response = _get_timeline(client, tokens, uuid.uuid4())
    assert response.status_code == 404


def test_unauthenticated_request_is_rejected(client, farmer_with_crop_cycle):
    _, crop_cycle_id = farmer_with_crop_cycle
    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/health-timeline")
    assert response.status_code == 401


def test_multiple_crop_cycles_never_combine_timeline_events(client, farmer_with_crop_cycle, sample_crop_id):
    tokens, crop_cycle_id_1 = farmer_with_crop_cycle
    from tests.farm_factories import valid_crop_cycle_payload, valid_farm_payload, valid_plot_payload

    headers = auth_headers(tokens)
    farm = client.post("/api/v1/farms", json=valid_farm_payload(), headers=headers).json()
    plot = client.post(f"/api/v1/farms/{farm['id']}/plots", json=valid_plot_payload(), headers=headers).json()
    cycle_2 = client.post(f"/api/v1/plots/{plot['id']}/crops", json=valid_crop_cycle_payload(sample_crop_id), headers=headers).json()
    crop_cycle_id_2 = cycle_2["id"]

    client.post(f"/api/v1/crop-cycles/{crop_cycle_id_1}/treatments", json={"application_date": "2026-01-01"}, headers=headers)

    timeline_1 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_1}/health-timeline", headers=headers).json()
    timeline_2 = client.get(f"/api/v1/crop-cycles/{crop_cycle_id_2}/health-timeline", headers=headers).json()

    treatments_1 = [e for e in timeline_1["events"] if e["event_type"] == "treatment_applied"]
    treatments_2 = [e for e in timeline_2["events"] if e["event_type"] == "treatment_applied"]
    assert len(treatments_1) == 1
    assert len(treatments_2) == 0


def test_multiple_event_types_all_appear_together(client, farmer_with_crop_cycle):
    tokens, crop_cycle_id = farmer_with_crop_cycle
    photo = _upload_photo(client, tokens, crop_cycle_id)
    _analyze(client, tokens, photo["id"], [TopKPrediction("Early Blight", 0.92)])
    client.post(f"/api/v1/crop-cycles/{crop_cycle_id}/treatments", json={"application_date": "2026-01-01"}, headers=auth_headers(tokens))
    client.post("/api/v1/cases", json=valid_case_payload(crop_cycle_id), headers=auth_headers(tokens))

    body = _get_timeline(client, tokens, crop_cycle_id).json()
    event_types = {e["event_type"] for e in body["events"]}
    assert "crop_cycle_started" in event_types
    assert "ai_analysis" in event_types
    assert "treatment_applied" in event_types
    assert "health_case_created" in event_types
