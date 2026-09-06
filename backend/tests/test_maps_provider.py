"""D90-03 (docs/audit/FINAL_CANONICAL_group_D.md)."""
from app.services.maps.not_configured_maps_provider import NotConfiguredMapsProvider


def test_not_configured_maps_provider_never_fabricates_a_geocode_result():
    provider = NotConfiguredMapsProvider()
    result = provider.geocode(address="123 Main St")
    assert result.available is False
    assert result.latitude is None
    assert result.unavailable_reason is not None


def test_not_configured_maps_provider_never_fabricates_a_reverse_geocode_result():
    provider = NotConfiguredMapsProvider()
    result = provider.reverse_geocode(latitude=17.0, longitude=78.0)
    assert result.available is False
    assert result.formatted_address is None
    assert result.unavailable_reason is not None
