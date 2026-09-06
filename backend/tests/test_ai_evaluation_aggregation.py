"""D91-09/D91-10 (docs/audit/FINAL_CANONICAL_group_D.md)."""
import io
import uuid

from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from tests.photo_factories import make_test_jpeg, valid_photo_session_payload
from app.services.ai.model_provider import TopKPrediction


def _analyze(client, tokens, crop_cycle_id, top_predictions, *, supported_crops=("tomato",)):
    session = client.post("/api/v1/crop-photo-sessions", json=valid_photo_session_payload(crop_cycle_id), headers=auth_headers(tokens)).json()
    files = {"file": ("leaf.jpg", io.BytesIO(make_test_jpeg()), "image/jpeg")}
    data = {"client_upload_id": f"upload-{uuid.uuid4().hex[:8]}", "source": "camera"}
    photo = client.post(f"/api/v1/crop-photo-sessions/{session['id']}/photos", files=files, data=data, headers=auth_headers(tokens)).json()
    with override_model_provider(FakeModelProvider(top_predictions=top_predictions, supported_crops=list(supported_crops))):
        return client.post(f"/api/v1/crop-photos/{photo['id']}/analyze", headers=auth_headers(tokens)).json()


def test_aggregate_correctly_separates_false_positive_from_false_negative_corrections(
    client, farmer_with_crop_cycle, admin_tokens
):
    tokens, crop_cycle_id = farmer_with_crop_cycle

    # A false positive: AI said diseased, farmer says actually healthy.
    fp_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Early Blight", 0.90)])
    assert fp_analysis["result_status"] == "disease_detected"
    client.post(
        f"/api/v1/ai/analysis/{fp_analysis['id']}/correction", json={"correction": "actually_healthy"}, headers=auth_headers(tokens)
    )

    # A false negative: AI said healthy, farmer says actually diseased.
    fn_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Healthy", 0.95)])
    assert fn_analysis["result_status"] == "healthy"
    client.post(
        f"/api/v1/ai/analysis/{fn_analysis['id']}/correction", json={"correction": "actually_diseased"}, headers=auth_headers(tokens)
    )

    # A confirmed-correct disease call - must not be counted as either.
    confirmed_analysis = _analyze(client, tokens, crop_cycle_id, [TopKPrediction("Late Blight", 0.93)])
    client.post(
        f"/api/v1/ai/analysis/{confirmed_analysis['id']}/correction", json={"correction": "confirmed_correct"}, headers=auth_headers(tokens)
    )

    response = client.get("/api/v1/ai/evaluation/correction-aggregate", headers=auth_headers(admin_tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["false_positive_count"] >= 1
    assert body["false_negative_count"] >= 1
    assert body["confirmed_correct_count"] >= 1
    assert body["total_disease_detected"] >= body["false_positive_count"]
    assert body["total_healthy"] >= body["false_negative_count"]
    assert 0 <= body["false_positive_rate"] <= 1
    assert 0 <= body["false_negative_rate"] <= 1


def test_aggregate_rate_is_none_not_a_fabricated_zero_when_no_analyses_of_that_type_exist(client, admin_tokens):
    """A brand-new environment (or one where this specific result type
    genuinely never occurred) must report None, never a fake 0%."""
    response = client.get("/api/v1/ai/evaluation/correction-aggregate", headers=auth_headers(admin_tokens))
    assert response.status_code == 200
    body = response.json()
    if body["total_disease_detected"] == 0:
        assert body["false_positive_rate"] is None
    if body["total_healthy"] == 0:
        assert body["false_negative_rate"] is None


def test_correction_aggregate_requires_admin_role(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/ai/evaluation/correction-aggregate", headers=auth_headers(tokens))
    assert response.status_code == 403
