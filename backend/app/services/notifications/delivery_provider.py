"""
NotificationDeliveryProvider: the abstraction a real push/SMS gateway
would sit behind (D90-04, docs/audit/FINAL_CANONICAL_group_D.md) - mirrors
WeatherProvider/ModelProvider/OCRProvider/AIProvider's exact pattern.

The Notification DB row is the source of truth (the in-app notification
list already works today without this) - delivery is a best-effort side
channel that must NEVER block, duplicate, or replace it. Every
implementation reports delivered=False honestly rather than fabricating
success when no real gateway is configured.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DeliveryResult:
    delivered: bool
    provider_name: str
    unavailable_reason: str | None = None


class NotificationDeliveryProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def send(self, farmer_id: str, payload: dict) -> DeliveryResult:
        """Attempts to push/SMS-deliver an already-created Notification's
        content to the farmer's device - never fabricates delivered=True;
        returns delivered=False with a reason on any failure (no provider
        configured, gateway error, farmer has no registered device)."""
