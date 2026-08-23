"""
Phase 39 endpoints: personalization profile, advisory feedback, learning
summary (ML foundation).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.personalization import (
    AdvisoryFeedbackCreateRequest,
    AdvisoryFeedbackResponse,
    LearningSummaryResponse,
    PersonalizationProfileResponse,
)
from app.services import advisory_feedback_service, learning_foundation_service, personalization_service

router = APIRouter(tags=["personalization"])


@router.get("/farmers/me/personalization", response_model=PersonalizationProfileResponse)
def get_personalization_profile(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> PersonalizationProfileResponse:
    return personalization_service.get_personalization_profile(db, current_user.user_id)


@router.post("/crop-cycles/{crop_cycle_id}/advisory-feedback", response_model=AdvisoryFeedbackResponse, status_code=201)
def submit_advisory_feedback(
    crop_cycle_id: uuid.UUID,
    payload: AdvisoryFeedbackCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> AdvisoryFeedbackResponse:
    return advisory_feedback_service.submit_feedback(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/learning-summary", response_model=LearningSummaryResponse)
def get_learning_summary(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> LearningSummaryResponse:
    return learning_foundation_service.get_learning_summary(db, current_user.user_id, crop_cycle_id)
