from tests.conftest import auth_headers, override_model_provider
from tests.fake_model_provider import FakeModelProvider
from app.services.ai.model_provider import TopKPrediction


def test_localized_analysis_for_ai_unavailable(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/ai/analysis/{analysis['id']}/localized", headers=auth_headers(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["language_code"] == "en"  # default from farmer's preferred_language_code
    assert "try again" in body["title"].lower()
    assert body["audio_text"]  # never empty


def test_localized_analysis_for_healthy_result(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Healthy", 0.95)], supported_crops=["tomato"])
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/ai/analysis/{analysis['id']}/localized", headers=auth_headers(tokens))
    body = response.json()
    assert "healthy" in body["title"].lower()
    assert "tomato" in body["title"].lower()


def test_localized_analysis_for_disease_detected_uses_local_name_if_available(client, uploaded_photo, db_session):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.95)], supported_crops=["tomato"])
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/ai/analysis/{analysis['id']}/localized?language=hi", headers=auth_headers(tokens))
    body = response.json()
    # "Early Blight" was seeded with a Hindi local_names entry in the
    # Prompt 6 migration - confirms the localization bridge actually
    # queries DiseaseClass.local_names, not just the raw English string.
    assert "Early Blight" not in body["title"]


def test_localized_analysis_never_names_disease_at_low_confidence(client, uploaded_photo):
    tokens, crop_cycle_id, photo_id, _ = uploaded_photo
    fake = FakeModelProvider(top_predictions=[TopKPrediction("Early Blight", 0.20)], supported_crops=["tomato"])
    with override_model_provider(fake):
        analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens)).json()

    response = client.get(f"/api/v1/ai/analysis/{analysis['id']}/localized", headers=auth_headers(tokens)).json()
    assert "Early Blight" not in response["title"]
    assert "clearer photo" in response["title"].lower()


def test_localized_analysis_ownership_enforced(client, uploaded_photo, another_farmer):
    tokens_a, crop_cycle_id, photo_id, _ = uploaded_photo
    _, tokens_b = another_farmer
    analysis = client.post(f"/api/v1/crop-photos/{photo_id}/analyze", headers=auth_headers(tokens_a)).json()

    response = client.get(f"/api/v1/ai/analysis/{analysis['id']}/localized", headers=auth_headers(tokens_b))
    assert response.status_code == 404


def test_supported_languages_endpoint(client, registered_farmer):
    _, tokens = registered_farmer
    response = client.get("/api/v1/ai/languages", headers=auth_headers(tokens))
    assert response.status_code == 200
    languages = response.json()["languages"]
    assert "en" in languages
    assert "hi" in languages
    assert "ml" in languages
