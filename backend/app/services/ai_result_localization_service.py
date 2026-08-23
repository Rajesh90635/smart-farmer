"""
AI result localization: AI result -> structured disease data ->
localization service -> farmer-friendly text -> (TTS happens client-side,
see docs/VOICE_AUDIO.md) -> display/play.

Never blindly translates raw AI output - every field is built from
STRUCTURED data (result_status, predicted_class, confidence) through the
same template system used for weather alerts, never a free-form AI
sentence passed through a translation call.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.farmer_messages import get_message
from app.models.ai_analysis import AIAnalysis, ResultStatus
from app.models.crop_master import CropMaster
from app.models.disease_class import DiseaseClass
from app.repositories import ai_analysis_repository
from app.schemas.farmer_friendly_result import FarmerFriendlyAnalysisResponse
from app.services.ai.confidence import ConfidenceLevel, classify_confidence

_CONFIDENCE_WORDING = {
    ConfidenceLevel.HIGH: {"en": "We are fairly confident about this."},
    ConfidenceLevel.MEDIUM: {"en": "We are somewhat confident - a second photo may help confirm this."},
}

_RESULT_MESSAGE_KEY = {
    ResultStatus.HEALTHY: "ai_result_healthy",
    ResultStatus.DISEASE_DETECTED: "ai_result_disease_detected",
    ResultStatus.UNKNOWN: "ai_result_unknown",
    ResultStatus.LOW_CONFIDENCE: "ai_result_low_confidence",
    ResultStatus.CROP_MISMATCH: "ai_result_crop_mismatch",
    ResultStatus.AI_UNAVAILABLE: "ai_result_ai_unavailable",
    ResultStatus.FAILED: "ai_result_failed",
    ResultStatus.PROCESSING: "ai_result_ai_unavailable",
}


def get_localized_analysis(db: Session, farmer_id: str, analysis_id: uuid.UUID, language_code: str) -> FarmerFriendlyAnalysisResponse:
    analysis = ai_analysis_repository.get_analysis_owned(db, analysis_id, uuid.UUID(farmer_id))
    if analysis is None:
        raise AppError(error_codes.NOT_FOUND, "Analysis not found.", 404)

    return localize_analysis(db, analysis, language_code)


def localize_analysis(db: Session, analysis: AIAnalysis, language_code: str) -> FarmerFriendlyAnalysisResponse:
    settings = get_settings()

    crop_name = None
    if analysis.crop_id:
        crop = db.get(CropMaster, analysis.crop_id)
        crop_name = crop.name if crop else None

    disease_display_name = analysis.predicted_class
    if analysis.predicted_class and analysis.crop_id:
        disease_rows = db.execute(select(DiseaseClass).where(DiseaseClass.crop_id == analysis.crop_id)).scalars().all()
        match = next((d for d in disease_rows if d.disease_name.lower() == analysis.predicted_class.lower()), None)
        if match and match.local_names and language_code in match.local_names:
            disease_display_name = match.local_names[language_code]

    message_key = _RESULT_MESSAGE_KEY[analysis.result_status]
    params = {}
    if analysis.result_status == ResultStatus.HEALTHY:
        params = {"crop_name": crop_name or "crop"}
    elif analysis.result_status == ResultStatus.DISEASE_DETECTED:
        params = {"disease_name": disease_display_name or "a problem", "crop_name": crop_name or "crop"}

    title = get_message(message_key, language_code, **params)

    confidence_wording = None
    if analysis.confidence is not None:
        level = classify_confidence(analysis.confidence, settings)
        wording_templates = _CONFIDENCE_WORDING.get(level)
        if wording_templates:
            confidence_wording = wording_templates.get(language_code) or wording_templates.get("en")

    next_action = None
    if analysis.result_status in (ResultStatus.UNKNOWN, ResultStatus.LOW_CONFIDENCE, ResultStatus.CROP_MISMATCH):
        next_action = get_message("ai_next_action_retake", language_code)
    elif analysis.requires_review:
        next_action = get_message("ai_next_action_review", language_code)

    audio_parts = [title]
    if confidence_wording:
        audio_parts.append(confidence_wording)
    if next_action:
        audio_parts.append(next_action)

    return FarmerFriendlyAnalysisResponse(
        analysis_id=analysis.id,
        language_code=language_code,
        result_status=analysis.result_status,
        title=title,
        confidence_wording=confidence_wording,
        next_action=next_action,
        audio_text=" ".join(audio_parts),
    )
