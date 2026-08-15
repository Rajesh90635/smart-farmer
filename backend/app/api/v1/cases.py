"""
CropHealthCase endpoints - farmer-initiated creation/management,
professional accept/decline/review, plus the case-scoped audit trail
(reusing the existing generic AuditLog, not a new table).
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.case import (
    CaseAssignmentResponse,
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseReviewCreateRequest,
    CaseReviewResponse,
    FeedbackCreateRequest,
    SecondOpinionRequest,
)
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["cases"])

_PROFESSIONAL_ROLES = (Role.FIELD_AGENT.value, Role.EXPERT.value)


@router.post("", response_model=CaseResponse, status_code=201)
def create_case(
    payload: CaseCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CaseResponse:
    return case_service.create_case(db, current_user.user_id, payload, settings)


@router.get("", response_model=CaseListResponse)
def list_my_cases(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CaseListResponse:
    return case_service.list_my_cases(db, current_user.user_id, limit=limit, offset=offset)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CaseResponse:
    return case_service.get_my_case(db, current_user.user_id, case_id)


@router.post("/{case_id}/accept", response_model=CaseAssignmentResponse)
def accept_case(
    case_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(*_PROFESSIONAL_ROLES)),
    db: Session = Depends(get_db),
) -> CaseAssignmentResponse:
    return case_service.accept_case(db, current_user.user_id, case_id)


@router.post("/{case_id}/decline", response_model=CaseAssignmentResponse)
def decline_case(
    case_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(*_PROFESSIONAL_ROLES)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CaseAssignmentResponse:
    return case_service.decline_case(db, current_user.user_id, case_id, settings)


@router.post("/{case_id}/review", response_model=CaseReviewResponse)
def submit_review(
    case_id: uuid.UUID,
    payload: CaseReviewCreateRequest,
    current_user: CurrentUser = Depends(require_role(*_PROFESSIONAL_ROLES)),
    db: Session = Depends(get_db),
) -> CaseReviewResponse:
    return case_service.submit_review(db, current_user.user_id, case_id, payload)


@router.post("/{case_id}/close", response_model=CaseResponse)
def close_case(
    case_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CaseResponse:
    return case_service.close_case(db, current_user.user_id, case_id)


@router.post("/{case_id}/second-opinion", response_model=CaseResponse)
def request_second_opinion(
    case_id: uuid.UUID,
    payload: SecondOpinionRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CaseResponse:
    return case_service.request_second_opinion(db, current_user.user_id, case_id, payload, settings)


@router.post("/{case_id}/feedback", status_code=204)
def submit_feedback(
    case_id: uuid.UUID,
    payload: FeedbackCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    case_service.submit_feedback(db, current_user.user_id, case_id, payload)


@router.get("/{case_id}/audit")
def get_case_audit(
    case_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Reuses the existing generic AuditLog table (entity='crop_health_case')
    rather than a new CaseAudit table - filtered to cases the caller owns."""
    from sqlalchemy import select

    from app.core import error_codes
    from app.core.errors import AppError
    from app.models.audit_log import AuditLog
    from app.repositories import case_repository

    case = case_repository.get_case_owned_by_farmer(db, case_id, uuid.UUID(current_user.user_id))
    if case is None:
        raise AppError(error_codes.NOT_FOUND, "Case not found.", 404)

    rows = db.execute(
        select(AuditLog).where(AuditLog.entity == "crop_health_case", AuditLog.entity_id == str(case_id)).order_by(AuditLog.occurred_at_utc.asc())
    ).scalars().all()
    return [
        {"action": r.action, "actor_role": r.actor_role, "occurred_at": r.occurred_at_utc.isoformat()}
        for r in rows
    ]
