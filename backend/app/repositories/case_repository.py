import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.case_assignment import AssignmentStatus, CaseAssignment
from app.models.case_consent import CaseConsent
from app.models.case_review import CaseReview
from app.models.crop_health_case import CropHealthCase
from app.models.photo_access_grant import PhotoAccessGrant
from app.models.professional_feedback import ProfessionalFeedback


def create_case(db: Session, case: CropHealthCase) -> CropHealthCase:
    db.add(case)
    return case


def get_case_owned_by_farmer(db: Session, case_id: uuid.UUID, farmer_id: uuid.UUID) -> CropHealthCase | None:
    return db.execute(select(CropHealthCase).where(CropHealthCase.id == case_id, CropHealthCase.farmer_id == farmer_id)).scalar_one_or_none()


def get_case_by_id(db: Session, case_id: uuid.UUID) -> CropHealthCase | None:
    return db.get(CropHealthCase, case_id)


def list_cases_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[CropHealthCase], int]:
    base = select(CropHealthCase).where(CropHealthCase.farmer_id == farmer_id)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = db.execute(base.order_by(CropHealthCase.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def list_cases_assigned_to_professional(db: Session, professional_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[CropHealthCase], int]:
    base = (
        select(CropHealthCase)
        .join(CaseAssignment, CaseAssignment.case_id == CropHealthCase.id)
        .where(CaseAssignment.professional_id == professional_id)
    )
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
    items = db.execute(base.order_by(CropHealthCase.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def create_assignment(db: Session, assignment: CaseAssignment) -> CaseAssignment:
    db.add(assignment)
    return assignment


def get_assignment_for_professional(db: Session, case_id: uuid.UUID, professional_id: uuid.UUID) -> CaseAssignment | None:
    return db.execute(
        select(CaseAssignment).where(CaseAssignment.case_id == case_id, CaseAssignment.professional_id == professional_id)
    ).scalar_one_or_none()


def get_current_pending_assignment(db: Session, case_id: uuid.UUID) -> CaseAssignment | None:
    return db.execute(
        select(CaseAssignment).where(CaseAssignment.case_id == case_id, CaseAssignment.status == AssignmentStatus.PENDING)
    ).scalar_one_or_none()


def get_active_assignment(db: Session, case_id: uuid.UUID) -> CaseAssignment | None:
    """'Active' here means the professional relationship that actually
    did the work - ACCEPTED (in progress) or COMPLETED (review already
    submitted). Originally only matched ACCEPTED, which broke feedback
    submission and the reputation counter in close_case once a review had
    already moved the assignment to COMPLETED - found by a real test
    failure (test_farmer_feedback_after_review), not by inspection."""
    return db.execute(
        select(CaseAssignment).where(CaseAssignment.case_id == case_id, CaseAssignment.status.in_([AssignmentStatus.ACCEPTED, AssignmentStatus.COMPLETED]))
    ).scalar_one_or_none()


def get_excluded_professional_ids(db: Session, case_id: uuid.UUID) -> set:
    rows = db.execute(
        select(CaseAssignment.professional_id).where(
            CaseAssignment.case_id == case_id,
            CaseAssignment.status.in_([AssignmentStatus.DECLINED, AssignmentStatus.PENDING, AssignmentStatus.ACCEPTED, AssignmentStatus.EXPIRED]),
        )
    ).all()
    return {r[0] for r in rows}


def count_active_assignments_for_professional(db: Session, professional_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count()).select_from(CaseAssignment).where(
            CaseAssignment.professional_id == professional_id,
            CaseAssignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.ACCEPTED]),
        )
    ).scalar_one()


def create_review(db: Session, review: CaseReview) -> CaseReview:
    db.add(review)
    return review


def list_reviews_for_case(db: Session, case_id: uuid.UUID) -> list[CaseReview]:
    return list(db.execute(select(CaseReview).where(CaseReview.case_id == case_id).order_by(CaseReview.created_at.asc())).scalars().all())


def create_consent(db: Session, consent: CaseConsent) -> CaseConsent:
    db.add(consent)
    return consent


def get_consent_for_case(db: Session, case_id: uuid.UUID) -> CaseConsent | None:
    return db.execute(select(CaseConsent).where(CaseConsent.case_id == case_id)).scalar_one_or_none()


def create_photo_grant(db: Session, grant: PhotoAccessGrant) -> PhotoAccessGrant:
    db.add(grant)
    return grant


def get_active_grant(db: Session, crop_photo_id: uuid.UUID, professional_id: uuid.UUID) -> PhotoAccessGrant | None:
    now = datetime.now(timezone.utc)
    grants = db.execute(
        select(PhotoAccessGrant).where(PhotoAccessGrant.crop_photo_id == crop_photo_id, PhotoAccessGrant.professional_id == professional_id)
    ).scalars().all()
    for g in grants:
        if g.is_active(now):
            return g
    return None


def revoke_grants_for_case(db: Session, case_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    grants = db.execute(select(PhotoAccessGrant).where(PhotoAccessGrant.case_id == case_id)).scalars().all()
    for g in grants:
        if g.revoked_at is None:
            g.revoked_at = now


def create_feedback(db: Session, feedback: ProfessionalFeedback) -> ProfessionalFeedback:
    db.add(feedback)
    return feedback


def get_feedback_for_case(db: Session, case_id: uuid.UUID) -> ProfessionalFeedback | None:
    return db.execute(select(ProfessionalFeedback).where(ProfessionalFeedback.case_id == case_id)).scalar_one_or_none()
