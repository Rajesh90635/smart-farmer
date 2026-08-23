"""
Phase 39: farmer feedback on any Phase 33/36/37/38 advisory.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.advisory_feedback import AdvisoryFeedback
from app.repositories import advisory_feedback_repository, crop_cycle_repository
from app.schemas.personalization import AdvisoryFeedbackCreateRequest, AdvisoryFeedbackResponse


def submit_feedback(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: AdvisoryFeedbackCreateRequest) -> AdvisoryFeedbackResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    feedback = AdvisoryFeedback(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        source_type=payload.source_type,
        source_reference=payload.source_reference,
        feedback_type=payload.feedback_type,
        note=payload.note,
    )
    advisory_feedback_repository.create(db, feedback)
    db.commit()
    db.refresh(feedback)
    return AdvisoryFeedbackResponse.model_validate(feedback, from_attributes=True)


def list_feedback_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> list[AdvisoryFeedbackResponse]:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
    feedback = advisory_feedback_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return [AdvisoryFeedbackResponse.model_validate(f, from_attributes=True) for f in feedback]
