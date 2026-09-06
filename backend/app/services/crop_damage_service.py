"""
Crop damage record service. D74-02 (docs/audit/FINAL_CANONICAL_group_D.md):
entirely farmer-entered/self-reported, like insurance_service.py - never
verified against a real insurer or disaster-authority assessment.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.crop_damage_record import CropDamageRecord
from app.repositories import crop_cycle_repository, crop_damage_repository, insurance_repository
from app.schemas.crop_damage import CropDamageRecordCreateRequest, CropDamageRecordListResponse, CropDamageRecordResponse
from app.services.audit_logger import AuditLogger


def record_damage(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: CropDamageRecordCreateRequest) -> CropDamageRecordResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    policy = insurance_repository.get_owned(db, payload.policy_id, farmer_uuid)
    if policy is None:
        raise AppError(error_codes.NOT_FOUND, "Insurance policy not found.", 404)

    record = CropDamageRecord(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        policy_id=payload.policy_id,
        loss_type=payload.loss_type,
        extent_percent=payload.extent_percent,
        occurred_on=payload.occurred_on,
        notes=payload.notes,
    )
    crop_damage_repository.create(db, record)
    db.flush()
    AuditLogger(db).log("CROP_DAMAGE_RECORDED", actor_id=farmer_id, actor_role="farmer", entity="crop_damage_record", entity_id=str(record.id))
    db.commit()
    db.refresh(record)
    return CropDamageRecordResponse.model_validate(record)


def list_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> CropDamageRecordListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    records = crop_damage_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return CropDamageRecordListResponse(items=[CropDamageRecordResponse.model_validate(r) for r in records], total=len(records))


def get_my_record(db: Session, farmer_id: str, record_id: uuid.UUID) -> CropDamageRecordResponse:
    record = crop_damage_repository.get_owned(db, record_id, uuid.UUID(farmer_id))
    if record is None:
        raise AppError(error_codes.NOT_FOUND, "Crop damage record not found.", 404)
    return CropDamageRecordResponse.model_validate(record)


def delete_record(db: Session, farmer_id: str, record_id: uuid.UUID) -> None:
    record = crop_damage_repository.get_owned(db, record_id, uuid.UUID(farmer_id))
    if record is None:
        raise AppError(error_codes.NOT_FOUND, "Crop damage record not found.", 404)
    crop_damage_repository.delete(db, record)
    AuditLogger(db).log("CROP_DAMAGE_DELETED", actor_id=farmer_id, actor_role="farmer", entity="crop_damage_record", entity_id=str(record_id))
    db.commit()
