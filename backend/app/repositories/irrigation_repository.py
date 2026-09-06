"""Irrigation record repository. Ownership enforced the same way as every
other farmer-scoped entity in this project."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.irrigation_record import IrrigationRecord


def create(db: Session, record: IrrigationRecord) -> IrrigationRecord:
    db.add(record)
    return record


def get_owned(db: Session, record_id: uuid.UUID, farmer_id: uuid.UUID) -> IrrigationRecord | None:
    return db.execute(
        select(IrrigationRecord).where(IrrigationRecord.id == record_id, IrrigationRecord.farmer_id == farmer_id)
    ).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[IrrigationRecord]:
    return list(
        db.execute(
            select(IrrigationRecord)
            .where(IrrigationRecord.crop_cycle_id == crop_cycle_id, IrrigationRecord.farmer_id == farmer_id)
            .order_by(IrrigationRecord.irrigation_date.desc())
        ).scalars().all()
    )
