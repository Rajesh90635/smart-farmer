"""
FastAPI dependency providing the configured NotificationDeliveryProvider.
Mirrors weather_provider_dependency.py's exact switch-point pattern - a
Settings flag would decide the real provider once one exists; today it
always returns the honest "not configured" stub, since no real push/SMS
gateway is configured anywhere in this project.
"""
from functools import lru_cache

from app.services.notifications.delivery_provider import NotificationDeliveryProvider
from app.services.notifications.not_configured_delivery_provider import NotConfiguredDeliveryProvider


@lru_cache
def get_notification_delivery_provider() -> NotificationDeliveryProvider:
    return NotConfiguredDeliveryProvider()
