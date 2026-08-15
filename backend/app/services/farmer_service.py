import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.farmer_profile import FarmerProfile
from app.repositories import user_repository
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
