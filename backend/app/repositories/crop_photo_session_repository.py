import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_photo_session import CropPhotoSession


def create(db: Session, session_obj: CropPhotoSession) -> CropPhotoSession:
    db.add(session_obj)
    return session_obj


def get_owned(db: Session, session_id: uuid.UUID, farmer_id: uuid.UUID) -> CropPhotoSession | None:
    return db.execute(
        select(CropPhotoSession).where(CropPhotoSession.id == session_id, CropPhotoSession.farmer_id == farmer_id)
    ).scalar_one_or_none()
