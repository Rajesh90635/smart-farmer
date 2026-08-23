from app.services.ai_contract import AIAnalysisStatus, AIInferenceService


def test_ai_inference_service_returns_not_implemented():
    service = AIInferenceService()
    result = service.analyze(photo_id="fake-id")
    assert result.status == AIAnalysisStatus.NOT_IMPLEMENTED


def test_ai_inference_service_never_returns_a_disease_or_confidence_field():
    service = AIInferenceService()
    result = service.analyze(photo_id="fake-id")
    # The result type itself has no disease/confidence fields at all -
    # this test documents that guarantee at the type level in addition to
    # the runtime check above.
    assert not hasattr(result, "disease")
    assert not hasattr(result, "confidence")
