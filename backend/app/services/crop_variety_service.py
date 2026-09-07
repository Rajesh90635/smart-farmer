import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.crop_variety import CropVariety
from app.repositories import crop_master_repository, crop_variety_repository
from app.schemas.crop_variety import CropVarietyCreateRequest, CropVarietyResponse


def list_varieties_for_crop(db: Session, crop_id: uuid.UUID) -> list[CropVarietyResponse]:
    crop = crop_master_repository.get_active(db, crop_id)
    if crop is None:
        raise AppError(error_codes.NOT_FOUND, "Crop not found.", 404)

    varieties = crop_variety_repository.list_for_crop(db, crop_id)
    return [CropVarietyResponse.model_validate(v) for v in varieties]


def create_variety(db: Session, crop_id: uuid.UUID, payload: CropVarietyCreateRequest) -> CropVarietyResponse:
    """D5-02 (docs/audit/FINAL_CANONICAL_group_A.md): admin-authored,
    mirrors crop_grade_option_service.add_grade_option's own convention -
    no fabricated dataset, only what an admin actually enters."""
    crop = crop_master_repository.get_active(db, crop_id)
    if crop is None:
        raise AppError(error_codes.NOT_FOUND, "Crop not found.", 404)

    if crop_variety_repository.get_by_crop_and_name(db, crop_id, payload.name) is not None:
        raise AppError(error_codes.VALIDATION_ERROR, "This variety name is already configured for this crop.", 409)

    variety = CropVariety(crop_id=crop_id, name=payload.name, typical_duration_days=payload.typical_duration_days)
    crop_variety_repository.create(db, variety)
    db.commit()
    db.refresh(variety)
    return CropVarietyResponse.model_validate(variety)
