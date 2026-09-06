"""
Task repository. Ownership is enforced the same way as every other
farmer-scoped entity in this project: every read/write is filtered by
Task.farmer_id == farmer_id, resolved from the authenticated session -
never trusted from a client-supplied id.
"""
import uuid
from datetime import date, datetime

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


def list_pending_for_farmer(db: Session, farmer_id: uuid.UUID) -> list[Task]:
    """D8-01 (docs/audit/FINAL_CANONICAL_group_A.md): every PENDING task
    across every one of the farmer's crop cycles/farms, unpaginated - the
    farmer-level calendar aggregation this row asked for, reusing the same
    Task.farmer_id scoping every other farmer-wide task query already
    uses (never a new relationship)."""
    return list(
        db.execute(
            select(Task)
            .where(Task.farmer_id == farmer_id, Task.status == TaskStatus.PENDING)
            .order_by(Task.due_date.asc().nulls_last(), Task.created_at.asc())
        ).scalars().all()
    )


def list_overdue_for_farmer(db: Session, farmer_id: uuid.UUID, *, today: date) -> list[Task]:
    """Reused by the Daily Briefing integration - overdue is computed
    here (pending + due_date in the past), never a stored flag."""
    return list(
        db.execute(
            select(Task).where(Task.farmer_id == farmer_id, Task.status == TaskStatus.PENDING, Task.due_date.is_not(None), Task.due_date < today)
        ).scalars().all()
    )


def count_completed_since(db: Session, farmer_id: uuid.UUID, since: datetime) -> int:
    """D94-04 (docs/audit/FINAL_CANONICAL_group_D.md): real completed-task
    count since a specific point in time, for the daily brief's "what
    changed" task-delta line."""
    return db.execute(
        select(func.count()).select_from(Task).where(Task.farmer_id == farmer_id, Task.completed_at.is_not(None), Task.completed_at > since)
    ).scalar_one()


def count_created_since(db: Session, farmer_id: uuid.UUID, since: datetime) -> int:
    """D94-04: real new-task count since a specific point in time."""
    return db.execute(
        select(func.count()).select_from(Task).where(Task.farmer_id == farmer_id, Task.created_at > since)
    ).scalar_one()


def list_overdue_unalerted(db: Session, *, today: date) -> list[Task]:
    """D9-16/D9-03 (docs/audit/FINAL_CANONICAL_group_A.md): the sweep's own
    query, across every farmer - mirrors input_inventory_repository's
    list_expiring_unalerted "fires once per episode" pattern."""
    return list(
        db.execute(
            select(Task).where(
                Task.status == TaskStatus.PENDING,
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.overdue_alerted_at.is_(None),
            )
        ).scalars().all()
    )
