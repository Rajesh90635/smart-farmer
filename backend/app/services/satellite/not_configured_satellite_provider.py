"""
NotConfiguredSatelliteProvider: returned until a real satellite-imagery
provider is configured. Per this project's absolute rule, never returns a
fabricated NDVI value - always available=False.
"""
from datetime import date

from app.services.satellite.satellite_provider import NdviResult, SatelliteProvider


class NotConfiguredSatelliteProvider(SatelliteProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    def get_ndvi(self, *, polygon: list[tuple[float, float]], start_date: date, end_date: date) -> NdviResult:
        return NdviResult(
            available=False,
            provider_name="none",
            unavailable_reason="No satellite-imagery provider is configured in this environment.",
        )
