"""
Phase 34: Treatment Effectiveness Tracking.

THE ABSOLUTE RULE: effectiveness is computed by comparing two REAL
AIAnalysis.result_status values (before -> after) - never from farmer
notes, never from AI-generated "improvement" text, never fabricated.
If either side of the comparison is missing or inconclusive, the result
is explicitly "insufficient_evidence" - never guessed.

A genuine, disclosed limitation: AIAnalysis has no severity score, only
a coarse healthy/disease_detected classification. This means
"no_significant_change" honestly means "same category before and
after" - it does NOT mean "we measured no change in severity within
that category," since no such measurement exists anywhere in this
project. Confidence scores are NEVER used as a severity proxy - that
would be fabricated precision.
"""
import uuid

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.models.ai_analysis import ResultStatus
from app.models.treatment_follow_up import TreatmentFollowUp
from app.models.treatment_record import TreatmentRecord
from app.repositories import ai_analysis_repository, crop_cycle_repository, treatment_repository
from app.schemas.treatment import (
    EffectivenessResponse,
    FollowUpCreateRequest,
    FollowUpListResponse,
    FollowUpResponse,
    TreatmentCreateRequest,
    TreatmentListResponse,
    TreatmentResponse,
)

_COMPARABLE_STATUSES = (ResultStatus.HEALTHY, ResultStatus.DISEASE_DETECTED)


def create_treatment(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: TreatmentCreateRequest) -> TreatmentResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    existing_analyses = ai_analysis_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    before_analysis = max(existing_analyses, key=lambda a: a.created_at) if existing_analyses else None

    treatment = TreatmentRecord(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        case_id=payload.case_id,
        product_id=payload.product_id,
        before_analysis_id=before_analysis.id if before_analysis else None,
        application_date=payload.application_date,
        notes=payload.notes,
    )
    treatment_repository.create_treatment(db, treatment)
    db.commit()
    db.refresh(treatment)
    return _to_treatment_response(treatment, before_analysis)


def list_treatments(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> TreatmentListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)
    treatments = treatment_repository.list_treatments_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    return TreatmentListResponse(items=[_to_treatment_response(t, _get_analysis(db, t.before_analysis_id, farmer_uuid)) for t in treatments])


def create_follow_up(db: Session, farmer_id: str, treatment_id: uuid.UUID, payload: FollowUpCreateRequest) -> FollowUpResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    treatment = treatment_repository.get_treatment_owned(db, treatment_id, farmer_uuid)
    if treatment is None:
        raise AppError(error_codes.NOT_FOUND, "Treatment record not found.", 404)

    after_analysis = None
    if payload.after_analysis_id is not None:
        after_analysis = ai_analysis_repository.get_analysis_owned(db, payload.after_analysis_id, farmer_uuid)
        if after_analysis is None:
            raise AppError(error_codes.NOT_FOUND, "Referenced crop analysis not found.", 404)

    follow_up = TreatmentFollowUp(
        farmer_id=farmer_uuid,
        treatment_id=treatment_id,
        after_analysis_id=payload.after_analysis_id,
        observation_date=payload.observation_date,
        notes=payload.notes,
    )
    treatment_repository.create_follow_up(db, follow_up)
    db.commit()
    db.refresh(follow_up)
    return _to_follow_up_response(follow_up, after_analysis)


def list_follow_ups(db: Session, farmer_id: str, treatment_id: uuid.UUID) -> FollowUpListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    treatment = treatment_repository.get_treatment_owned(db, treatment_id, farmer_uuid)
    if treatment is None:
        raise AppError(error_codes.NOT_FOUND, "Treatment record not found.", 404)
    follow_ups = treatment_repository.list_follow_ups_for_treatment(db, treatment_id, farmer_uuid)
    return FollowUpListResponse(items=[_to_follow_up_response(f, _get_analysis(db, f.after_analysis_id, farmer_uuid)) for f in follow_ups])


def get_effectiveness(db: Session, farmer_id: str, treatment_id: uuid.UUID) -> EffectivenessResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    treatment = treatment_repository.get_treatment_owned(db, treatment_id, farmer_uuid)
    if treatment is None:
        raise AppError(error_codes.NOT_FOUND, "Treatment record not found.", 404)

    before_analysis = _get_analysis(db, treatment.before_analysis_id, farmer_uuid)
    follow_ups = treatment_repository.list_follow_ups_for_treatment(db, treatment_id, farmer_uuid)
    most_recent_follow_up = max(follow_ups, key=lambda f: f.observation_date) if follow_ups else None
    after_analysis = _get_analysis(db, most_recent_follow_up.after_analysis_id, farmer_uuid) if most_recent_follow_up else None

    before_status = before_analysis.result_status if before_analysis else None
    after_status = after_analysis.result_status if after_analysis else None

    if before_analysis is None:
        result, basis = "insufficient_evidence", "No crop analysis existed before this treatment was applied."
    elif before_status not in _COMPARABLE_STATUSES:
        result, basis = "insufficient_evidence", f"The analysis before treatment was inconclusive ({before_status.value}), not a clear healthy/disease result."
    elif most_recent_follow_up is None:
        result, basis = "insufficient_evidence", "No follow-up observation has been recorded yet."
    elif after_analysis is None:
        result, basis = "insufficient_evidence", "The follow-up observation has no linked crop analysis."
    elif after_status not in _COMPARABLE_STATUSES:
        result, basis = "insufficient_evidence", f"The follow-up analysis was inconclusive ({after_status.value}), not a clear healthy/disease result."
    elif before_status == ResultStatus.DISEASE_DETECTED and after_status == ResultStatus.HEALTHY:
        result, basis = "improved", "The crop showed disease before treatment and appears healthy in the follow-up analysis."
    elif before_status == ResultStatus.HEALTHY and after_status == ResultStatus.DISEASE_DETECTED:
        result, basis = "worsened", "The crop appeared healthy before treatment but disease was detected in the follow-up analysis."
    else:
        result, basis = "no_significant_change", "The follow-up analysis shows the same health category as before treatment."

    return EffectivenessResponse(
        treatment_id=treatment_id,
        result=result,
        basis=basis,
        before_result_status=before_status.value if before_status else None,
        after_result_status=after_status.value if after_status else None,
        has_follow_up=most_recent_follow_up is not None,
    )


def _get_analysis(db: Session, analysis_id, farmer_id: uuid.UUID):
    if analysis_id is None:
        return None
    return ai_analysis_repository.get_analysis_owned(db, analysis_id, farmer_id)


def _to_treatment_response(treatment: TreatmentRecord, before_analysis) -> TreatmentResponse:
    return TreatmentResponse(
        id=treatment.id,
        crop_cycle_id=treatment.crop_cycle_id,
        case_id=treatment.case_id,
        product_id=treatment.product_id,
        before_analysis_id=treatment.before_analysis_id,
        before_result_status=before_analysis.result_status.value if before_analysis else None,
        application_date=treatment.application_date,
        notes=treatment.notes,
        created_at=treatment.created_at,
    )


def _to_follow_up_response(follow_up: TreatmentFollowUp, after_analysis) -> FollowUpResponse:
    return FollowUpResponse(
        id=follow_up.id,
        treatment_id=follow_up.treatment_id,
        after_analysis_id=follow_up.after_analysis_id,
        after_result_status=after_analysis.result_status.value if after_analysis else None,
        observation_date=follow_up.observation_date,
        notes=follow_up.notes,
        created_at=follow_up.created_at,
    )
