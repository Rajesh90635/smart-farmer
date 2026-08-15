"""
Task repository. Ownership is enforced the same way as every other
farmer-scoped entity in this project: every read/write is filtered by
Task.farmer_id == farmer_id, resolved from the authenticated session -
never trusted from a client-supplied id.
"""
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


def create(db: Session, task: Task) -> Task:
    db.add(task)
    return task


def get_owned(db: Session, task_id: uuid.UUID, farmer_id: uuid.UUID) -> Task | None:
    return db.execute(select(Task).where(Task.id == task_id, Task.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_crop_cycle(db: Session, crop_cycle_id: uuid.UUID, farmer_id: uuid.UUID) -> list[Task]:
    """Farmer ownership is enforced here directly (farmer_id on the task
    row itself) - not solely relying on the caller having already
    checked crop-cycle ownership, so this function is safe even if
    called from a future second call site that forgets that check."""
    return list(
        db.execute(
            select(Task).where(Task.crop_cycle_id == crop_cycle_id, Task.farmer_id == farmer_id).order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc())
        ).scalars().all()
    )


def list_for_farmer(db: Session, farmer_id: uuid.UUID, *, limit: int, offset: int) -> tuple[list[Task], int]:
    stmt = select(Task).where(Task.farmer_id == farmer_id)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = (
        db.execute(stmt.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).limit(limit).offset(offset))
        .scalars().all()
    )
    return list(items), total


def list_overdue_for_farmer(db: Session, farmer_id: uuid.UUID, *, today: date) -> list[Task]:
    """Reused by the Daily Briefing integration - overdue is computed
    here (pending + due_date in the past), never a stored flag."""
    return list(
        db.execute(
            select(Task).where(Task.farmer_id == farmer_id, Task.status == TaskStatus.PENDING, Task.due_date.is_not(None), Task.due_date < today)
        ).scalars().all()
    )
