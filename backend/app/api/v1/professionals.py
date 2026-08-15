"""
Professional profile + admin verification endpoints. Reuses the existing
auth/RBAC system - not a second authentication system.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.professional import (
    AvailabilityUpdateRequest,
    ProfessionalListResponse,
    ProfessionalProfileResponse,
    ProfessionalRegisterRequest,
    VerificationActionRequest,
)
from app.services import professional_service

router = APIRouter(prefix="/professionals", tags=["professionals"])

_PROFESSIONAL_ROLES = (Role.FIELD_AGENT.value, Role.EXPERT.value, Role.TRADER.value, Role.DEALER.value)


@router.post("", response_model=ProfessionalProfileResponse, status_code=status.HTTP_201_CREATED)
def register_professional(
    payload: ProfessionalRegisterRequest,
    current_user: CurrentUser = Depends(require_role(*_PROFESSIONAL_ROLES)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.register_professional(db, current_user.user_id, payload)


@router.get("/me", response_model=ProfessionalProfileResponse)
def get_my_professional_profile(
    current_user: CurrentUser = Depends(require_role(*_PROFESSIONAL_ROLES)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.get_my_profile(db, current_user.user_id)


@router.put("/me/availability", response_model=ProfessionalProfileResponse)
def update_my_availability(
    payload: AvailabilityUpdateRequest,
    current_user: CurrentUser = Depends(require_role(*_PROFESSIONAL_ROLES)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.update_my_availability(db, current_user.user_id, payload)


@router.get("", response_model=ProfessionalListResponse)
def list_professionals(
    role: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value, Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProfessionalListResponse:
    """Only VERIFIED professionals are ever listed here - see
    professional_repository.list_verified_by_role. A farmer can browse
    verified professionals; the full unrestricted directory (including
    pending/rejected) is admin-only via a different mechanism (not built
    this phase beyond the verification actions below)."""
    return professional_service.list_verified_professionals(db, role, limit=limit, offset=offset)


@router.get("/{professional_id}", response_model=ProfessionalProfileResponse)
def get_professional(
    professional_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value, Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.get_professional_public(db, professional_id)


@router.post("/{professional_id}/verify", response_model=ProfessionalProfileResponse)
def verify_professional(
    professional_id: uuid.UUID,
    payload: VerificationActionRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.admin_verify(db, current_user.user_id, professional_id, payload)


@router.post("/{professional_id}/reject", response_model=ProfessionalProfileResponse)
def reject_professional(
    professional_id: uuid.UUID,
    payload: VerificationActionRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.admin_reject(db, current_user.user_id, professional_id, payload)


@router.post("/{professional_id}/suspend", response_model=ProfessionalProfileResponse)
def suspend_professional(
    professional_id: uuid.UUID,
    payload: VerificationActionRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.admin_suspend(db, current_user.user_id, professional_id, payload)


@router.post("/{professional_id}/reactivate", response_model=ProfessionalProfileResponse)
def reactivate_professional(
    professional_id: uuid.UUID,
    payload: VerificationActionRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN.value)),
    db: Session = Depends(get_db),
) -> ProfessionalProfileResponse:
    return professional_service.admin_reactivate(db, current_user.user_id, professional_id, payload)
