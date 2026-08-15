import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference


def get_by_dedup_key(db: Session, farmer_id: uuid.UUID, dedup_key: str) -> Notification | None:
    return db.execute(
        select(Notification).where(Notification.farmer_id == farmer_id, Notification.dedup_key == dedup_key)
    ).scalar_one_or_none()


def create(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    return notification


def list_for_farmer(db: Session, farmer_id: uuid.UUID, *, unread_only: bool, limit: int, offset: int) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.farmer_id == farmer_id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)).scalars().all()
    return list(items), total


def get_owned(db: Session, notification_id: uuid.UUID, farmer_id: uuid.UUID) -> Notification | None:
    return db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.farmer_id == farmer_id)
    ).scalar_one_or_none()


def mark_all_read(db: Session, farmer_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    result = db.execute(
        select(Notification).where(Notification.farmer_id == farmer_id, Notification.read_at.is_(None))
    ).scalars().all()
    for n in result:
        n.read_at = now
    return len(result)


def get_preferences(db: Session, farmer_id: uuid.UUID) -> NotificationPreference | None:
    return db.execute(select(NotificationPreference).where(NotificationPreference.farmer_id == farmer_id)).scalar_one_or_none()


def create_preferences(db: Session, preferences: NotificationPreference) -> NotificationPreference:
    db.add(preferences)
    return preferences
