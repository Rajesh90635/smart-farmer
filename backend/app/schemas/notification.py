import uuid
from datetime import datetime, time

from pydantic import BaseModel

from app.models.notification import NotificationCategory, NotificationPriority


class NotificationResponse(BaseModel):
    id: uuid.UUID
    category: NotificationCategory
    priority: NotificationPriority
    title: str
    body: str
    language_code: str
    related_entity_type: str | None
    related_entity_id: str | None
    # D89-01/02/07 (docs/FINAL_GAP_REPORT.md): None for non-rule-triggered
    # notifications (payment/harvest/SLA/etc) - only weather-alert-rule
    # output carries a version today.
    rule_version: str | None = None
    # D88-01 (docs/audit/FINAL_CANONICAL_group_D.md): None for a category
    # with no mapped source (see notification_service._SOURCE_BY_CATEGORY)
    # rather than a guessed value.
    source_summary: str | None = None
    read_at: datetime | None
    created_at: datetime
    # D79-04 (docs/audit/FINAL_CANONICAL_group_D.md): None for
    # SECURITY_ALERT (never expires) - a real category-specific default
    # otherwise, set once at creation.
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationPreferenceResponse(BaseModel):
    weather_alerts_enabled: bool
    rain_alerts_enabled: bool
    crop_alerts_enabled: bool
    disease_alerts_enabled: bool
    audio_alerts_enabled: bool
    general_notifications_enabled: bool
    quiet_hours_start: time | None
    quiet_hours_end: time | None

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdateRequest(BaseModel):
    weather_alerts_enabled: bool | None = None
    rain_alerts_enabled: bool | None = None
    crop_alerts_enabled: bool | None = None
    disease_alerts_enabled: bool | None = None
    audio_alerts_enabled: bool | None = None
    general_notifications_enabled: bool | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None
