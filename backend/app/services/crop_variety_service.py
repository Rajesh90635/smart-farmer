import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.repositories import crop_master_repository, crop_variety_repository
from app.schemas.crop_variety import CropVarietyResponse


def list_varieties_for_crop(db: Session, crop_id: uuid.UUID) -> list[CropVarietyResponse]:
    crop = crop_master_repository.get_active(db, crop_id)
    if crop is None:
        raise AppError(error_codes.NOT_FOUND, "Crop not found.", 404)

    varieties = crop_variety_repository.list_for_crop(db, crop_id)
    return [CropVarietyResponse.model_validate(v) for v in varieties]
