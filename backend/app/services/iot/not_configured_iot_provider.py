"""
NotConfiguredIoTProvider: returned until a real on-farm IoT hardware
integration is configured. Per this project's absolute rule, never
returns a fabricated sensor reading - always available=False.
"""
from app.services.iot.iot_provider import IoTProvider, SensorReadingResult


class NotConfiguredIoTProvider(IoTProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    def get_reading(self, *, sensor_id: str, metric: str) -> SensorReadingResult:
        return SensorReadingResult(
            available=False,
            provider_name="none",
            unavailable_reason="No IoT sensor provider is configured in this environment.",
        )
