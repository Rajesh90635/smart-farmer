"""
D52-02/D51-03 (docs/audit/FINAL_CANONICAL_group_C.md): formal per-crop
grading, replacing unconstrained free text on HarvestListing.quality_grade
once an admin has actually configured real grade options for that crop.
See app/models/crop_grade_option.py's own docstring for why this is
admin-authored and empty by default rather than a fabricated dataset.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.crop_grade_option import CropGradeOption
from app.repositories import crop_grade_option_repository, crop_master_repository
from app.schemas.crop_grade_option import CropGradeOptionCreateRequest, CropGradeOptionResponse


def add_grade_option(db: Session, crop_id: uuid.UUID, payload: CropGradeOptionCreateRequest) -> CropGradeOptionResponse:
    crop = crop_master_repository.get_active(db, crop_id)
    if crop is None:
        raise AppError(error_codes.NOT_FOUND, "Crop not found.", 404)

    if crop_grade_option_repository.get_by_crop_and_code(db, crop_id, payload.grade_code) is not None:
        raise AppError(error_codes.VALIDATION_ERROR, "This grade code is already configured for this crop.", 409)

    option = CropGradeOption(
        crop_id=crop_id, grade_code=payload.grade_code, display_name=payload.display_name, sort_order=payload.sort_order,
    )
    crop_grade_option_repository.create(db, option)
    db.commit()
    db.refresh(option)
    return CropGradeOptionResponse.model_validate(option)


def list_grade_options(db: Session, crop_id: uuid.UUID) -> list[CropGradeOptionResponse]:
    return [CropGradeOptionResponse.model_validate(o) for o in crop_grade_option_repository.list_for_crop(db, crop_id)]


def validate_quality_grade(db: Session, crop_id: uuid.UUID, quality_grade: str | None) -> None:
    """Called wherever a farmer sets a HarvestListing's quality_grade
    (D52-02). Deliberately permissive when no grade options are configured
    for this crop yet (free text stays allowed, matching this project's
    "no schema nobody configured blocks a farmer" convention) - only
    enforces once an admin has actually sourced real options."""
    if quality_grade is None:
        return
    options = crop_grade_option_repository.list_for_crop(db, crop_id)
    if not options:
        return
    valid_codes = {o.grade_code for o in options}
    if quality_grade not in valid_codes:
        raise AppError(
            error_codes.VALIDATION_ERROR,
            f"'{quality_grade}' is not a configured grade for this crop. Valid options: {', '.join(sorted(valid_codes))}.",
            422,
        )
