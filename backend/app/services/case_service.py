"""
Case lifecycle orchestration. Every state transition is explicit and
audited (via the existing AuditLogger - no separate CaseAudit table, per
"do not create duplicate tables if equivalent structures exist").

Consent is checked BEFORE a case is created - there is no code path that
creates a case and shares anything without a CaseConsent row existing
first, in the SAME transaction.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.core.roles import Role
from app.models.case_assignment import AssignmentStatus, CaseAssignment
from app.models.case_consent import CaseConsent
from app.models.case_review import EXPERT_OUTCOMES, FIELD_AGENT_OUTCOMES, CaseReview, ReviewerRole
from app.models.crop_health_case import CasePriority, CaseStatus, CropHealthCase
from app.models.photo_access_grant import PhotoAccessGrant
from app.models.professional_feedback import ProfessionalFeedback
from app.repositories import case_repository, crop_cycle_repository, professional_repository
from app.schemas.case import (
    CaseAssignmentResponse,
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseReviewCreateRequest,
    CaseReviewResponse,
    FeedbackCreateRequest,
    SecondOpinionRequest,
)
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.nearby_professional_service import MatchCriteria, find_ranked_candidates

_MAX_SECOND_OPINIONS = 1
_ASSIGNMENT_TIMEOUT_HOURS = 24

_PRIORITY_BY_REASON = {
    "farmer_requested": CasePriority.MEDIUM,
    "ai_low_confidence": CasePriority.MEDIUM,
    "ai_unknown": CasePriority.LOW,
    "farmer_dispute": CasePriority.HIGH,
}


def create_case(db: Session, farmer_id: str, payload: CaseCreateRequest, settings: Settings) -> CaseResponse:
    farmer_uuid = uuid.UUID(farmer_id)

    if payload.requested_professional_role not in (Role.FIELD_AGENT.value, Role.EXPERT.value):
        raise AppError(error_codes.VALIDATION_ERROR, "requested_professional_role must be 'field_agent' or 'expert'.", 422)

    crop_cycle = crop_cycle_repository.get_owned(db, payload.crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    case = CropHealthCase(
        farmer_id=farmer_uuid,
        farm_id=crop_cycle.plot.farm_id,
        plot_id=crop_cycle.plot_id,
        crop_cycle_id=crop_cycle.id,
        crop_photo_id=payload.crop_photo_id,
        ai_analysis_id=payload.ai_analysis_id,
        requested_professional_role=payload.requested_professional_role,
        reason=payload.reason,
        status=CaseStatus.WAITING_FOR_ASSIGNMENT,
        priority=_PRIORITY_BY_REASON.get(payload.reason.value, CasePriority.MEDIUM),
    )
    case_repository.create_case(db, case)
    db.flush()

    consent = CaseConsent(
        case_id=case.id,
        farmer_id=farmer_uuid,
        consent_given=True,
        shared_items=payload.consent_shared_items,
    )
    case_repository.create_consent(db, consent)

    AuditLogger(db).log("CASE_CREATED", actor_id=farmer_id, actor_role="farmer", entity="crop_health_case", entity_id=str(case.id))

    db.commit()
    db.refresh(case)

    _try_auto_assign(db, case, settings)

    db.refresh(case)
    return CaseResponse.model_validate(case)


def _try_auto_assign(db: Session, case: CropHealthCase, settings: Settings) -> None:
    excluded = case_repository.get_excluded_professional_ids(db, case.id)
    criteria = MatchCriteria(role=case.requested_professional_role, exclude_professional_ids=frozenset(excluded))
    ranked = find_ranked_candidates(db, criteria, settings)

    if not ranked:
        case.status = CaseStatus.WAITING_FOR_ASSIGNMENT
        db.commit()
        return

    best = ranked[0].professional
    assignment = CaseAssignment(
        case_id=case.id,
        professional_id=best.id,
        status=AssignmentStatus.PENDING,
        assignment_reason=ranked[0].reason,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=_ASSIGNMENT_TIMEOUT_HOURS),
    )
    case_repository.create_assignment(db, assignment)
    case.status = CaseStatus.ASSIGNED

    AuditLogger(db).log("CASE_ASSIGNED", actor_id=None, actor_role="automation_service", entity="crop_health_case", entity_id=str(case.id))

    if case.crop_photo_id:
        grant = PhotoAccessGrant(
            case_id=case.id,
            crop_photo_id=case.crop_photo_id,
            professional_id=best.id,
            expires_at=assignment.expires_at,
        )
        case_repository.create_photo_grant(db, grant)

    db.commit()

    _notify_case_event(db, case, "CASE_ASSIGNED", professional_user_id=best.user_id)


def get_my_case(db: Session, farmer_id: str, case_id: uuid.UUID) -> CaseResponse:
    case = case_repository.get_case_owned_by_farmer(db, case_id, uuid.UUID(farmer_id))
    if case is None:
        raise AppError(error_codes.NOT_FOUND, "Case not found.", 404)
    return CaseResponse.model_validate(case)


def list_my_cases(db: Session, farmer_id: str, *, limit: int = 50, offset: int = 0) -> CaseListResponse:
    items, total = case_repository.list_cases_for_farmer(db, uuid.UUID(farmer_id), limit=limit, offset=offset)
    return CaseListResponse(items=[CaseResponse.model_validate(c) for c in items], total=total)


def _get_case_for_professional_or_404(db: Session, user_id: str, case_id: uuid.UUID):
    professional = professional_repository.get_by_user_id(db, uuid.UUID(user_id))
    if professional is None:
        raise AppError(error_codes.NOT_FOUND, "No professional profile found for this account.", 404)

    case = case_repository.get_case_by_id(db, case_id)
    if case is None or case_repository.get_assignment_for_professional(db, case_id, professional.id) is None:
        raise AppError(error_codes.NOT_FOUND, "Case not found.", 404)

    return case, professional


def accept_case(db: Session, user_id: str, case_id: uuid.UUID) -> CaseAssignmentResponse:
    case, professional = _get_case_for_professional_or_404(db, user_id, case_id)
    assignment = case_repository.get_assignment_for_professional(db, case_id, professional.id)

    if assignment.status != AssignmentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "This assignment is no longer pending.", 409)

    assignment.status = AssignmentStatus.ACCEPTED
    assignment.accepted_at = datetime.now(timezone.utc)
    case.status = CaseStatus.IN_REVIEW

    AuditLogger(db).log("CASE_ASSIGNMENT_ACCEPTED", actor_id=user_id, actor_role=professional.role, entity="crop_health_case", entity_id=str(case.id))
    db.commit()
    db.refresh(assignment)

    _notify_case_event(db, case, "CASE_ACCEPTED", farmer_id=case.farmer_id)

    return CaseAssignmentResponse.model_validate(assignment)


def decline_case(db: Session, user_id: str, case_id: uuid.UUID, settings: Settings) -> CaseAssignmentResponse:
    case, professional = _get_case_for_professional_or_404(db, user_id, case_id)
    assignment = case_repository.get_assignment_for_professional(db, case_id, professional.id)

    if assignment.status != AssignmentStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, "This assignment is no longer pending.", 409)

    assignment.status = AssignmentStatus.DECLINED
    assignment.declined_at = datetime.now(timezone.utc)

    AuditLogger(db).log("CASE_ASSIGNMENT_DECLINED", actor_id=user_id, actor_role=professional.role, entity="crop_health_case", entity_id=str(case.id))
    db.commit()

    _try_auto_assign(db, case, settings)

    db.refresh(assignment)
    return CaseAssignmentResponse.model_validate(assignment)


def submit_review(db: Session, user_id: str, case_id: uuid.UUID, payload: CaseReviewCreateRequest) -> CaseReviewResponse:
    case, professional = _get_case_for_professional_or_404(db, user_id, case_id)
    assignment = case_repository.get_assignment_for_professional(db, case_id, professional.id)

    if assignment.status != AssignmentStatus.ACCEPTED:
        raise AppError(error_codes.VALIDATION_ERROR, "You must accept this case before submitting a review.", 409)

    reviewer_role = ReviewerRole.EXPERT if professional.role == Role.EXPERT.value else ReviewerRole.FIELD_AGENT
    allowed_outcomes = EXPERT_OUTCOMES if reviewer_role == ReviewerRole.EXPERT else FIELD_AGENT_OUTCOMES
    if payload.outcome not in allowed_outcomes:
        raise AppError(error_codes.VALIDATION_ERROR, f"'{payload.outcome}' is not a valid outcome for role {reviewer_role.value}.", 422)

    review = CaseReview(
        case_id=case.id,
        assignment_id=assignment.id,
        professional_id=professional.id,
        reviewer_role=reviewer_role,
        outcome=payload.outcome,
        alternative_disease_name=payload.alternative_disease_name,
        notes=payload.notes,
    )
    case_repository.create_review(db, review)

    if payload.outcome == "confirmed":
        case.final_verification_source = reviewer_role.value
    elif payload.outcome == "different_diagnosis" and payload.alternative_disease_name:
        case.final_verified_class = payload.alternative_disease_name
        case.final_verification_source = reviewer_role.value

    if payload.outcome in ("needs_more_information", "needs_expert", "needs_better_photo"):
        case.status = CaseStatus.NEEDS_MORE_INFORMATION
    elif payload.outcome in ("confirmed", "different_diagnosis", "no_disease_visible", "healthy_looking", "possible_disease"):
        case.status = CaseStatus.VERIFIED
    elif payload.outcome == "field_visit_required":
        case.status = CaseStatus.ESCALATED

    assignment.status = AssignmentStatus.COMPLETED
    assignment.completed_at = datetime.now(timezone.utc)

    AuditLogger(db).log("CASE_REVIEW_SUBMITTED", actor_id=user_id, actor_role=professional.role, entity="crop_health_case", entity_id=str(case.id))
    db.commit()
    db.refresh(review)

    _notify_case_event(db, case, "CASE_REVIEWED", farmer_id=case.farmer_id)

    return CaseReviewResponse.model_validate(review)


def close_case(db: Session, farmer_id: str, case_id: uuid.UUID) -> CaseResponse:
    case = case_repository.get_case_owned_by_farmer(db, case_id, uuid.UUID(farmer_id))
    if case is None:
        raise AppError(error_codes.NOT_FOUND, "Case not found.", 404)

    case.status = CaseStatus.CLOSED
    case.closed_at = datetime.now(timezone.utc)
    case_repository.revoke_grants_for_case(db, case.id)

    active_assignment = case_repository.get_active_assignment(db, case.id)
    if active_assignment:
        professional = professional_repository.get_by_id(db, active_assignment.professional_id)
        if professional:
            professional.completed_case_count += 1

    AuditLogger(db).log("CASE_CLOSED", actor_id=farmer_id, actor_role="farmer", entity="crop_health_case", entity_id=str(case.id))
    db.commit()
    db.refresh(case)
    return CaseResponse.model_validate(case)


def request_second_opinion(db: Session, farmer_id: str, case_id: uuid.UUID, payload: SecondOpinionRequest, settings: Settings) -> CaseResponse:
    case = case_repository.get_case_owned_by_farmer(db, case_id, uuid.UUID(farmer_id))
    if case is None:
        raise AppError(error_codes.NOT_FOUND, "Case not found.", 404)

    if case.second_opinion_count >= _MAX_SECOND_OPINIONS:
        raise AppError(error_codes.VALIDATION_ERROR, "The maximum number of second opinions has already been reached for this case.", 409)

    case.second_opinion_count += 1
    case.status = CaseStatus.WAITING_FOR_ASSIGNMENT

    AuditLogger(db).log("CASE_SECOND_OPINION_REQUESTED", actor_id=farmer_id, actor_role="farmer", entity="crop_health_case", entity_id=str(case.id))
    db.commit()

    _try_auto_assign(db, case, settings)

    db.refresh(case)
    return CaseResponse.model_validate(case)


def submit_feedback(db: Session, farmer_id: str, case_id: uuid.UUID, payload: FeedbackCreateRequest) -> None:
    case = case_repository.get_case_owned_by_farmer(db, case_id, uuid.UUID(farmer_id))
    if case is None:
        raise AppError(error_codes.NOT_FOUND, "Case not found.", 404)

    if case_repository.get_feedback_for_case(db, case_id) is not None:
        raise AppError(error_codes.VALIDATION_ERROR, "Feedback has already been submitted for this case.", 409)

    active_assignment = case_repository.get_active_assignment(db, case.id)
    if active_assignment is None:
        raise AppError(error_codes.VALIDATION_ERROR, "This case has no completed professional assignment to give feedback on.", 422)

    feedback = ProfessionalFeedback(
        case_id=case.id,
        farmer_id=uuid.UUID(farmer_id),
        professional_id=active_assignment.professional_id,
        helpful=payload.helpful,
        rating=payload.rating,
        feedback_text=payload.feedback_text,
    )
    case_repository.create_feedback(db, feedback)
    db.commit()


def _notify_case_event(db: Session, case: CropHealthCase, message_key: str, *, farmer_id=None, professional_user_id=None) -> None:
    """Reuses Prompt 7's NotificationService entirely - no new
    notification infrastructure."""
    from app.models.notification import NotificationCategory, NotificationPriority
    from app.repositories import user_repository
    from app.services.weather_alert_rules import AlertCandidate

    target_user_id = farmer_id or professional_user_id
    if target_user_id is None:
        return

    user = user_repository.get_by_id(db, target_user_id)
    language_code = "en"
    if user and getattr(user, "farmer_profile", None):
        language_code = user.farmer_profile.preferred_language_code

    candidate = AlertCandidate(
        category=NotificationCategory.CROP_ALERT,
        priority=NotificationPriority.MEDIUM,
        message_key=message_key,
        message_params={},
        dedup_suffix=f"{message_key}:{case.id}",
    )
    notification_service.create_alert_notification(
        db, str(target_user_id), candidate, dedup_scope=f"case:{case.id}", language_code=language_code,
        related_entity_type="crop_health_case", related_entity_id=str(case.id),
    )
