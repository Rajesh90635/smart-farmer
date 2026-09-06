"""
D18-06 (docs/audit/FINAL_CANONICAL_group_A.md): irrigation activity
records - mirrors treatment_service.py's CRUD shape for the irrigation
domain, which had no analogous log before this.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.irrigation_record import IrrigationRecord
from app.repositories import crop_cycle_repository, irrigation_repository, task_repository
from app.schemas.irrigation import IrrigationRecordCreateRequest, IrrigationRecordListResponse, IrrigationRecordResponse
from app.services.audit_logger import AuditLogger


def create_irrigation_record(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: IrrigationRecordCreateRequest
) -> IrrigationRecordResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    if payload.task_id is not None:
        task = task_repository.get_owned(db, payload.task_id, farmer_uuid)
        if task is None:
            raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
        if task.crop_cycle_id != crop_cycle_id:
            raise AppError(error_codes.VALIDATION_ERROR, "task_id must belong to the same crop cycle.", 422)

    record = IrrigationRecord(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        task_id=payload.task_id,
        irrigation_date=payload.irrigation_date,
        duration_minutes=payload.duration_minutes,
        volume_liters=payload.volume_liters,
        source=payload.source,
        notes=payload.notes,
        failure_note=payload.failure_note,
    )
    irrigation_repository.create(db, record)

    AuditLogger(db).log("IRRIGATION_RECORD_CREATED", actor_id=farmer_id, actor_role="farmer", entity="irrigation_record", entity_id=str(record.id))
    db.commit()
    db.refresh(record)
    return IrrigationRecordResponse.model_validate(record)


def list_irrigation_records(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> IrrigationRecordListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
    records = irrigation_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return IrrigationRecordListResponse(
        items=[IrrigationRecordResponse.model_validate(r) for r in records], total=len(records)
    )
