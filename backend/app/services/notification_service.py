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
from datetime import datetime, time, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.farmer_messages import get_message
from app.models.notification import Notification, NotificationCategory, NotificationPriority
from app.models.notification_preference import NotificationPreference
from app.repositories import notification_repository
from app.services.weather_alert_rules import AlertCandidate

if TYPE_CHECKING:
    from app.services.notifications.delivery_provider import NotificationDeliveryProvider

_CATEGORY_PREFERENCE_MAP = {
    NotificationCategory.WEATHER_ALERT: "weather_alerts_enabled",
    NotificationCategory.RAIN_ALERT: "rain_alerts_enabled",
    NotificationCategory.HEAVY_RAIN_ALERT: "rain_alerts_enabled",
    NotificationCategory.CROP_ALERT: "crop_alerts_enabled",
    NotificationCategory.DISEASE_ALERT: "disease_alerts_enabled",
    NotificationCategory.HARVEST_ALERT: "general_notifications_enabled",
    NotificationCategory.STOCK_ALERT: "general_notifications_enabled",
    NotificationCategory.PAYMENT_ALERT: "general_notifications_enabled",
    NotificationCategory.TASK_ALERT: "general_notifications_enabled",
    NotificationCategory.DISPUTE_ALERT: "general_notifications_enabled",
    NotificationCategory.SEVERE_WEATHER_ALERT: "weather_alerts_enabled",
    NotificationCategory.SOIL_TEST_REMINDER: "general_notifications_enabled",
    NotificationCategory.TREATMENT_FOLLOWUP_REMINDER: "disease_alerts_enabled",
    # SECURITY_ALERT deliberately NOT gated by any preference toggle - a
    # farmer must never be able to silently miss being told their own
    # account's password changed, the same reasoning that already exempts
    # CRITICAL-priority alerts from quiet hours below.
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
    NotificationCategory.TASK_ALERT: "Task Overdue",
    NotificationCategory.DISPUTE_ALERT: "Dispute Update",
    NotificationCategory.SECURITY_ALERT: "Security Alert",
    NotificationCategory.SEVERE_WEATHER_ALERT: "Severe Weather Warning",
    NotificationCategory.SOIL_TEST_REMINDER: "Soil Test Reminder",
    NotificationCategory.TREATMENT_FOLLOWUP_REMINDER: "Treatment Follow-up Reminder",
}

# D88-01 (docs/audit/FINAL_CANONICAL_group_D.md): mirrors the "source"
# strings already used by app/services/assistant/tools.py's tool
# functions (e.g. "Weather service (Prompt 7)") - the subsystem that
# actually produced this category of alert, not a new invented taxonomy.
_SOURCE_BY_CATEGORY = {
    NotificationCategory.WEATHER_ALERT: "Weather service",
    NotificationCategory.RAIN_ALERT: "Weather service",
    NotificationCategory.HEAVY_RAIN_ALERT: "Weather service",
    NotificationCategory.SEVERE_WEATHER_ALERT: "Weather service",
    NotificationCategory.CROP_ALERT: "Weather service",
    NotificationCategory.DISEASE_ALERT: "AI disease detection",
    NotificationCategory.HARVEST_ALERT: "Harvest record",
    NotificationCategory.STOCK_ALERT: "Input inventory",
    NotificationCategory.PAYMENT_ALERT: "Payment records",
    NotificationCategory.TASK_ALERT: "Task records",
    NotificationCategory.DISPUTE_ALERT: "Dispute records",
    NotificationCategory.SECURITY_ALERT: "Account security",
    NotificationCategory.SOIL_TEST_REMINDER: "Soil testing",
    NotificationCategory.TREATMENT_FOLLOWUP_REMINDER: "Treatment records",
}

# D79-04 (docs/audit/FINAL_CANONICAL_group_D.md): a category-specific
# default TTL so notifications don't accumulate forever in the farmer's
# default list. Weather-related alerts are inherently time-sensitive
# (today's rain/heat/wind is stale information within a couple of days);
# everything else gets a longer, generic "don't accumulate forever"
# default. Never applied to SECURITY_ALERT - a farmer must always be able
# to look back at their own account-security history, the same reasoning
# that already exempts it from the preference-toggle map above.
_WEATHER_ALERT_TTL_HOURS = 48
_DEFAULT_TTL_HOURS = 24 * 30


def _default_expires_at(category: NotificationCategory) -> datetime | None:
    if category == NotificationCategory.SECURITY_ALERT:
        return None
    ttl_hours = _WEATHER_ALERT_TTL_HOURS if category in _SOURCE_BY_CATEGORY and _SOURCE_BY_CATEGORY[category] == "Weather service" else _DEFAULT_TTL_HOURS
    return datetime.now(timezone.utc) + timedelta(hours=ttl_hours)


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
    rule_version: str | None = None,
    delivery_provider: "NotificationDeliveryProvider | None" = None,
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
        rule_version=rule_version,
        source_summary=_SOURCE_BY_CATEGORY.get(candidate.category),
        expires_at=_default_expires_at(candidate.category),
    )
    notification_repository.create(db, notification)
    db.commit()
    db.refresh(notification)

    # D90-04 (docs/audit/FINAL_CANONICAL_group_D.md): best-effort push/SMS
    # delivery side channel - the Notification row above is already the
    # complete, working in-app feature; this NEVER blocks on or reverses
    # that write, and swallows any delivery-provider failure rather than
    # letting it surface as a 500 for what is otherwise a successful call.
    if delivery_provider is not None:
        try:
            delivery_provider.send(farmer_id, {"title": notification.title, "body": notification.body})
        except Exception:  # noqa: BLE001 - delivery is best-effort only, never fatal
            pass

    return notification
