import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_cycle_stage_history import CropCycleStageHistory


def create(db: Session, entry: CropCycleStageHistory) -> CropCycleStageHistory:
    db.add(entry)
    return entry


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID) -> list[CropCycleStageHistory]:
    return list(
        db.execute(
            select(CropCycleStageHistory)
            .where(CropCycleStageHistory.crop_cycle_id == crop_cycle_id)
            .order_by(CropCycleStageHistory.entered_at.asc())
        ).scalars().all()
    )
