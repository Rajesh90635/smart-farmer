"""
Crop damage record endpoints - D74-02 (docs/audit/FINAL_CANONICAL_group_D.md).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.crop_damage import CropDamageRecordCreateRequest, CropDamageRecordListResponse, CropDamageRecordResponse
from app.services import crop_damage_service

router = APIRouter(tags=["crop-damage"])


@router.post("/crop-cycles/{crop_cycle_id}/damage-records", response_model=CropDamageRecordResponse, status_code=201)
def record_damage(
    crop_cycle_id: uuid.UUID,
    payload: CropDamageRecordCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropDamageRecordResponse:
    return crop_damage_service.record_damage(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/damage-records", response_model=CropDamageRecordListResponse)
def list_damage_records(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropDamageRecordListResponse:
    return crop_damage_service.list_for_crop_cycle(db, current_user.user_id, crop_cycle_id)


@router.get("/damage-records/{record_id}", response_model=CropDamageRecordResponse)
def get_damage_record(
    record_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> CropDamageRecordResponse:
    return crop_damage_service.get_my_record(db, current_user.user_id, record_id)


@router.delete("/damage-records/{record_id}", status_code=204)
def delete_damage_record(
    record_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> None:
    crop_damage_service.delete_record(db, current_user.user_id, record_id)
