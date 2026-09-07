import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    task_type: TaskType = TaskType.GENERAL
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None
    depends_on_task_id: uuid.UUID | None = None
    repeat_interval_days: int | None = Field(default=None, gt=0)
    priority: TaskPriority = TaskPriority.MEDIUM
    # D37-01 (docs/audit/FINAL_CANONICAL_group_B.md): optional - only ever
    # set when the farmer explicitly confirms a review's task suggestion
    # (see CaseResponse.suggests_task), never auto-populated. Validated in
    # task_service.create_task to belong to a review of THIS crop cycle's
    # own case, owned by this farmer.
    source_case_review_id: uuid.UUID | None = None


class TaskUpdateRequest(BaseModel):
    """D9-05/D9-06 (docs/audit/FINAL_CANONICAL_group_A.md): one shared
    endpoint for both snooze (postpone) and reschedule (pick a new date) -
    the underlying mutation is identical, only the farmer's intent differs."""
    due_date: date | None = None


class TaskActionRequest(BaseModel):
    """D9-10: optional farmer-entered reason, shared by cancel/skip/fail."""
    reason: str | None = Field(default=None, max_length=500)


class TaskProgressReportRequest(BaseModel):
    """D9-08 (docs/audit/FINAL_CANONICAL_group_A.md)."""
    completion_percentage: int = Field(ge=0, le=100)


class WeatherAdvisoryResponse(BaseModel):
    action: str
    reason_message_key: str
    basis: str


class TaskResponse(BaseModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    task_type: TaskType
    title: str
    description: str | None
    due_date: date | None
    status: TaskStatus
    display_status: str
    completed_at: datetime | None
    created_at: datetime
    weather_advisory: WeatherAdvisoryResponse | None = None
    depends_on_task_id: uuid.UUID | None = None
    # None when depends_on_task_id is None; otherwise whether that
    # dependency is currently COMPLETED - lets the client show a
    # blocked/waiting state without a second lookup.
    dependency_completed: bool | None = None
    repeat_interval_days: int | None = None
    priority: TaskPriority
    cancellation_reason: str | None = None
    source_case_review_id: uuid.UUID | None = None
    completion_percentage: int | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class TaskCalendarGroupResponse(BaseModel):
    """D8-01 (docs/audit/FINAL_CANONICAL_group_A.md): one day's pending
    tasks, aggregated across every one of the farmer's crop cycles/farms -
    due_date is None only for the genuinely-undated group, never a
    fabricated bucket."""
    due_date: date | None
    tasks: list[TaskResponse]


class TaskCalendarResponse(BaseModel):
    groups: list[TaskCalendarGroupResponse]
    total: int
