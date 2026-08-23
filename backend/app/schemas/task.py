import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.task import TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    task_type: TaskType = TaskType.GENERAL
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None


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

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
