"""
Professional registration and verification. Registering NEVER sets
verification_status to VERIFIED - it always starts PENDING, and only an
explicit admin action (verify/reject/suspend/reactivate) can change it -
this is what makes "no fake verification" and "professionals cannot
self-verify" actually true in code, not just policy.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.core.roles import Role
from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
from app.models.verification_record import VerificationAction, VerificationRecord
from app.repositories import professional_repository
from app.schemas.professional import (
    AvailabilityUpdateRequest,
    ProfessionalListResponse,
    ProfessionalProfileResponse,
    ProfessionalRegisterRequest,
    VerificationActionRequest,
)
from app.services.audit_logger import AuditLogger

_PROFESSIONAL_ROLES = {Role.FIELD_AGENT.value, Role.EXPERT.value, Role.TRADER.value, Role.DEALER.value}


def register_professional(db: Session, user_id: str, payload: ProfessionalRegisterRequest) -> ProfessionalProfileResponse:
    if payload.role not in _PROFESSIONAL_ROLES:
        raise AppError(error_codes.VALIDATION_ERROR, f"'{payload.role}' is not a valid professional role.", 422)

    user_uuid = uuid.UUID(user_id)
    if professional_repository.get_by_user_id(db, user_uuid) is not None:
        raise AppError(error_codes.DUPLICATE_ACCOUNT, "A professional profile already exists for this account.", 409)

    profile = ProfessionalProfile(
        user_id=user_uuid,
        role=payload.role,
        display_name=payload.display_name,
        organization=payload.organization,
        qualification=payload.qualification,
        experience_years=payload.experience_years,
        language_codes=payload.language_codes,
        crop_specialization_ids=[str(c) for c in payload.crop_specialization_ids],
        disease_specialization_categories=payload.disease_specialization_categories,
        service_area=payload.service_area.model_dump() if payload.service_area else None,
        verification_status=VerificationStatus.PENDING,
        availability_status=AvailabilityStatus.OFFLINE,
    )
    professional_repository.create(db, profile)
    db.flush()

    AuditLogger(db).log("PROFESSIONAL_REGISTERED", actor_id=user_id, actor_role=payload.role, entity="professional_profile", entity_id=str(profile.id))

    db.commit()
    db.refresh(profile)
    return ProfessionalProfileResponse.model_validate(profile)


def get_my_profile(db: Session, user_id: str) -> ProfessionalProfileResponse:
    profile = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if profile is None:
        raise AppError(error_codes.NOT_FOUND, "No professional profile found for this account.", 404)
    return ProfessionalProfileResponse.model_validate(profile)


def update_my_availability(db: Session, user_id: str, payload: AvailabilityUpdateRequest) -> ProfessionalProfileResponse:
    profile = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if profile is None:
        raise AppError(error_codes.NOT_FOUND, "No professional profile found for this account.", 404)

    profile.availability_status = payload.availability_status
    db.commit()
    db.refresh(profile)
    return ProfessionalProfileResponse.model_validate(profile)


def get_professional_public(db: Session, professional_id: uuid.UUID) -> ProfessionalProfileResponse:
    profile = professional_repository.get_by_id(db, professional_id)
    if profile is None:
        raise AppError(error_codes.NOT_FOUND, "Professional not found.", 404)
    return ProfessionalProfileResponse.model_validate(profile)


def list_verified_professionals(db: Session, role: str, *, limit: int = 50, offset: int = 0) -> ProfessionalListResponse:
    items, total = professional_repository.list_verified_by_role(db, role, limit=limit, offset=offset)
    return ProfessionalListResponse(items=[ProfessionalProfileResponse.model_validate(p) for p in items], total=total)


def _apply_verification_action(
    db: Session, admin_user_id: str, professional_id: uuid.UUID, action: VerificationAction, new_status: VerificationStatus, payload: VerificationActionRequest
) -> ProfessionalProfileResponse:
    profile = professional_repository.get_by_id(db, professional_id)
    if profile is None:
        raise AppError(error_codes.NOT_FOUND, "Professional not found.", 404)

    profile.verification_status = new_status

    record = VerificationRecord(
        professional_id=profile.id,
        action=action,
        performed_by_admin_id=uuid.UUID(admin_user_id),
        reason=payload.reason,
    )
    professional_repository.create_verification_record(db, record)

    AuditLogger(db).log(
        f"PROFESSIONAL_{action.value.upper()}", actor_id=admin_user_id, actor_role="admin", entity="professional_profile", entity_id=str(profile.id)
    )

    db.commit()
    db.refresh(profile)
    return ProfessionalProfileResponse.model_validate(profile)


def admin_verify(db: Session, admin_user_id: str, professional_id: uuid.UUID, payload: VerificationActionRequest) -> ProfessionalProfileResponse:
    return _apply_verification_action(db, admin_user_id, professional_id, VerificationAction.VERIFY, VerificationStatus.VERIFIED, payload)


def admin_reject(db: Session, admin_user_id: str, professional_id: uuid.UUID, payload: VerificationActionRequest) -> ProfessionalProfileResponse:
    return _apply_verification_action(db, admin_user_id, professional_id, VerificationAction.REJECT, VerificationStatus.REJECTED, payload)


def admin_suspend(db: Session, admin_user_id: str, professional_id: uuid.UUID, payload: VerificationActionRequest) -> ProfessionalProfileResponse:
    return _apply_verification_action(db, admin_user_id, professional_id, VerificationAction.SUSPEND, VerificationStatus.SUSPENDED, payload)


def admin_reactivate(db: Session, admin_user_id: str, professional_id: uuid.UUID, payload: VerificationActionRequest) -> ProfessionalProfileResponse:
    return _apply_verification_action(db, admin_user_id, professional_id, VerificationAction.REACTIVATE, VerificationStatus.VERIFIED, payload)
