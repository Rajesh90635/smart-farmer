import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_variety import CropVariety


def list_for_crop(db: Session, crop_id: uuid.UUID) -> list[CropVariety]:
    return list(
        db.execute(select(CropVariety).where(CropVariety.crop_id == crop_id).order_by(CropVariety.name)).scalars().all()
    )


def get_by_id(db: Session, variety_id: uuid.UUID) -> CropVariety | None:
    return db.get(CropVariety, variety_id)


def get_for_crop(db: Session, variety_id: uuid.UUID, crop_id: uuid.UUID) -> CropVariety | None:
    """Used to validate a selected variety actually belongs to the crop it
    claims to - a variety_id that resolves but belongs to a DIFFERENT crop
    must be rejected, never silently accepted."""
    return db.execute(
        select(CropVariety).where(CropVariety.id == variety_id, CropVariety.crop_id == crop_id)
    ).scalar_one_or_none()
