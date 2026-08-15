"""
Task endpoints. Farmer-created tasks only (see app/models/task.py) -
never an auto-generated agronomic recommendation.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import get_db
from app.schemas.task import TaskCreateRequest, TaskListResponse, TaskResponse
from app.services import task_service
from app.services.weather.weather_provider import WeatherProvider

router = APIRouter(tags=["tasks"])


@router.post("/crop-cycles/{crop_cycle_id}/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    crop_cycle_id: uuid.UUID,
    payload: TaskCreateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> TaskResponse:
    return task_service.create_task(db, current_user.user_id, crop_cycle_id, payload)


@router.get("/crop-cycles/{crop_cycle_id}/tasks", response_model=TaskListResponse)
def list_tasks(
    crop_cycle_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
    weather_provider: WeatherProvider = Depends(get_weather_provider),
    settings: Settings = Depends(get_settings),
) -> TaskListResponse:
    return task_service.list_tasks_for_crop_cycle(db, current_user.user_id, crop_cycle_id, weather_provider, settings)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> TaskResponse:
    return task_service.get_task(db, current_user.user_id, task_id)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> TaskResponse:
    return task_service.complete_task(db, current_user.user_id, task_id)


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(
    task_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> TaskResponse:
    return task_service.cancel_task(db, current_user.user_id, task_id)
