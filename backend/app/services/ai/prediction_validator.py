"""
PredictionValidator: the safety layer between a raw model prediction and
the AIAnalysis record. This is where Requirements 10, 13, 15, and 26 are
actually enforced in code, not just documented as intent.

Decision order (each check is a hard gate - falling through past it means
the earlier condition definitely doesn't apply):
1. Model unavailable -> AI_UNAVAILABLE. Never fabricate a result.
2. Crop not supported by this model -> UNKNOWN. Never claim a disease for
   a crop the model was never trained to recognize.
3. Model explicitly says the photo doesn't match the selected crop ->
   CROP_MISMATCH. Never silently give a same-crop diagnosis anyway.
4. Confidence LOW -> LOW_CONFIDENCE, and predicted_class is NOT surfaced
   as a disease name at this layer (the safety layer knows what the model
   guessed, but callers building farmer-facing text must not name a
   disease when this status is LOW_CONFIDENCE).
5. Otherwise -> HEALTHY or DISEASE_DETECTED, with requires_review set
   whenever confidence is only MEDIUM (never review-free on a guess this
   uncertain).
"""
from dataclasses import dataclass

from app.core.config import Settings
from app.models.ai_analysis import ResultStatus
from app.services.ai.confidence import ConfidenceLevel, classify_confidence
from app.services.ai.model_provider import DiseasePrediction

_HEALTHY_CLASS_NAME = "healthy"


@dataclass(frozen=True)
class SafeAnalysisResult:
    result_status: ResultStatus
    predicted_class: str | None
    confidence: float | None
    requires_review: bool
    top_k_predictions: list[dict]


def validate_disease_prediction(
    prediction: DiseasePrediction,
    *,
    crop_name: str,
    supported_crop_names: list[str],
    settings: Settings,
) -> SafeAnalysisResult:
    if not prediction.available:
        return SafeAnalysisResult(
            result_status=ResultStatus.AI_UNAVAILABLE,
            predicted_class=None,
            confidence=None,
            requires_review=True,
            top_k_predictions=[],
        )

    if crop_name.lower() not in {c.lower() for c in supported_crop_names}:
        return SafeAnalysisResult(
            result_status=ResultStatus.UNKNOWN,
            predicted_class=None,
            confidence=None,
            requires_review=True,
            top_k_predictions=_serialize(prediction.top_predictions),
        )

    if prediction.crop_match is False:
        return SafeAnalysisResult(
            result_status=ResultStatus.CROP_MISMATCH,
            predicted_class=None,
            confidence=None,
            requires_review=True,
            top_k_predictions=_serialize(prediction.top_predictions),
        )

    if not prediction.top_predictions:
        return SafeAnalysisResult(
            result_status=ResultStatus.UNKNOWN,
            predicted_class=None,
            confidence=None,
            requires_review=True,
            top_k_predictions=[],
        )

    top = prediction.top_predictions[0]
    level = classify_confidence(top.confidence, settings)
    top_k_serialized = _serialize(prediction.top_predictions)

    if level == ConfidenceLevel.LOW:
        return SafeAnalysisResult(
            result_status=ResultStatus.LOW_CONFIDENCE,
            predicted_class=None,  # never name a disease at low confidence
            confidence=top.confidence,
            requires_review=True,
            top_k_predictions=top_k_serialized,
        )

    is_healthy = top.class_name.strip().lower() == _HEALTHY_CLASS_NAME
    return SafeAnalysisResult(
        result_status=ResultStatus.HEALTHY if is_healthy else ResultStatus.DISEASE_DETECTED,
        predicted_class=top.class_name,
        confidence=top.confidence,
        requires_review=(level == ConfidenceLevel.MEDIUM),
        top_k_predictions=top_k_serialized,
    )


def _serialize(predictions) -> list[dict]:
    return [{"class_name": p.class_name, "confidence": p.confidence} for p in predictions]
