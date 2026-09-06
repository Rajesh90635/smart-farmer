"""
NotConfiguredMapsProvider: returned until a real geocoding provider is
configured. Per this project's absolute rule, never returns a fabricated
coordinate or address - always available=False.
"""
from app.services.maps.maps_provider import GeocodeResult, MapsProvider


class NotConfiguredMapsProvider(MapsProvider):
    @property
    def provider_name(self) -> str:
        return "none"

    def geocode(self, *, address: str) -> GeocodeResult:
        return GeocodeResult(available=False, provider_name="none", unavailable_reason="No geocoding provider is configured in this environment.")

    def reverse_geocode(self, *, latitude: float, longitude: float) -> GeocodeResult:
        return GeocodeResult(available=False, provider_name="none", unavailable_reason="No geocoding provider is configured in this environment.")
