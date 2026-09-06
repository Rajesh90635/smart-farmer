"""
NotConfiguredDeliveryProvider: returned when no push/SMS gateway is
configured in this environment (D90-04, same "free-first" posture as
D90-05/06's STT/TTS providers). Never returns fabricated delivered=True.
"""
from app.services.notifications.delivery_provider import DeliveryResult, NotificationDeliveryProvider


class NotConfiguredDeliveryProvider(NotificationDeliveryProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    def send(self, farmer_id: str, payload: dict) -> DeliveryResult:
        return DeliveryResult(
            delivered=False,
            provider_name="none",
            unavailable_reason="No push/SMS delivery provider is configured in this environment.",
        )
