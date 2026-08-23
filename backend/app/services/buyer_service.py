"""
Buyer registration: creates a ProfessionalProfile (role='buyer', reused
from Prompt 8 unchanged - same PENDING-by-default, admin-only
verification workflow) plus a BuyerBusinessProfile extension for
buyer-specific fields. No second verification system.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.core.roles import Role
from app.models.buyer_business_profile import BuyerBusinessProfile
from app.models.professional_profile import AvailabilityStatus, ProfessionalProfile, VerificationStatus
from app.repositories import buyer_offer_repository, professional_repository
from app.schemas.marketplace import BuyerProfileRegisterRequest, BuyerProfileResponse
from app.services.audit_logger import AuditLogger


def register_buyer(db: Session, user_id: str, payload: BuyerProfileRegisterRequest) -> BuyerProfileResponse:
    user_uuid = uuid.UUID(user_id)
    if professional_repository.get_by_user_id(db, user_uuid) is not None:
        raise AppError(error_codes.DUPLICATE_ACCOUNT, "A professional/buyer profile already exists for this account.", 409)

    profile = ProfessionalProfile(
        user_id=user_uuid,
        role=Role.BUYER.value,
        display_name=payload.display_name,
        service_area=payload.service_area,
        verification_status=VerificationStatus.PENDING,
        availability_status=AvailabilityStatus.OFFLINE,
    )
    professional_repository.create(db, profile)
    db.flush()

    business_profile = BuyerBusinessProfile(
        professional_id=profile.id,
        buyer_type=payload.buyer_type,
        crops_purchased=[str(c) for c in payload.crops_purchased],
        quality_requirements=payload.quality_requirements,
        min_quantity=payload.min_quantity,
        max_quantity=payload.max_quantity,
        purchase_frequency=payload.purchase_frequency,
        collection_method=payload.collection_method,
    )
    buyer_offer_repository.create_buyer_business_profile(db, business_profile)

    AuditLogger(db).log("BUYER_REGISTERED", actor_id=user_id, actor_role="buyer", entity="professional_profile", entity_id=str(profile.id))
    db.commit()
    db.refresh(profile)
    db.refresh(business_profile)

    return _to_response(profile, business_profile)


def get_my_buyer_profile(db: Session, user_id: str) -> BuyerProfileResponse:
    profile = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if profile is None or profile.role != Role.BUYER.value:
        raise AppError(error_codes.NOT_FOUND, "No buyer profile found for this account.", 404)
    business_profile = buyer_offer_repository.get_buyer_business_profile(db, profile.id)
    return _to_response(profile, business_profile)


def _to_response(profile: ProfessionalProfile, business_profile: BuyerBusinessProfile) -> BuyerProfileResponse:
    return BuyerProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        verification_status=profile.verification_status.value,
        buyer_type=business_profile.buyer_type,
        crops_purchased=business_profile.crops_purchased,
        min_quantity=business_profile.min_quantity,
        max_quantity=business_profile.max_quantity,
        collection_method=business_profile.collection_method,
    )
