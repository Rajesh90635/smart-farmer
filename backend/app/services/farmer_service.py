import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.farmer_profile import FarmerProfile
from app.models.user import AccountStatus
from app.repositories import refresh_token_repository, user_repository
from app.schemas.farmer import FarmerProfileResponse, FarmerProfileUpdateRequest
from app.services.audit_logger import AuditLogger


def _to_response(user_id: uuid.UUID, profile: FarmerProfile, status, phone_number: str, created_at) -> FarmerProfileResponse:
    return FarmerProfileResponse(
        user_id=user_id,
        phone_number=phone_number,
        full_name=profile.full_name,
        preferred_language_code=profile.preferred_language_code,
        preferred_voice_language_code=profile.preferred_voice_language_code,
        status=status,
        created_at=created_at,
    )


def get_profile(db: Session, user_id: str) -> FarmerProfileResponse:
    user = user_repository.get_by_id(db, uuid.UUID(user_id))
    if user is None or user.farmer_profile is None:
        raise AppError(error_codes.NOT_FOUND, "Farmer profile not found.", 404)

    return _to_response(user.id, user.farmer_profile, user.status, user.phone_number, user.created_at)


def update_profile(db: Session, user_id: str, payload: FarmerProfileUpdateRequest) -> FarmerProfileResponse:
    user = user_repository.get_by_id(db, uuid.UUID(user_id))
    if user is None or user.farmer_profile is None:
        raise AppError(error_codes.NOT_FOUND, "Farmer profile not found.", 404)

    profile = user.farmer_profile
    if payload.full_name is not None:
        profile.full_name = payload.full_name
    if payload.preferred_language_code is not None:
        profile.preferred_language_code = payload.preferred_language_code
    if payload.preferred_voice_language_code is not None:
        profile.preferred_voice_language_code = payload.preferred_voice_language_code

    AuditLogger(db).log("PROFILE_UPDATED", actor_id=user_id, actor_role="farmer", entity="user", entity_id=user_id)

    db.commit()
    db.refresh(profile)
    return _to_response(user.id, profile, user.status, user.phone_number, user.created_at)


def deactivate_own_account(db: Session, user_id: str) -> None:
    """D1-19 (docs/audit/FINAL_CANONICAL_group_A.md): a softer, reversible
    sibling of D100-09's delete-account flow - AccountStatus.INACTIVE is
    already correctly enforced at login (auth_service.py), it just had no
    self-service path to set it before now. Deliberately does NOT require
    password re-confirmation: D100-09's own delete-account (a strictly
    more destructive, harder-to-reverse action on the same account) sets
    this exact same precedent already - requiring re-confirmation only
    for the softer sibling would be an inconsistent, not a safer, design.
    Unlike delete-account, this does NOT scrub PII - reactivation (a
    farmer contacting support, or a future self-service reactivate
    endpoint) should be able to restore the account as-is."""
    farmer_uuid = uuid.UUID(user_id)
    user = user_repository.get_by_id(db, farmer_uuid)
    if user is None:
        raise AppError(error_codes.NOT_FOUND, "Account not found.", 404)
    if user.status == AccountStatus.INACTIVE:
        raise AppError(error_codes.VALIDATION_ERROR, "This account is already deactivated.", 409)

    user.status = AccountStatus.INACTIVE
    refresh_token_repository.revoke_all_for_user(db, farmer_uuid)

    AuditLogger(db).log("ACCOUNT_DEACTIVATED", actor_id=user_id, actor_role="farmer", entity="user", entity_id=user_id)
    db.commit()
