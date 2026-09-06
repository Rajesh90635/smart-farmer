"""
Insurance policy service. D74-01 (docs/audit/FINAL_CANONICAL_group_D.md):
entirely farmer-entered/self-reported - no insurer integration exists, so
nothing here is ever verified against a real insurer. crop_id, when
given, must reference a real CropMaster row - never silently stored
unvalidated.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.insurance_policy import InsurancePolicy
from app.repositories import crop_master_repository, insurance_repository
from app.schemas.insurance import InsurancePolicyCreateRequest, InsurancePolicyListResponse, InsurancePolicyResponse
from app.services.audit_logger import AuditLogger


def create_policy(db: Session, farmer_id: str, payload: InsurancePolicyCreateRequest) -> InsurancePolicyResponse:
    if payload.crop_id is not None and crop_master_repository.get_active(db, payload.crop_id) is None:
        raise AppError(error_codes.VALIDATION_ERROR, "Selected crop was not found.", 422)

    policy = InsurancePolicy(
        farmer_id=uuid.UUID(farmer_id),
        crop_id=payload.crop_id,
        policy_number=payload.policy_number,
        insurer=payload.insurer,
        sum_insured=payload.sum_insured,
        premium=payload.premium,
        season=payload.season,
    )
    insurance_repository.create(db, policy)
    AuditLogger(db).log("INSURANCE_POLICY_CREATED", actor_id=farmer_id, actor_role="farmer", entity="insurance_policy", entity_id=str(policy.id))
    db.commit()
    db.refresh(policy)
    return InsurancePolicyResponse.model_validate(policy)


def list_my_policies(db: Session, farmer_id: str) -> InsurancePolicyListResponse:
    policies = insurance_repository.list_for_farmer(db, uuid.UUID(farmer_id))
    return InsurancePolicyListResponse(items=[InsurancePolicyResponse.model_validate(p) for p in policies], total=len(policies))


def get_my_policy(db: Session, farmer_id: str, policy_id: uuid.UUID) -> InsurancePolicyResponse:
    policy = insurance_repository.get_owned(db, policy_id, uuid.UUID(farmer_id))
    if policy is None:
        raise AppError(error_codes.NOT_FOUND, "Insurance policy not found.", 404)
    return InsurancePolicyResponse.model_validate(policy)


def delete_policy(db: Session, farmer_id: str, policy_id: uuid.UUID) -> None:
    policy = insurance_repository.get_owned(db, policy_id, uuid.UUID(farmer_id))
    if policy is None:
        raise AppError(error_codes.NOT_FOUND, "Insurance policy not found.", 404)
    insurance_repository.delete(db, policy)
    AuditLogger(db).log("INSURANCE_POLICY_DELETED", actor_id=farmer_id, actor_role="farmer", entity="insurance_policy", entity_id=str(policy_id))
    db.commit()
