"""D74-02 (docs/audit/FINAL_CANONICAL_group_D.md)."""
import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_damage_record import CropDamageRecord


def create(db: Session, record: CropDamageRecord) -> CropDamageRecord:
    db.add(record)
    return record


def get_owned(db: Session, record_id: uuid.UUID, farmer_id: uuid.UUID) -> CropDamageRecord | None:
    return db.execute(select(CropDamageRecord).where(CropDamageRecord.id == record_id, CropDamageRecord.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[CropDamageRecord]:
    return list(
        db.execute(
            select(CropDamageRecord)
            .where(CropDamageRecord.crop_cycle_id == crop_cycle_id, CropDamageRecord.farmer_id == farmer_id)
            .order_by(CropDamageRecord.occurred_on.desc())
        )
        .scalars()
        .all()
    )


def delete(db: Session, record: CropDamageRecord) -> None:
    db.execute(sa_delete(CropDamageRecord).where(CropDamageRecord.id == record.id))
