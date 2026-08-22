"""
Phase 34 endpoints: treatment records, follow-ups, effectiveness.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.treatment import (
    EffectivenessResponse,
    FollowUpCreateRequest,
    FollowUpListResponse,
    FollowUpResponse,
    TreatmentCreateRequest,
    TreatmentListResponse,
    TreatmentResponse,
)
from app.services import treatment_service

router = APIRouter(tags=["treatments"])


@router.post("/crop-cycles/{crop_cycle_id}/treatments", response_model=TreatmentResponse, status_code=201)
def create_treatment(
    crop_cycle_id: uuid.UUID,
    payload: TreatmentCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> TreatmentResponse:
    return treatment_service.create_treatment(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/treatments", response_model=TreatmentListResponse)
def list_treatments(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> TreatmentListResponse:
    return treatment_service.list_treatments(db, current_user.user_id, crop_cycle_id)


@router.post("/treatments/{treatment_id}/follow-ups", response_model=FollowUpResponse, status_code=201)
def create_follow_up(
    treatment_id: uuid.UUID,
    payload: FollowUpCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FollowUpResponse:
    return treatment_service.create_follow_up(db, current_user.user_id, treatment_id, payload)


@router.get("/treatments/{treatment_id}/follow-ups", response_model=FollowUpListResponse)
def list_follow_ups(
    treatment_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> FollowUpListResponse:
    return treatment_service.list_follow_ups(db, current_user.user_id, treatment_id)


@router.get("/treatments/{treatment_id}/effectiveness", response_model=EffectivenessResponse)
def get_effectiveness(
    treatment_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> EffectivenessResponse:
    return treatment_service.get_effectiveness(db, current_user.user_id, treatment_id)
