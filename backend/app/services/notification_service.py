"""
NotificationService. Decides: should an alert be created, in which
language, with what priority - and enforces deduplication via the DB
unique constraint (farmer_id, dedup_key), not just an in-memory check
(safe under concurrent requests).

Quiet hours is a pure predicate here (`is_within_quiet_hours`). Honest
limitation: since this phase has no background push scheduler, a
non-critical alert whose creation is suppressed during quiet hours is
simply not created for that check cycle - it is not automatically
deferred and delivered once quiet hours end. True deferred delivery needs
a background worker, out of scope per "do not introduce a complicated
distributed architecture unnecessarily" - see docs/NOTIFICATION_ARCHITECTURE.md.
"""
import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.core.farmer_messages import get_message
from app.models.notification import Notification, NotificationCategory, NotificationPriority
from app.models.notification_preference import NotificationPreference
from app.repositories import notification_repository
from app.services.weather_alert_rules import AlertCandidate

_CATEGORY_PREFERENCE_MAP = {
    NotificationCategory.WEATHER_ALERT: "weather_alerts_enabled",
    NotificationCategory.RAIN_ALERT: "rain_alerts_enabled",
    NotificationCategory.HEAVY_RAIN_ALERT: "rain_alerts_enabled",
    NotificationCategory.CROP_ALERT: "crop_alerts_enabled",
    NotificationCategory.DISEASE_ALERT: "disease_alerts_enabled",
    NotificationCategory.HARVEST_ALERT: "general_notifications_enabled",
    NotificationCategory.STOCK_ALERT: "general_notifications_enabled",
    NotificationCategory.PAYMENT_ALERT: "general_notifications_enabled",
}

_TITLE_BY_CATEGORY = {
    NotificationCategory.WEATHER_ALERT: "Weather Update",
    NotificationCategory.RAIN_ALERT: "Rain Alert",
    NotificationCategory.HEAVY_RAIN_ALERT: "Heavy Rain Warning",
    NotificationCategory.CROP_ALERT: "Crop Alert",
    NotificationCategory.DISEASE_ALERT: "Crop Health Alert",
    NotificationCategory.HARVEST_ALERT: "Harvest Update",
    NotificationCategory.STOCK_ALERT: "Input Stock Alert",
    NotificationCategory.PAYMENT_ALERT: "Payment Update",
}


def get_or_create_preferences(db: Session, farmer_id: str) -> NotificationPreference:
    farmer_uuid = uuid.UUID(farmer_id)
    existing = notification_repository.get_preferences(db, farmer_uuid)
    if existing is not None:
        return existing

    preferences = NotificationPreference(farmer_id=farmer_uuid)
    notification_repository.create_preferences(db, preferences)
    db.commit()
    db.refresh(preferences)
    return preferences


def is_within_quiet_hours(now_local: time, prefs: NotificationPreference) -> bool:
    if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
        return False
    start, end = prefs.quiet_hours_start, prefs.quiet_hours_end
    if start <= end:
        return start <= now_local <= end
    return now_local >= start or now_local <= end


def create_alert_notification(
    db: Session,
    farmer_id: str,
    candidate: AlertCandidate,
    *,
    dedup_scope: str,
    language_code: str,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    now_local_time: time | None = None,
) -> Notification | None:
    """Returns the created Notification, or None if suppressed by
    preference, quiet hours, or an existing duplicate."""
    farmer_uuid = uuid.UUID(farmer_id)
    prefs = get_or_create_preferences(db, farmer_id)

    preference_field = _CATEGORY_PREFERENCE_MAP.get(candidate.category)
    if preference_field and not getattr(prefs, preference_field):
        return None

    if (
        candidate.priority != NotificationPriority.CRITICAL
        and now_local_time is not None
        and is_within_quiet_hours(now_local_time, prefs)
    ):
        return None

    dedup_key = f"{candidate.category.value}:{dedup_scope}:{candidate.dedup_suffix}"
    existing = notification_repository.get_by_dedup_key(db, farmer_uuid, dedup_key)
    if existing is not None:
        return None

    body = get_message(candidate.message_key, language_code, **candidate.message_params)
    notification = Notification(
        farmer_id=farmer_uuid,
        category=candidate.category,
        priority=candidate.priority,
        title=_TITLE_BY_CATEGORY.get(candidate.category, "Update"),
        body=body,
        language_code=language_code,
        dedup_key=dedup_key,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    notification_repository.create(db, notification)
    db.commit()
    db.refresh(notification)
    return notification
