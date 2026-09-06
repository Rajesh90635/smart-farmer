"""
Task service. Two things worth calling out:

1. compute_display_status is the ONLY place "overdue" is ever decided -
   a pure function of (stored status, due_date, today). It is never
   stored on the row, so it can never go stale.

2. The weather-task connection reuses Step 15's FarmWeatherResponse.crop_action
   DIRECTLY - no new rule, no re-derivation. If the farm's live weather
   already carries an advisory (e.g. avoid spraying - high wind/rain),
   and a PENDING task's type is SPRAYING, that exact same advisory is
   attached to the task in the API response. This is a read-only
   connection - it never changes task status, due date, or completion.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.crop_cycle import CultivationStatus
from app.models.notification import NotificationCategory, NotificationPriority
from app.models.task import Task, TaskStatus, TaskType
from app.repositories import crop_cycle_repository, farm_repository, plot_repository, task_repository, user_repository
from app.schemas.task import (
    TaskActionRequest,
    TaskCalendarGroupResponse,
    TaskCalendarResponse,
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
    WeatherAdvisoryResponse,
)
from app.services import notification_service
from app.services.audit_logger import AuditLogger
from app.services.weather.weather_provider import WeatherProvider
from app.services.weather_alert_rules import AlertCandidate

_TERMINAL_CULTIVATION_STATUSES = (CultivationStatus.HARVESTED, CultivationStatus.CANCELLED)


def compute_display_status(task: Task, today: date) -> str:
    if task.status != TaskStatus.PENDING:
        return task.status.value
    if task.due_date is not None and task.due_date < today:
        return "overdue"
    return task.status.value


def create_task(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, payload: TaskCreateRequest) -> TaskResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    # D97-12 (docs/audit/FINAL_CANONICAL_group_D.md): a HARVESTED/CANCELLED
    # cycle already cancels every pending task via
    # cancel_all_pending_for_crop_cycle - creating a new task on it
    # afterward (farmer double-tap, or an offline-queued create replayed
    # after the cycle closed) would silently reopen work on a cycle
    # that's already done, the same guard complete_task's recurrence
    # branch already applies.
    if crop_cycle.cultivation_status in _TERMINAL_CULTIVATION_STATUSES:
        raise AppError(
            error_codes.VALIDATION_ERROR, "Cannot create a task for a crop cycle that has already ended.", 409
        )

    if payload.depends_on_task_id is not None:
        _validate_dependency(db, farmer_uuid, crop_cycle_id, payload.depends_on_task_id)

    task = Task(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        task_type=payload.task_type,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        depends_on_task_id=payload.depends_on_task_id,
        repeat_interval_days=payload.repeat_interval_days,
        priority=payload.priority,
    )
    task_repository.create(db, task)

    AuditLogger(db).log("TASK_CREATED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def _validate_dependency(db: Session, farmer_uuid: uuid.UUID, crop_cycle_id: uuid.UUID, depends_on_task_id: uuid.UUID) -> Task:
    """D8-07 (docs/FINAL_GAP_REPORT.md): a dependency is only meaningful
    within the same crop cycle it's tracking, and must belong to the same
    farmer (task_repository.get_owned already enforces that). A cycle in
    the dependency graph is impossible at creation time - the new task's
    id doesn't exist yet, so it can only ever depend on something that
    already exists, never on itself or on something that (transitively)
    depends on it."""
    dependency = task_repository.get_owned(db, depends_on_task_id, farmer_uuid)
    if dependency is None:
        raise AppError(error_codes.NOT_FOUND, "Dependency task not found.", 404)
    if dependency.crop_cycle_id != crop_cycle_id:
        raise AppError(error_codes.VALIDATION_ERROR, "A task can only depend on another task in the same crop cycle.", 422)
    return dependency


def get_task(db: Session, farmer_id: str, task_id: uuid.UUID) -> TaskResponse:
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def update_task(db: Session, farmer_id: str, task_id: uuid.UUID, payload: TaskUpdateRequest) -> TaskResponse:
    """D9-05/D9-06 (docs/audit/FINAL_CANONICAL_group_A.md): one shared
    update endpoint serves both snooze (push the due date out) and
    reschedule (pick any new date) - the farmer's UI intent differs, the
    mutation does not."""
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot reschedule a task with status '{task.status.value}'.", 409)

    task.due_date = payload.due_date
    # A due-date change invalidates whatever overdue-alert episode was in
    # progress - if it's still (or newly) overdue after this change, the
    # next sweep tick re-evaluates and re-alerts correctly.
    task.overdue_alerted_at = None

    AuditLogger(db).log("TASK_RESCHEDULED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def list_tasks_for_crop_cycle(
    db: Session, farmer_id: str, crop_cycle_id: uuid.UUID, weather_provider: WeatherProvider | None, settings: Settings | None
) -> TaskListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    crop_cycle = crop_cycle_repository.get_owned(db, crop_cycle_id, farmer_uuid)
    if crop_cycle is None:
        raise AppError(error_codes.NOT_FOUND, "Crop cycle not found.", 404)

    tasks = task_repository.list_for_crop_cycle(db, crop_cycle_id, farmer_uuid)
    today = datetime.now(timezone.utc).date()

    advisory = None
    has_pending_spraying_task = any(t.task_type == TaskType.SPRAYING and t.status == TaskStatus.PENDING for t in tasks)
    if has_pending_spraying_task and weather_provider is not None and settings is not None:
        advisory = _get_current_spray_advisory(db, farmer_id, crop_cycle, weather_provider, settings)

    items = []
    for task in tasks:
        response = _to_response(db, task, today=today)
        if advisory is not None and task.task_type == TaskType.SPRAYING and task.status == TaskStatus.PENDING:
            response.weather_advisory = advisory
        items.append(response)

    return TaskListResponse(items=items, total=len(items))


def get_my_task_calendar(db: Session, farmer_id: str) -> TaskCalendarResponse:
    """D8-01 (docs/audit/FINAL_CANONICAL_group_A.md): a farmer-level,
    date-grouped view across every active crop cycle/farm - a pure read
    aggregation over the same PENDING tasks list_for_crop_cycle's
    per-cycle callers already see, grouped rather than flattened."""
    today = datetime.now(timezone.utc).date()
    tasks = task_repository.list_pending_for_farmer(db, uuid.UUID(farmer_id))

    groups: dict[date | None, list[TaskResponse]] = {}
    for task in tasks:
        groups.setdefault(task.due_date, []).append(_to_response(db, task, today=today))

    ordered_dates = sorted((d for d in groups if d is not None))
    response_groups = [TaskCalendarGroupResponse(due_date=d, tasks=groups[d]) for d in ordered_dates]
    if None in groups:
        response_groups.append(TaskCalendarGroupResponse(due_date=None, tasks=groups[None]))

    return TaskCalendarResponse(groups=response_groups, total=len(tasks))


def _get_current_spray_advisory(
    db: Session, farmer_id: str, crop_cycle, weather_provider: WeatherProvider, settings: Settings
) -> WeatherAdvisoryResponse | None:
    from app.services import weather_service

    farmer_uuid = uuid.UUID(farmer_id)
    plot = plot_repository.get_owned(db, crop_cycle.plot_id, farmer_uuid)
    if plot is None:
        return None
    farm = farm_repository.get_owned(db, plot.farm_id, farmer_uuid)
    if farm is None or farm.latitude is None or farm.longitude is None:
        return None

    try:
        weather = weather_service.get_farm_weather(db, farmer_id, farm.id, weather_provider, settings)
    except AppError:
        return None

    if not weather.available or weather.crop_action is None:
        return None
    return WeatherAdvisoryResponse(
        action=weather.crop_action.action,
        reason_message_key=weather.crop_action.reason_message_key,
        basis=weather.crop_action.basis,
    )


def complete_task(db: Session, farmer_id: str, task_id: uuid.UUID) -> TaskResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    task = task_repository.get_owned(db, task_id, farmer_uuid)
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot complete a task with status '{task.status.value}'.", 409)

    if task.depends_on_task_id is not None:
        dependency = task_repository.get_owned(db, task.depends_on_task_id, farmer_uuid)
        if dependency is None or dependency.status != TaskStatus.COMPLETED:
            raise AppError(
                error_codes.VALIDATION_ERROR, "Cannot complete this task until the task it depends on is completed.", 409
            )

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)

    audit = AuditLogger(db)
    audit.log("TASK_COMPLETED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    _maybe_create_next_recurrence(db, audit, task, farmer_uuid)

    db.commit()
    db.refresh(task)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def _maybe_create_next_recurrence(db: Session, audit: AuditLogger, task: Task, farmer_uuid: uuid.UUID) -> None:
    """D8-08 (docs/FINAL_GAP_REPORT.md): a plain future date offset, never
    a cron/calendar rule. Only creates the next occurrence when the crop
    cycle is still active - a cycle that has already ended (HARVESTED/
    CANCELLED) has nothing left for a recurring task to act on, consistent
    with cancel_all_pending_for_crop_cycle's own reasoning. Shared by
    complete_task and skip_task (D9-09) - both are "this occurrence is
    done, one way or another" outcomes for a recurring task."""
    if task.repeat_interval_days is None:
        return
    crop_cycle = crop_cycle_repository.get_owned(db, task.crop_cycle_id, farmer_uuid)
    if crop_cycle is None or crop_cycle.cultivation_status in _TERMINAL_CULTIVATION_STATUSES:
        return
    base_date = task.due_date if task.due_date is not None else datetime.now(timezone.utc).date()
    next_task = Task(
        farmer_id=farmer_uuid,
        crop_cycle_id=task.crop_cycle_id,
        task_type=task.task_type,
        title=task.title,
        description=task.description,
        due_date=base_date + timedelta(days=task.repeat_interval_days),
        repeat_interval_days=task.repeat_interval_days,
        priority=task.priority,
    )
    task_repository.create(db, next_task)
    db.flush()
    audit.log(
        "TASK_AUTO_CREATED_RECURRENCE", actor_id=None, actor_role="automation_service",
        entity="task", entity_id=str(next_task.id),
    )


def cancel_task(db: Session, farmer_id: str, task_id: uuid.UUID, payload: TaskActionRequest = TaskActionRequest()) -> TaskResponse:
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot cancel a task with status '{task.status.value}'.", 409)

    task.status = TaskStatus.CANCELLED
    task.cancellation_reason = payload.reason
    AuditLogger(db).log("TASK_CANCELLED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def skip_task(db: Session, farmer_id: str, task_id: uuid.UUID, payload: TaskActionRequest = TaskActionRequest()) -> TaskResponse:
    """D9-09 (docs/audit/FINAL_CANONICAL_group_A.md): distinct from cancel
    - skips only this occurrence of a recurring task, while still
    generating the next one per repeat_interval_days. Only meaningful for
    a recurring task; a one-off task has nothing to skip to, so it must
    use cancel instead."""
    farmer_uuid = uuid.UUID(farmer_id)
    task = task_repository.get_owned(db, task_id, farmer_uuid)
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot skip a task with status '{task.status.value}'.", 409)
    if task.repeat_interval_days is None:
        raise AppError(error_codes.VALIDATION_ERROR, "Only a recurring task can be skipped; use cancel instead.", 422)

    task.status = TaskStatus.CANCELLED
    task.cancellation_reason = payload.reason

    audit = AuditLogger(db)
    audit.log("TASK_SKIPPED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    _maybe_create_next_recurrence(db, audit, task, farmer_uuid)

    db.commit()
    db.refresh(task)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def fail_task(db: Session, farmer_id: str, task_id: uuid.UUID, payload: TaskActionRequest = TaskActionRequest()) -> TaskResponse:
    """D9-12 (docs/audit/FINAL_CANONICAL_group_A.md): distinct from
    CANCELLED - the farmer attempted the task but genuinely could not
    (e.g. D18-08's pump failure), a real-world outcome worth reporting
    differently from simply choosing not to do it. Deliberately does NOT
    auto-continue a recurrence (unlike complete/skip) - an unspecified
    equipment/field failure is not the same "this occurrence is done, the
    schedule continues" signal completion or a deliberate skip is."""
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot fail a task with status '{task.status.value}'.", 409)

    task.status = TaskStatus.FAILED
    task.cancellation_reason = payload.reason
    AuditLogger(db).log("TASK_FAILED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(db, task, today=datetime.now(timezone.utc).date())


def cancel_all_pending_for_crop_cycle(db: Session, farmer_id: str, crop_cycle_id: uuid.UUID) -> int:
    """D9-15 (docs/audit/c02_lifecycle_edgecases.md): when a crop cycle
    ends (CANCELLED or HARVESTED), a task still PENDING for it would
    otherwise stay open/overdue forever with no crop cycle left to act
    on - inflating the farmer's overdue-task count and the Crop Risk
    Score's "Operational Task Risk" factor indefinitely. Cancelled, not
    deleted - preserves history. Does NOT commit - the caller
    (crop_cycle_service.py) commits as part of its own status-change
    transaction."""
    tasks = task_repository.list_for_crop_cycle(db, crop_cycle_id, uuid.UUID(farmer_id))
    cancelled = 0
    for task in tasks:
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            AuditLogger(db).log(
                "TASK_AUTO_CANCELLED_CROP_CYCLE_ENDED", actor_id=None, actor_role="automation_service",
                entity="task", entity_id=str(task.id),
            )
            cancelled += 1
    return cancelled


def _to_response(db: Session, task: Task, *, today: date) -> TaskResponse:
    # NOT TaskResponse.model_validate(task) - the ORM object has no
    # display_status attribute at all (it's a Pydantic-only computed
    # field, never a database column), so from_attributes validation
    # fails on a required-but-missing field before there's ever a chance
    # to set it afterward. Constructing directly avoids that.
    dependency_completed = None
    if task.depends_on_task_id is not None:
        dependency = task_repository.get_owned(db, task.depends_on_task_id, task.farmer_id)
        dependency_completed = dependency is not None and dependency.status == TaskStatus.COMPLETED

    return TaskResponse(
        id=task.id,
        crop_cycle_id=task.crop_cycle_id,
        task_type=task.task_type,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        status=task.status,
        display_status=compute_display_status(task, today),
        completed_at=task.completed_at,
        created_at=task.created_at,
        weather_advisory=None,
        depends_on_task_id=task.depends_on_task_id,
        dependency_completed=dependency_completed,
        repeat_interval_days=task.repeat_interval_days,
        priority=task.priority,
        cancellation_reason=task.cancellation_reason,
    )


def run_overdue_task_alert_sweep(db: Session, settings: Settings) -> int:
    """D9-16/D9-03/D78-01/D37-04 (docs/audit/FINAL_CANONICAL_group_A.md):
    one cluster, one sweep - a farmer who never opens the app is otherwise
    never told a task became overdue (compute_display_status only surfaces
    it on read). Mirrors input_inventory_service.run_expiry_check_sweep's
    "fires once per episode" pattern via overdue_alerted_at."""
    today = datetime.now(timezone.utc).date()
    tasks = task_repository.list_overdue_unalerted(db, today=today)

    alerted = 0
    for task in tasks:
        language_code = _language_for(db, str(task.farmer_id))
        candidate = AlertCandidate(
            category=NotificationCategory.TASK_ALERT,
            priority=NotificationPriority.MEDIUM,
            message_key="TASK_OVERDUE",
            message_params={"title": task.title},
            dedup_suffix=f"overdue:{task.id}:{task.due_date.isoformat()}",
        )
        created = notification_service.create_alert_notification(
            db, str(task.farmer_id), candidate, dedup_scope=f"task:{task.id}", language_code=language_code,
            related_entity_type="task", related_entity_id=str(task.id),
        )
        task.overdue_alerted_at = datetime.now(timezone.utc)
        db.commit()
        if created is not None:
            alerted += 1

    return alerted


def _language_for(db: Session, farmer_id: str) -> str:
    user = user_repository.get_by_id(db, uuid.UUID(farmer_id))
    if user and getattr(user, "farmer_profile", None):
        return user.farmer_profile.preferred_language_code
    return "en"
