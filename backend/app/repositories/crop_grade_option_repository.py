import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crop_grade_option import CropGradeOption


def create(db: Session, option: CropGradeOption) -> CropGradeOption:
    db.add(option)
    return option


def list_for_crop(db: Session, crop_id: uuid.UUID) -> list[CropGradeOption]:
    return list(
        db.execute(
            select(CropGradeOption).where(CropGradeOption.crop_id == crop_id).order_by(CropGradeOption.sort_order, CropGradeOption.grade_code)
        ).scalars().all()
    )


def get_by_crop_and_code(db: Session, crop_id: uuid.UUID, grade_code: str) -> CropGradeOption | None:
    return db.execute(
        select(CropGradeOption).where(CropGradeOption.crop_id == crop_id, CropGradeOption.grade_code == grade_code)
    ).scalar_one_or_none()
