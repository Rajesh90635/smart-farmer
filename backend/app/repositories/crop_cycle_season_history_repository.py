import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_cycle_season_history import CropCycleSeasonHistory


def create(db: Session, entry: CropCycleSeasonHistory) -> CropCycleSeasonHistory:
    db.add(entry)
    return entry


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID) -> list[CropCycleSeasonHistory]:
    return list(
        db.execute(
            select(CropCycleSeasonHistory)
            .where(CropCycleSeasonHistory.crop_cycle_id == crop_cycle_id)
            .order_by(CropCycleSeasonHistory.changed_at.asc())
        ).scalars().all()
    )
