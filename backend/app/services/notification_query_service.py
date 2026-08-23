import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import error_codes
from app.core.errors import AppError
from app.repositories import notification_repository
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationResponse,
)
from app.services.notification_service import get_or_create_preferences

_DEFAULT_PAGE_SIZE = 50


def list_notifications(db: Session, farmer_id: str, *, unread_only: bool = False, limit: int = _DEFAULT_PAGE_SIZE, offset: int = 0) -> NotificationListResponse:
    farmer_uuid = uuid.UUID(farmer_id)
    items, total = notification_repository.list_for_farmer(db, farmer_uuid, unread_only=unread_only, limit=limit, offset=offset)
    _, unread_total = notification_repository.list_for_farmer(db, farmer_uuid, unread_only=True, limit=1, offset=0)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items], total=total, unread_count=unread_total
    )


def mark_read(db: Session, farmer_id: str, notification_id: uuid.UUID) -> NotificationResponse:
    notification = notification_repository.get_owned(db, notification_id, uuid.UUID(farmer_id))
    if notification is None:
        raise AppError(error_codes.NOT_FOUND, "Notification not found.", 404)
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return NotificationResponse.model_validate(notification)


def mark_all_read(db: Session, farmer_id: str) -> int:
    count = notification_repository.mark_all_read(db, uuid.UUID(farmer_id))
    db.commit()
    return count


def get_preferences(db: Session, farmer_id: str) -> NotificationPreferenceResponse:
    prefs = get_or_create_preferences(db, farmer_id)
    return NotificationPreferenceResponse.model_validate(prefs)


def update_preferences(db: Session, farmer_id: str, payload: NotificationPreferenceUpdateRequest) -> NotificationPreferenceResponse:
    prefs = get_or_create_preferences(db, farmer_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return NotificationPreferenceResponse.model_validate(prefs)
