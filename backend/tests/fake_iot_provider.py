"""
FakeIoTProvider - TEST-ONLY, mirrors the FakeWeatherProvider pattern.
Injected via FastAPI's dependency_overrides only (once a real caller/
dependency-provider exists); the production default remains
NotConfiguredIoTProvider until real hardware is integrated.
"""
from datetime import datetime, timezone

from app.services.iot.iot_provider import IoTProvider, SensorReadingResult


class FakeIoTProvider(IoTProvider):
    def __init__(self, *, available: bool = True, value: float = 42.0, unit: str = "percent"):
        self._available = available
        self._value = value
        self._unit = unit

    @property
    def provider_name(self) -> str:
        return "fake_test_provider"

    def get_reading(self, *, sensor_id: str, metric: str) -> SensorReadingResult:
        if not self._available:
            return SensorReadingResult(available=False, provider_name=self.provider_name, unavailable_reason="fake provider marked unavailable")
        return SensorReadingResult(
            available=True, provider_name=self.provider_name, value=self._value, unit=self._unit, read_at=datetime.now(timezone.utc)
        )
