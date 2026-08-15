"""
AI analysis session endpoints. Per-photo analysis lives in crop_photos.py
(POST /crop-photos/{id}/analyze etc.) since those routes are photo-scoped;
these are session-scoped (grouping several photos from one crop check).
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.ai_model_dependency import get_model_provider
from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.storage_dependency import get_file_storage
from app.db.session import get_db
from app.schemas.ai_analysis import AIAnalysisSessionCreateRequest, AIAnalysisSessionResponse
from app.services import ai_analysis_session_service
from app.services.ai.model_provider import ModelProvider
from app.services.storage.base import FileStorage

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/sessions", response_model=AIAnalysisSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: AIAnalysisSessionCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> AIAnalysisSessionResponse:
    return ai_analysis_session_service.create_analysis_session(db, current_user.user_id, payload)


@router.get("/sessions/{session_id}", response_model=AIAnalysisSessionResponse)
def get_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> AIAnalysisSessionResponse:
    return ai_analysis_session_service.get_analysis_session(db, current_user.user_id, session_id)


@router.post("/sessions/{session_id}/analyze", response_model=AIAnalysisSessionResponse)
def analyze_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    model_provider: ModelProvider = Depends(get_model_provider),
    storage: FileStorage = Depends(get_file_storage),
    settings: Settings = Depends(get_settings),
) -> AIAnalysisSessionResponse:
    return ai_analysis_session_service.analyze_session(db, current_user.user_id, session_id, model_provider, storage, settings)


@router.get("/analysis/{analysis_id}")
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
):
    from app.services import ai_analysis_service

    return ai_analysis_service.get_analysis(db, current_user.user_id, analysis_id)


@router.get("/analysis/{analysis_id}/localized")
def get_localized_analysis(
    analysis_id: uuid.UUID,
    language: str | None = None,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
):
    """Renders an AIAnalysis into farmer-friendly, localized text -
    never raw AI output. Defaults to the farmer's own
    preferred_language_code (from FarmerProfile, Prompt 3) if no
    `language` query param is given."""
    from app.repositories import user_repository
    from app.services import ai_result_localization_service

    if language is None:
        farmer_user = user_repository.get_by_id(db, uuid.UUID(current_user.user_id))
        language = farmer_user.farmer_profile.preferred_language_code if farmer_user and farmer_user.farmer_profile else "en"

    return ai_result_localization_service.get_localized_analysis(db, current_user.user_id, analysis_id, language)


@router.get("/languages")
def list_supported_languages():
    """Reuses the existing localization whitelist (app/core/localization.py,
    established in Prompt 2) - not a new/duplicate language list."""
    from app.core.localization import SUPPORTED_LANGUAGE_CODES

    return {"languages": sorted(SUPPORTED_LANGUAGE_CODES)}
