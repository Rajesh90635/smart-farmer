"""
Insurance policy endpoints - D74-01 (docs/audit/FINAL_CANONICAL_group_D.md).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.insurance import InsurancePolicyCreateRequest, InsurancePolicyListResponse, InsurancePolicyResponse
from app.services import insurance_service

router = APIRouter(tags=["insurance"])


@router.post("/farmers/me/insurance-policies", response_model=InsurancePolicyResponse, status_code=201)
def create_insurance_policy(
    payload: InsurancePolicyCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InsurancePolicyResponse:
    return insurance_service.create_policy(db, current_user.user_id, payload)


@router.get("/farmers/me/insurance-policies", response_model=InsurancePolicyListResponse)
def list_insurance_policies(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InsurancePolicyListResponse:
    return insurance_service.list_my_policies(db, current_user.user_id)


@router.get("/farmers/me/insurance-policies/{policy_id}", response_model=InsurancePolicyResponse)
def get_insurance_policy(
    policy_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> InsurancePolicyResponse:
    return insurance_service.get_my_policy(db, current_user.user_id, policy_id)


@router.delete("/farmers/me/insurance-policies/{policy_id}", status_code=204)
def delete_insurance_policy(
    policy_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    insurance_service.delete_policy(db, current_user.user_id, policy_id)
