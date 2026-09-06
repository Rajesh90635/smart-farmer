"""
FakeSatelliteProvider - TEST-ONLY, mirrors the FakeWeatherProvider pattern.
Injected via FastAPI's dependency_overrides only (once a real caller/
dependency-provider exists); the production default remains
NotConfiguredSatelliteProvider until a real provider is built.
"""
from datetime import date

from app.services.satellite.satellite_provider import NdviResult, SatelliteProvider


class FakeSatelliteProvider(SatelliteProvider):
    def __init__(self, *, available: bool = True, ndvi: float = 0.65, observed_date: date | None = None):
        self._available = available
        self._ndvi = ndvi
        self._observed_date = observed_date or date.today()

    @property
    def provider_name(self) -> str:
        return "fake_test_provider"

    def get_ndvi(self, *, polygon: list[tuple[float, float]], start_date: date, end_date: date) -> NdviResult:
        if not self._available:
            return NdviResult(available=False, provider_name=self.provider_name, unavailable_reason="fake provider marked unavailable")
        return NdviResult(available=True, provider_name=self.provider_name, ndvi=self._ndvi, observed_date=self._observed_date)
