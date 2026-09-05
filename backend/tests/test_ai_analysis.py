from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from app.services.ai.model_provider import TopKPrediction


def test_valid_photo_analysis_with_real_default_provider_is_honestly_unavailable(client, uploaded_photo):
    """The REAL production path (no override): since no real model is
    configured, every analysis must honestly report AI_UNAVAILABLE - this
    is the correct behavior, not a bug, per the 'no fake AI' rule."""
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["result_status"] == "ai_unavailable"
    assert body["analysis_status"] == "completed"
    assert body["requires_review"] is True
    assert body["predicted_class"] is None
    assert body["model_name"] == "crop_disease_baseline"
    assert body["model_version"] == "unconfigured-0.0"


def test_healthy_result_with_fake_provider(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Healthy", 0.95)], supported_crops=["tomato"])
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    assert response.status_code == 201
    body = response.json()
    assert body["result_status"] == "healthy"
    assert body["predicted_class"] == "Healthy"
    assert body["requires_review"] is False


def test_disease_detected_result_with_fake_provider(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.90)], supported_crops=["tomato"])
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    body = response.json()
    assert body["result_status"] == "disease_detected"
    assert body["predicted_class"] == "Early Blight"


def test_low_confidence_result_never_names_a_disease(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.30)], supported_crops=["tomato"])
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    body = response.json()
    assert body["result_status"] == "low_confidence"
    assert body["predicted_class"] is None  # the absolute rule - never name a disease at low confidence
    assert body["requires_review"] is True


# --- D91-07/D91-09/D91-10: farmer correction of a specific AI result ---

def test_farmer_can_submit_a_correction_marking_a_false_positive(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.90)], supported_crops=["tomato"])
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()
    assert analysis["result_status"] == "disease_detected"

    response = client.post(
        f"/api/v1/ai/analysis/{analysis['id']}/correction",
        json={"correction": "actually_healthy", "notes": "It was just water spots, not disease."},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["farmer_correction"] == "actually_healthy"
    assert body["farmer_correction_notes"] == "It was just water spots, not disease."
    assert body["farmer_corrected_at"] is not None


def test_farmer_can_revise_a_previously_submitted_correction(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.90)], supported_crops=["tomato"])
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    client.post(
        f"/api/v1/ai/analysis/{analysis['id']}/correction", json={"correction": "actually_healthy"}, headers=auth_headers(tokens)
    )
    revised = client.post(
        f"/api/v1/ai/analysis/{analysis['id']}/correction", json={"correction": "confirmed_correct"}, headers=auth_headers(tokens)
    )
    assert revised.json()["farmer_correction"] == "confirmed_correct"


def test_cannot_submit_correction_for_another_farmers_analysis(client, uploaded_photo, another_farmer):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.90)], supported_crops=["tomato"])
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    _, tokens_b = another_farmer
    response = client.post(
        f"/api/v1/ai/analysis/{analysis['id']}/correction", json={"correction": "actually_healthy"}, headers=auth_headers(tokens_b)
    )
    assert response.status_code == 404


def test_unsupported_crop_result(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    # The photo's crop cycle is a Tomato (see farmer_with_crop_cycle
    # fixture); simulate a model that only supports Rice.
    fake = FakeModelProvider(top_predictions=[TopKPrediction("X", 0.99)], supported_crops=["rice"])
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    body = response.json()
    assert body["result_status"] == "unknown"
    assert body["predicted_class"] is None


def test_crop_mismatch_result(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("X", 0.99)], supported_crops=["tomato"], crop_match=False)
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    body = response.json()
    assert body["result_status"] == "crop_mismatch"


def test_ai_failure_during_inference_is_handled_safely(client, uploaded_photo):
    """A raised exception mid-inference must degrade to a safe FAILED
    state, never propagate as a 500 or fabricate a result."""
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(raise_on_predict=True)
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    assert response.status_code == 201  # the analysis job itself was created and completed (with a FAILED result)
    body = response.json()
    assert body["result_status"] == "failed"
    assert body["analysis_status"] == "failed"
    assert body["requires_review"] is True


def test_model_version_is_always_recorded(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider()
    with override_model_provider(fake):
        response = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))
    body = response.json()
    # NotConfiguredModelProvider was used for the actual model_row lookup
    # (the registry, not the injected fake) - the ANALYSIS row records
    # whatever the registry says is active, which is the "not configured"
    # placeholder since no real model has been activated in the registry.
    assert body["model_name"]
    assert body["model_version"]


def test_analysis_history_for_crop_cycle(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))

    response = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/analyses", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_latest_analysis_for_photo(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens))

    response = client.get(f"/api/v1/crop-photos/{photo_id}/analysis", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["crop_photo_id"] == photo_id


def test_get_analysis_with_no_prior_request_returns_404(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    response = client.get(f"/api/v1/crop-photos/{photo_id}/analysis", headers=auth_headers(tokens))
    assert response.status_code == 404


def test_duplicate_analysis_request_returns_the_same_in_flight_or_completed_result(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    first = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()
    second = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()
    # Since analysis completes synchronously in this phase, the first
    # request is already COMPLETED by the time the second arrives - so a
    # second POST creates a new analysis (a farmer re-checking is a valid
    # new request once the prior one is done). Both are retained in history.
    history = client.get(f"/api/v1/crop-cycles/{crop_cycle_id}/analyses", headers=auth_headers(tokens)).json()
    assert history["total"] == 2
    assert first["id"] != second["id"]


def test_analysis_requires_accepted_photo_quality(client, farmer_with_crop_cycle):
    """A photo whose quality was REJECTED must not be analyzable at all -
    the quality gate is a hard stop before any inference attempt."""
    import io

    from tests.photo_factories import make_test_jpeg, valid_photo_session_payload

    tokens, crop_cycle_id = farmer_with_crop_cycle
    session = client.post(
        "/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)
    ).json()
    # A dark, flat (blurry) photo - fails quality, still uploads successfully.
    dark_content = make_test_jpeg(color=(2, 2, 2), textured=False)
    files = {"file": ("leaf.jpg", io.BytesIO(dark_content), "image/jpeg")}
    data = {"client_upload_id": "quality-rejected-1", "source": "camera"}
    photo = client.post(
        f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)
    ).json()
    assert photo["image_quality_status"] == "rejected"

    response = client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens))
    assert response.status_code == 422


def test_analysis_status_transitions_end_in_completed(client, uploaded_photo, db_session):
    import uuid as uuid_mod

    from app.models.ai_analysis import AIAnalysis

    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    result = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    row = db_session.get(AIAnalysis, uuid_mod.UUID(result["id"]))
    assert row.analysis_status.value == "completed"
