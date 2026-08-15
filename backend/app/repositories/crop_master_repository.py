import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_master import CropMaster


def get_active(db: Session, crop_id: uuid.UUID) -> CropMaster | None:
    return db.execute(
        select(CropMaster).where(CropMaster.id == crop_id, CropMaster.is_active.is_(True))
    ).scalar_one_or_none()


def search(db: Session, query: str | None, *, limit: int) -> list[CropMaster]:
    stmt = select(CropMaster).where(CropMaster.is_active.is_(True))
    if query:
        stmt = stmt.where(CropMaster.name.ilike(f"%{query}%"))
    return list(db.execute(stmt.order_by(CropMaster.name).limit(limit)).scalars().all())
