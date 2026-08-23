"""
AI analysis session: groups analyses across a CropPhotoSession's photos
(Requirement 20/21). Each photo is analyzed independently through the same
`ai_analysis_service.analyze_photo` pipeline - no combined/fused diagnosis
is computed, since no model capable of real multi-image fusion exists.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.ai_analysis_session import AIAnalysisSession
from app.repositories import ai_analysis_repository, crop_photo_repository, crop_photo_session_repository
from app.schemas.ai_analysis import AIAnalysisResponse, AIAnalysisSessionCreateRequest, AIAnalysisSessionResponse
from app.services import ai_analysis_service
from app.services.ai.model_provider import ModelProvider
from app.services.audit_logger import AuditLogger
from app.services.storage.base import FileStorage


def create_analysis_session(db: Session, farmer_id: str, payload: AIAnalysisSessionCreateRequest) -> AIAnalysisSessionResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    photo_session = crop_photo_session_repository.get_owned(db, payload.crop_photo_session_id, farmer_uuid)
    if photo_session is None:
        raise AppError(error_codes.NOT_FOUND, "Photo session not found.", 404)

    session_obj = AIAnalysisSession(
        crop_photo_session_id=photo_session.id,
        farmer_id=farmer_uuid,
        crop_cycle_id=photo_session.crop_cycle_id,
    )
    db.add(session_obj)
    db.flush()

    AuditLogger(db).log(
        "AI_ANALYSIS_SESSION_CREATED", actor_id=farmer_id, actor_role="farmer", entity="ai_analysis_session", entity_id=str(session_obj.id)
    )
    db.commit()
    db.refresh(session_obj)
    return AIAnalysisSessionResponse.model_validate(session_obj)


def get_analysis_session(db: Session, farmer_id: str, session_id: uuid.UUID) -> AIAnalysisSessionResponse:
    session_obj = _get_owned_or_404(db, farmer_id, session_id)
    analyses = ai_analysis_repository.list_for_session(db, session_id)
    response = AIAnalysisSessionResponse.model_validate(session_obj)
    response.analyses = [AIAnalysisResponse.model_validate(a) for a in analyses]
    return response


def analyze_session(
    db: Session,
    farmer_id: str,
    session_id: uuid.UUID,
    model_provider: ModelProvider,
    storage: FileStorage,
    settings: Settings,
) -> AIAnalysisSessionResponse:
    session_obj = _get_owned_or_404(db, farmer_id, session_id)

    photos = crop_photo_repository.list_for_session(db, session_obj.crop_photo_session_id)
    results = []
    for photo in photos:
        result = ai_analysis_service.analyze_photo(
            db, farmer_id, photo.id, model_provider, storage, settings, analysis_session_id=session_obj.id
        )
        results.append(result)

    response = AIAnalysisSessionResponse.model_validate(session_obj)
    response.analyses = results
    return response


def _get_owned_or_404(db: Session, farmer_id: str, session_id: uuid.UUID) -> AIAnalysisSession:
    session_obj = ai_analysis_repository.get_session_owned(db, session_id, uuid.UUID(farmer_id))
    if session_obj is None:
        raise AppError(error_codes.NOT_FOUND, "AI analysis session not found.", 404)
    return session_obj
