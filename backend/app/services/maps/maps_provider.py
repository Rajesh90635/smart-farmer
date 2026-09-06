"""
MapsProvider: D90-03 (docs/audit/FINAL_CANONICAL_group_D.md) - the
abstraction a real geocoding API (e.g. an OSM-based service, respecting
this project's "free-first" posture on external services) would sit
behind, mirroring WeatherProvider/MarketProvider exactly. No real
implementation exists this phase - no geocoding API account is
configured - only the interface plus an honest NotConfiguredMapsProvider
stub. Location handling today remains the static Mandal/Village master
data, not live geocoding.

Like WeatherProvider, reports availability explicitly rather than raising
for the expected "not configured" case - never fabricates a coordinate or
address.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GeocodeResult:
    available: bool
    provider_name: str
    latitude: float | None = None
    longitude: float | None = None
    formatted_address: str | None = None
    unavailable_reason: str | None = None


class MapsProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def geocode(self, *, address: str) -> GeocodeResult:
        """Address -> coordinates. Never fabricates a location; returns
        available=False with a reason on any failure."""

    @abstractmethod
    def reverse_geocode(self, *, latitude: float, longitude: float) -> GeocodeResult:
        """Coordinates -> a formatted address. Never fabricates a location;
        returns available=False with a reason on any failure."""
