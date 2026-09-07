import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.case_assignment import AssignmentStatus
from app.models.case_review import ReviewerRole
from app.models.crop_health_case import CasePriority, CaseReason, CaseStatus
from app.models.task import TaskPriority, TaskType


class CaseCreateRequest(BaseModel):
    crop_cycle_id: uuid.UUID
    crop_photo_id: uuid.UUID | None = None
    ai_analysis_id: uuid.UUID | None = None
    requested_professional_role: str
    reason: CaseReason
    consent_shared_items: list[str] = Field(min_length=1)
    # D27-02 (docs/audit/FINAL_CANONICAL_group_B.md): optional, farmer-
    # entered free-text symptom description - never inferred.
    symptom_description: str | None = Field(default=None, max_length=500)


class CaseResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    crop_photo_id: uuid.UUID | None
    ai_analysis_id: uuid.UUID | None
    requested_professional_role: str
    reason: CaseReason
    symptom_description: str | None = None
    status: CaseStatus
    priority: CasePriority
    final_verified_class: str | None
    final_verification_source: str | None
    second_opinion_count: int
    # D36-02 (docs/audit/c06_expert_network.md): the professional's free-text
    # explanation, previously stored (CaseReview.notes) but never surfaced
    # to the farmer's own case-detail view. Only set by get_my_case (the
    # single-case detail endpoint) - list_my_cases/create_case leave it
    # None to avoid an extra query per row in a list.
    latest_review_notes: str | None = None
    # D36-04 (docs/audit/FINAL_CANONICAL_group_B.md): the farmer needs this
    # id to call POST /cases/{id}/reviews/{review_id}/acknowledge - without
    # it that endpoint was unreachable from any farmer-facing read path.
    # Same "only set by get_my_case" scoping as latest_review_notes above.
    latest_review_id: uuid.UUID | None = None
    # D37-01/02/03 (docs/audit/FINAL_CANONICAL_group_B.md): a farmer-
    # confirmed task suggestion derived from the LATEST review's outcome
    # and this case's own real CasePriority - never auto-created, never
    # fabricated (see case_service._build_task_suggestion). All None/False
    # when the latest review doesn't imply a suggested action.
    suggests_task: bool = False
    suggested_task_type: TaskType | None = None
    suggested_due_date: date | None = None
    suggested_priority: TaskPriority | None = None
    created_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int


class CaseReviewCreateRequest(BaseModel):
    outcome: str
    alternative_disease_name: str | None = None
    notes: str | None = Field(default=None, max_length=1000)
    # D36-03 (docs/audit/FINAL_CANONICAL_group_B.md): optional - each id is
    # validated against the professional's own PhotoAccessGrant for this
    # case at submission time (case_service.submit_review), not trusted
    # merely because it parses as a UUID.
    evidence_photo_ids: list[uuid.UUID] = Field(default_factory=list)
    evidence_analysis_ids: list[uuid.UUID] = Field(default_factory=list)
    # D36-07 (docs/audit/FINAL_CANONICAL_group_B.md): optional - only set
    # when this review is explicitly meant to revise a prior one for the
    # SAME case (validated in case_service.submit_review), not simply an
    # additional independent second opinion.
    supersedes_review_id: uuid.UUID | None = None


class CaseReviewResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    reviewer_role: ReviewerRole
    outcome: str
    alternative_disease_name: str | None
    notes: str | None
    evidence_photo_ids: list[uuid.UUID] | None = None
    evidence_analysis_ids: list[uuid.UUID] | None = None
    supersedes_review_id: uuid.UUID | None = None
    # D36-04 (docs/audit/FINAL_CANONICAL_group_B.md): a farmer read-receipt,
    # None until the farmer explicitly acknowledges this review.
    acknowledged_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseAssignmentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    professional_id: uuid.UUID
    status: AssignmentStatus
    assignment_reason: str | None
    assigned_at: datetime

    model_config = {"from_attributes": True}


class SecondOpinionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class FeedbackCreateRequest(BaseModel):
    helpful: bool | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=1000)
