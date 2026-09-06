"""
SatelliteProvider: D76-06/D90-08 (docs/audit/FINAL_CANONICAL_group_D.md) -
the abstraction a real satellite-imagery API (e.g. Sentinel Hub) would
sit behind, mirroring WeatherProvider/PaymentGatewayProvider/MarketProvider
exactly. No real implementation exists this phase - no satellite-imagery
API account is configured - only the interface plus an honest
NotConfiguredSatelliteProvider stub.

Like WeatherProvider, reports availability explicitly rather than raising
for the expected "not configured" case - never fabricates an NDVI value.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class NdviResult:
    available: bool
    provider_name: str
    ndvi: float | None = None
    observed_date: date | None = None
    unavailable_reason: str | None = None


class SatelliteProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_ndvi(self, *, polygon: list[tuple[float, float]], start_date: date, end_date: date) -> NdviResult:
        """Fetches the most recent NDVI reading for the given polygon within
        the date range - never fabricates a value; returns available=False
        with a reason on any failure (no provider configured, no clear
        imagery in range, network error)."""
