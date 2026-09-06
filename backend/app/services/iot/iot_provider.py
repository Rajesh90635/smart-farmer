"""
IoTProvider: D77-06 (docs/audit/FINAL_CANONICAL_group_D.md) - the
abstraction a real on-farm IoT sensor (soil moisture, weather station,
etc.) would sit behind, mirroring WeatherProvider/SatelliteProvider
exactly. No real implementation exists this phase - no hardware is
deployed, only the interface plus an honest NotConfiguredIoTProvider stub.
Feeds D77-01/02/03/04 once real hardware/readings exist.

Like WeatherProvider, reports availability explicitly rather than raising
for the expected "no sensor configured" case - never fabricates a reading.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SensorReadingResult:
    available: bool
    provider_name: str
    value: float | None = None
    unit: str | None = None
    read_at: datetime | None = None
    unavailable_reason: str | None = None


class IoTProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_reading(self, *, sensor_id: str, metric: str) -> SensorReadingResult:
        """Fetches the most recent reading for one sensor/metric pair -
        never fabricates a value; returns available=False with a reason
        when no sensor is registered/reachable (no hardware configured,
        sensor offline, network error)."""
