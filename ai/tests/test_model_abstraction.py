import pytest

from app.model_abstraction import InferenceService, NotImplementedModelProvider


def test_not_implemented_provider_reports_not_ready():
    provider = NotImplementedModelProvider("crop_disease_vision")
    assert provider.is_ready() is False


def test_not_implemented_provider_raises_on_predict_rather_than_faking_a_result():
    provider = NotImplementedModelProvider("crop_disease_vision")
    with pytest.raises(NotImplementedError):
        provider.predict(b"fake-image-bytes")


def test_inference_service_health_shape():
    service = InferenceService(NotImplementedModelProvider("llm_explanation"))
    health = service.health()
    assert health["ready"] is False
    assert health["model"]["name"] == "llm_explanation"
