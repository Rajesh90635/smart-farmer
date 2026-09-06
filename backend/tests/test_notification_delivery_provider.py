"""D90-04 (docs/audit/FINAL_CANONICAL_group_D.md)."""
import uuid

from app.core.jwt import decode_access_token
from app.models.notification import NotificationCategory, NotificationPriority
from app.services import notification_service
from app.services.notifications.delivery_provider import DeliveryResult
from app.services.notifications.not_configured_delivery_provider import NotConfiguredDeliveryProvider
from app.services.weather_alert_rules import AlertCandidate
from tests.conftest import auth_headers


def test_not_configured_delivery_provider_reports_delivered_false_honestly():
    provider = NotConfiguredDeliveryProvider()
    result = provider.send("some-farmer-id", {"title": "t", "body": "b"})
    assert result.delivered is False
    assert result.provider_name == "none"
    assert result.unavailable_reason


def test_create_alert_notification_calls_delivery_provider_best_effort_without_blocking_the_write(
    client, registered_farmer, db_session
):
    _, tokens = registered_farmer
    farmer_id = decode_access_token(tokens["access_token"])["sub"]

    calls = []

    class _RecordingProvider(NotConfiguredDeliveryProvider):
        def send(self, farmer_id, payload):
            calls.append((farmer_id, payload))
            return DeliveryResult(delivered=True, provider_name="recording")

    candidate = AlertCandidate(
        category=NotificationCategory.WEATHER_ALERT,
        priority=NotificationPriority.HIGH,
        message_key="high_wind_alert",
        message_params={"wind_speed": 60},
        dedup_suffix="test_delivery",
    )
    notification = notification_service.create_alert_notification(
        db_session, farmer_id, candidate, dedup_scope="test:delivery", language_code="en",
        delivery_provider=_RecordingProvider(),
    )
    assert notification is not None
    assert len(calls) == 1
    assert calls[0][0] == farmer_id


def test_create_alert_notification_still_succeeds_when_delivery_provider_raises(client, registered_farmer, db_session):
    """Delivery is best-effort only - a raising provider must never
    prevent the Notification row from being created."""
    _, tokens = registered_farmer
    farmer_id = decode_access_token(tokens["access_token"])["sub"]

    class _FailingProvider(NotConfiguredDeliveryProvider):
        def send(self, farmer_id, payload):
            raise RuntimeError("gateway unreachable")

    candidate = AlertCandidate(
        category=NotificationCategory.WEATHER_ALERT,
        priority=NotificationPriority.HIGH,
        message_key="high_wind_alert",
        message_params={"wind_speed": 60},
        dedup_suffix="test_delivery_failure",
    )
    notification = notification_service.create_alert_notification(
        db_session, farmer_id, candidate, dedup_scope="test:delivery_failure", language_code="en",
        delivery_provider=_FailingProvider(),
    )
    assert notification is not None
