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
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.config import Settings
from app.core.errors import AppError
from app.models.task import Task, TaskStatus, TaskType
from app.repositories import crop_cycle_repository, farm_repository, plot_repository, task_repository
from app.schemas.task import TaskCreateRequest, TaskListResponse, TaskResponse, WeatherAdvisoryResponse
from app.services.audit_logger import AuditLogger
from app.services.weather.weather_provider import WeatherProvider


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

    task = Task(
        farmer_id=farmer_uuid,
        crop_cycle_id=crop_cycle_id,
        task_type=payload.task_type,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )
    task_repository.create(db, task)

    AuditLogger(db).log("TASK_CREATED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(task, today=datetime.now(timezone.utc).date())


def get_task(db: Session, farmer_id: str, task_id: uuid.UUID) -> TaskResponse:
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    return _to_response(task, today=datetime.now(timezone.utc).date())


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
        response = _to_response(task, today=today)
        if advisory is not None and task.task_type == TaskType.SPRAYING and task.status == TaskStatus.PENDING:
            response.weather_advisory = advisory
        items.append(response)

    return TaskListResponse(items=items, total=len(items))


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
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot complete a task with status '{task.status.value}'.", 409)

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)

    AuditLogger(db).log("TASK_COMPLETED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(task, today=datetime.now(timezone.utc).date())


def cancel_task(db: Session, farmer_id: str, task_id: uuid.UUID) -> TaskResponse:
    task = task_repository.get_owned(db, task_id, uuid.UUID(farmer_id))
    if task is None:
        raise AppError(error_codes.NOT_FOUND, "Task not found.", 404)
    if task.status != TaskStatus.PENDING:
        raise AppError(error_codes.VALIDATION_ERROR, f"Cannot cancel a task with status '{task.status.value}'.", 409)

    task.status = TaskStatus.CANCELLED
    AuditLogger(db).log("TASK_CANCELLED", actor_id=farmer_id, actor_role="farmer", entity="task", entity_id=str(task.id))
    db.commit()
    db.refresh(task)
    return _to_response(task, today=datetime.now(timezone.utc).date())


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


def _to_response(task: Task, *, today: date) -> TaskResponse:
    # NOT TaskResponse.model_validate(task) - the ORM object has no
    # display_status attribute at all (it's a Pydantic-only computed
    # field, never a database column), so from_attributes validation
    # fails on a required-but-missing field before there's ever a chance
    # to set it afterward. Constructing directly avoids that.
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
    )
