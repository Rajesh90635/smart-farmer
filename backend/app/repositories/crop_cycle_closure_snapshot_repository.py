import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_cycle_closure_snapshot import CropCycleClosureSnapshot


def create(db: Session, snapshot: CropCycleClosureSnapshot) -> CropCycleClosureSnapshot:
    db.add(snapshot)
    return snapshot


def get_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID) -> CropCycleClosureSnapshot | None:
    return db.execute(
        select(CropCycleClosureSnapshot).where(CropCycleClosureSnapshot.crop_cycle_id == crop_cycle_id)
    ).scalar_one_or_none()
