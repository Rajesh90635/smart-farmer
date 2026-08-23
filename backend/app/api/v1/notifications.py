"""
Notification and notification-preference endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.current_user import CurrentUser, require_role
from app.core.roles import Role
from app.db.session import get_db
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationResponse,
)
from app.services import notification_query_service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    return notification_query_service.list_notifications(db, current_user.user_id, unread_only=unread_only, limit=limit, offset=offset)


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    return notification_query_service.mark_read(db, current_user.user_id, notification_id)


@router.post("/notifications/read-all", status_code=status.HTTP_200_OK)
def mark_all_read(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> dict:
    count = notification_query_service.mark_all_read(db, current_user.user_id)
    return {"marked_read": count}


@router.get("/notification-preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> NotificationPreferenceResponse:
    return notification_query_service.get_preferences(db, current_user.user_id)


@router.put("/notification-preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    payload: NotificationPreferenceUpdateRequest,
    current_user: CurrentUser = Depends(require_role(Role.FARMER.value)),
    db: Session = Depends(get_db),
) -> NotificationPreferenceResponse:
    return notification_query_service.update_preferences(db, current_user.user_id, payload)
