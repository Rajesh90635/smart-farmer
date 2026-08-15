import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_photo import CropPhoto, UploadStatus


def create(db: Session, photo: CropPhoto) -> CropPhoto:
    db.add(photo)
    return photo


def get_owned(db: Session, photo_id: uuid.UUID, farmer_id: uuid.UUID) -> CropPhoto | None:
    """farmer_id is denormalized directly on CropPhoto (see model
    docstring for why), so ownership here is a single-table lookup rather
    than a multi-join - still authoritative, since farmer_id is only ever
    set server-side from a validated chain, never from client input."""
    return db.execute(
        select(CropPhoto).where(
            CropPhoto.id == photo_id, CropPhoto.farmer_id == farmer_id, CropPhoto.upload_status != UploadStatus.DELETED
        )
    ).scalar_one_or_none()


def get_by_client_upload_id(db: Session, session_id: uuid.UUID, client_upload_id: str) -> CropPhoto | None:
    """Idempotency lookup - if a photo with this (session_id,
    client_upload_id) pair already exists, a retried upload returns it
    instead of creating a duplicate."""
    return db.execute(
        select(CropPhoto).where(
            CropPhoto.session_id == session_id, CropPhoto.client_upload_id == client_upload_id
        )
    ).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[CropPhoto]:
    return list(
        db.execute(
            select(CropPhoto)
            .where(
                CropPhoto.crop_cycle_id == crop_cycle_id,
                CropPhoto.farmer_id == farmer_id,
                CropPhoto.upload_status != UploadStatus.DELETED,
            )
            .order_by(CropPhoto.created_at.desc())
        )
        .scalars()
        .all()
    )


def list_for_session(db: Session, session_id: uuid.UUID) -> list[CropPhoto]:
    return list(
        db.execute(
            select(CropPhoto)
            .where(CropPhoto.session_id == session_id, CropPhoto.upload_status != UploadStatus.DELETED)
            .order_by(CropPhoto.created_at.asc())
        )
        .scalars()
        .all()
    )
